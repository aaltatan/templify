"""The data pipeline options: `--data`, `--order`, `--filter` and `--group-by`."""

import json
from pathlib import Path
from typing import Annotated
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
from typer_di import Depends

from templify.filter_rules import rules
from templify.models import Data
from templify.readers import readers
from templify.transformers import OrderByKey, filter_data, group_by_data, order_by_data

# -----------------------
# utils
# -----------------------


def _extract_extension(file: Path) -> str:
    return file.suffix.lstrip(".")


# -----------------------
# read data
# -----------------------


def _check_if_extension_is_supported(file: Path) -> Path:
    extension = _extract_extension(file)

    if extension not in readers:
        message = f"Extension {extension} is not supported"
        raise typer.BadParameter(message)

    return file


def _read(
    file: Annotated[
        Path,
        typer.Option(
            "-d",
            "--data",
            help="Path to the data file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            callback=_check_if_extension_is_supported,
        ),
    ],
) -> Data:
    try:
        return readers[_extract_extension(file)](file)
    except (ValueError, BadZipFile) as e:
        msg = f"Could not read data file '{file.name}': {e}"
        raise typer.BadParameter(msg) from e


# -----------------------
# order data
# -----------------------


def _get_order_by_keys(
    keys: Annotated[
        list[str],
        typer.Option(
            "--order",
            help="Columns to order by",
            default_factory=list,
            rich_help_panel="Data Options",
        ),
    ],
) -> list[OrderByKey]:
    return [OrderByKey(key) for key in keys]


def _order(
    data: Annotated[Data, Depends(_read)],
    keys: Annotated[list[OrderByKey], Depends(_get_order_by_keys)],
) -> Data:
    try:
        return order_by_data(data, keys) if keys else data
    except KeyError as e:
        raise typer.BadParameter(str(e)) from e


# -----------------------
# filter data
# -----------------------


def _get_compiler() -> PredicateCompiler:
    return PredicateCompiler(
        rules.rules,
        lambda schema: Predicate(
            lambda _: schema["operator"] == "all",
            operator="logical",
        ),
    )


def _get_filter_schema_dict(
    json_string: Annotated[
        str | None,
        typer.Option(
            "--filter",
            help="JSON string containing the filter schema",
            rich_help_panel="Data Options",
        ),
    ] = None,
) -> ExpressionWrapperDict | PredicateDict | None:
    if json_string is None:
        return None

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise typer.BadParameter(str(e)) from e


def _filter(
    data: Annotated[Data, Depends(_order)],
    compiler: Annotated[PredicateCompiler, Depends(_get_compiler)],
    schema: Annotated[
        ExpressionWrapperDict | PredicateDict | None, Depends(_get_filter_schema_dict)
    ],
) -> Data:
    if schema is None:
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


# -----------------------
# group data
# -----------------------


def _group(
    data: Annotated[Data, Depends(_filter)],
    group_keys: Annotated[
        list[str],
        typer.Option(
            "--group-by",
            help="Columns to group by, each group holds its rows under --group-items",
            default_factory=list,
            rich_help_panel="Data Options",
        ),
    ],
    group_items_key: Annotated[
        str,
        typer.Option(
            "--group-items",
            help="Name of the variable that holds each group rows",
            rich_help_panel="Data Options",
        ),
    ] = "items",
) -> Data:
    if not group_keys:
        return data

    try:
        return group_by_data(data, group_keys, group_items_key)
    except (KeyError, ValueError) as e:
        raise typer.BadParameter(str(e)) from e
    except TypeError as e:
        msg = f"Can not group by unhashable values (like lists or objects): {e}"
        raise typer.BadParameter(msg) from e


# -----------------------
# DI
# -----------------------


DataDI = Annotated[Data, Depends(_group)]
"""Injects the records read from `--data`, then ordered, filtered and grouped."""
