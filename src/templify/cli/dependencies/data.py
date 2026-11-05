"""The data options: the mode, `--data` / `--schema`, `--order`, `--filter` and `--group-by`."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal
from zipfile import BadZipFile

import typer
from pyspecification import (
    ArgumentError,
    ExpressionWrapperDict,
    Predicate,
    PredicateCompiler,
    PredicateDict,
    ProcessArgumentError,
    RuleDoesNotExistError,
    RuleKeyDoesNotExistError,
)
from schemify.fillers import InvalidDataError, ask_data, ask_list
from schemify.models import Schema
from schemify.registry import NotSupportedError
from schemify.validators import check_schema
from typer_di import Depends

from templify.filter_rules import rules
from templify.models import Data, DataItem
from templify.readers import ExtensionNotSupportedError, ReaderRegistry, object_readers, readers
from templify.transformers import OrderByKey, filter_data, group_by_data, order_by_data

type Mode = Literal["single", "each", "object"]
"""How `render` writes: all rows in one file, one file per row, or one object in one file."""

type FilterSchema = ExpressionWrapperDict | PredicateDict

# -----------------------
# mode
# -----------------------


def _get_mode(
    each: Annotated[  # noqa: FBT002 - typer flag
        bool,
        typer.Option(
            "--each",
            help="Render one file per row (or per group)",
            rich_help_panel="Mode",
        ),
    ] = False,
    object_: Annotated[  # noqa: FBT002 - typer flag
        bool,
        typer.Option(
            "--object",
            help="The data is a single object, render it into one file",
            rich_help_panel="Mode",
        ),
    ] = False,
) -> Mode:
    if each and object_:
        msg = "--each and --object can not be used together"
        raise typer.BadParameter(msg)

    if each:
        return "each"

    return "object" if object_ else "single"


# -----------------------
# read data
# -----------------------

DataFileOption = Annotated[
    Path | None,
    typer.Option(
        "-d",
        "--data",
        help="Path to the data file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        rich_help_panel="Data Source (one of)",
    ),
]

SchemaFileOption = Annotated[
    Path | None,
    typer.Option(
        "-s",
        "--schema",
        help="Path to a JSON Schema file, ask for the data matching it",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        rich_help_panel="Data Source (one of)",
    ),
]


def _load_schema(path: Path) -> Schema:
    try:
        schema: Schema = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        msg = f"Could not read schema file '{path.name}': {e}"
        raise typer.BadParameter(msg) from e

    error = check_schema(schema)

    if error is not None:
        msg = f"Invalid schema file '{path.name}': {error}"
        raise typer.BadParameter(msg)

    return schema


def _read_source[T](
    registry: ReaderRegistry[T],
    ask: Callable[[Schema], T],
    file: Path | None,
    schema_path: Path | None,
) -> T:
    """Read `file` with `registry`, or ask for data matching the schema at `schema_path`."""
    if (file is None) == (schema_path is None):
        msg = "Give exactly one data source: -d / --data or -s / --schema"
        raise typer.BadParameter(msg)

    if schema_path is not None:
        schema = _load_schema(schema_path)

        try:
            return ask(schema)
        except (NotSupportedError, InvalidDataError) as e:
            raise typer.BadParameter(str(e)) from e
        except KeyboardInterrupt:
            raise typer.Abort from None

    assert file is not None  # checked above

    try:
        return registry[file.suffix.lstrip(".")](file)
    except ExtensionNotSupportedError as e:
        raise typer.BadParameter(str(e)) from e
    except (ValueError, BadZipFile) as e:
        msg = f"Could not read data file '{file.name}': {e}"
        raise typer.BadParameter(msg) from e


def _read(
    mode: Annotated[Mode, Depends(_get_mode)],
    file: DataFileOption = None,
    schema_path: SchemaFileOption = None,
) -> Data | DataItem:
    if mode == "object":
        return _read_source(object_readers, ask_data, file, schema_path)

    return _read_source(readers, ask_list, file, schema_path)


# -----------------------
# data options
# -----------------------


def _get_order_by_keys(
    order: Annotated[
        list[str],
        typer.Option(
            "--order",
            help="Columns to order by, -column for descending",
            default_factory=list,
            show_default=False,
            rich_help_panel="Data Options",
        ),
    ],
) -> list[OrderByKey]:
    return [OrderByKey(key) for key in order]


def _get_filter_schema(
    json_string: Annotated[
        str | None,
        typer.Option(
            "--filter",
            help="JSON string containing the filter schema",
            rich_help_panel="Data Options",
        ),
    ] = None,
) -> FilterSchema | None:
    if json_string is None:
        return None

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise typer.BadParameter(str(e)) from e


def _get_group_keys(
    group_by: Annotated[
        list[str],
        typer.Option(
            "--group-by",
            help="Columns to group by, each group holds its rows under --items-var",
            default_factory=list,
            show_default=False,
            rich_help_panel="Data Options",
        ),
    ],
) -> list[str]:
    return group_by


def _get_compiler() -> PredicateCompiler:
    return PredicateCompiler(
        rules.rules,
        lambda schema: Predicate(
            lambda _: schema["operator"] == "all",
            operator="logical",
        ),
    )


# -----------------------
# pipeline: order → filter → group
# -----------------------


def _order(
    data: Annotated[Data | DataItem, Depends(_read)],
    order_keys: Annotated[list[OrderByKey], Depends(_get_order_by_keys)],
    filter_schema: Annotated[FilterSchema | None, Depends(_get_filter_schema)],
    group_keys: Annotated[list[str], Depends(_get_group_keys)],
) -> Data | DataItem:
    if isinstance(data, dict):
        if order_keys or filter_schema is not None or group_keys:
            msg = "--order, --filter and --group-by do not work with --object"
            raise typer.BadParameter(msg)

        return data

    try:
        return order_by_data(data, order_keys) if order_keys else data
    except KeyError as e:
        raise typer.BadParameter(str(e)) from e


def _filter(
    data: Annotated[Data | DataItem, Depends(_order)],
    compiler: Annotated[PredicateCompiler, Depends(_get_compiler)],
    schema: Annotated[FilterSchema | None, Depends(_get_filter_schema)],
) -> Data | DataItem:
    if isinstance(data, dict) or schema is None:
        return data

    try:
        return filter_data(data, compiler, schema)
    except (
        RuleKeyDoesNotExistError,
        RuleDoesNotExistError,
        ArgumentError,
        ProcessArgumentError,
    ) as e:
        raise typer.BadParameter(str(e)) from e
    except (TypeError, ValueError, AttributeError) as e:
        msg = f"Filter failed on a data value (empty cell or wrong type?): {e}"
        raise typer.BadParameter(msg) from e


def _group(
    data: Annotated[Data | DataItem, Depends(_filter)],
    group_keys: Annotated[list[str], Depends(_get_group_keys)],
    items_var: Annotated[
        str,
        typer.Option(
            "--items-var",
            help="Name of the variable that holds each group rows",
            rich_help_panel="Data Options",
        ),
    ] = "items",
) -> Data | DataItem:
    if isinstance(data, dict) or not group_keys:
        return data

    try:
        return group_by_data(data, group_keys, items_var)
    except (KeyError, ValueError) as e:
        raise typer.BadParameter(str(e)) from e
    except TypeError as e:
        msg = f"Can not group by unhashable values (like lists or objects): {e}"
        raise typer.BadParameter(msg) from e


# -----------------------
# DI
# -----------------------

ModeDI = Annotated[Mode, Depends(_get_mode)]
"""Injects the `render` mode chosen with `--each` / `--object`."""

DataDI = Annotated[Data | DataItem, Depends(_group)]
"""Injects the data from `--data` or `--schema`: a list ordered, filtered and grouped,
or a single object with `--object`."""
