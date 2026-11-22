"""The templify command line application."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer
from jinja2 import TemplateError
from pyrecords import Data, filter_data, get_compiler, readers, rules
from pyspecification import get_expression_json_schema
from rich.console import Console
from rich.markup import escape
from rich.progress import track
from rich.table import Table
from schemify import ask_data, ask_list, check_value
from schemify.cli.dependencies.schema import ask_or_abort
from typer_di import TyperDI
from typer_swissknife import add_typer, command

from templify.cli.dependencies.console import ConsoleDI
from templify.cli.dependencies.data import (
    DataDI,
    FilterSchemaDI,
    Mode,
    ModeDI,
    filter_errors,
    read_data_file,
)
from templify.cli.dependencies.store import SchemaStoreDI, store_errors
from templify.cli.dependencies.template import OutputDirDI, TemplateDI
from templify.writers import InvalidOutputError, write_multiple, write_single

from .help import RENDER_HELP_TEXT

app = TyperDI(
    name="templify",
    help="Fill Word, text, Markdown, HTML and JSON templates with data",
    no_args_is_help=True,
)

store_app = TyperDI(help="Keep records asked from a schema in a store file", no_args_is_help=True)
add_typer(app, store_app, name="store", aliases=("s",))

IdArgument = Annotated[int, typer.Argument(metavar="ID", help="The record id", show_default=False)]


@command(app, name="render", aliases=("r",), no_args_is_help=True, help=RENDER_HELP_TEXT)
def render(  # noqa: PLR0913, PLR0917
    console: ConsoleDI,
    mode: ModeDI,
    data: DataDI,
    template: TemplateDI,
    output_dir: OutputDirDI,
    filename: Annotated[
        str | None,
        typer.Option(
            "-f",
            "--filename",
            help=r"Output filename without extension \[default: template filename]",
            rich_help_panel="Output (default and --object)",
        ),
    ] = None,
    var: Annotated[
        str | None,
        typer.Option(
            "-v",
            "--var",
            help=r"Template variable holding the data \[default: objects, or object with --object]",
            rich_help_panel="Output (default and --object)",
        ),
    ] = None,
    name_by: Annotated[
        str | None,
        typer.Option(
            "-n",
            "--name-by",
            help=r"Column naming each file \[default: template-<index>]",
            rich_help_panel="Output (--each)",
        ),
    ] = None,
    numbered: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--numbered",
            help="Prefix each filename with its row number: 1 - Rama",
            rich_help_panel="Output (--each)",
        ),
    ] = False,
    **variables: str,
) -> None:
    """Render the template with the data, into one file or one file per row.

    Undeclared options such as `--title "Q3 report"` become template variables.
    """
    _check_mode_options(mode, filename=filename, var=var, name_by=name_by, numbered=numbered)

    try:
        if mode == "each":
            assert isinstance(data, list)  # only --object reads a single object

            files = write_multiple(
                template.writer,
                data,
                output_dir=output_dir,
                extension=template.extension,
                filename_key=name_by,
                include_index=numbered,
                variables=variables,
            )

            for _ in track(files, description="Generating", total=len(data), console=console):
                pass

            console.print(f"[green]{len(data)} files generated successfully in:[/] {output_dir}")

            return

        filepath = write_single(
            template.writer,
            data,
            var_name=var or ("object" if mode == "object" else "objects"),
            output_dir=output_dir,
            filename=filename or template.path.stem,
            extension=template.extension,
            variables=variables,
        )

    except (TemplateError, InvalidOutputError) as e:
        _fail(f"Template Error: {e}")

    console.print(f"[green]File generated successfully:[/] {filepath}")


@command(app, name="filters", aliases=("f",), help="List the filter rules for --filter")
def filters(console: ConsoleDI) -> None:
    """List the filter rules, their arguments and description."""
    table = Table("Rule", "Arguments", "Description", box=None, header_style="bold")
    expressions = get_expression_json_schema(rules.rules)["$defs"]["expression"]["oneOf"]

    for expression in expressions:
        if "name" not in expression.get("properties", {}):
            continue  # the all / any wrapper, not a rule

        properties = expression["properties"]
        arguments = properties["kwargs"]["properties"].items()
        table.add_row(
            properties["name"]["const"],
            escape(", ".join(f"{name}: {_type_name(schema)}" for name, schema in arguments)),
            expression.get("description", ""),
        )

    console.print(table)


# -----------------------
# store
# -----------------------


@command(store_app, name="init", no_args_is_help=True)
def store_init(console: ConsoleDI, target: SchemaStoreDI) -> None:
    """Create the store file and its table or sheet, does nothing if they exist."""
    with store_errors():
        target.store.init()

    console.print("[green]Store ready[/]")


@command(store_app, name="add", no_args_is_help=True)
def store_add(console: ConsoleDI, target: SchemaStoreDI) -> None:
    """Ask for records matching the schema and add them to the store."""
    records = ask_or_abort(target.schema, ask_list)

    with store_errors(records):
        ids = target.store.add(records)

    console.print(f"[green]Added records:[/] {', '.join(map(str, ids))}")


@command(store_app, name="list", aliases=("ls",), no_args_is_help=True)
def store_list(console: ConsoleDI, target: SchemaStoreDI) -> None:
    """List every record in the store."""
    with store_errors():
        records = target.store.all()

    _print_records(console, records)


@command(store_app, name="get", no_args_is_help=True)
def store_get(console: ConsoleDI, target: SchemaStoreDI, id_: IdArgument) -> None:
    """Show one record."""
    with store_errors():
        record = target.store.get(id_)

    _print_records(console, [record])


@command(store_app, name="search", no_args_is_help=True)
def store_search(console: ConsoleDI, target: SchemaStoreDI, filter_schema: FilterSchemaDI) -> None:
    """List the records matching --filter (see `templify filters` for the rules)."""
    if filter_schema is None:
        msg = "--filter is required"
        raise typer.BadParameter(msg)

    with store_errors():
        records = target.store.all()

    with filter_errors():
        records = filter_data(records, get_compiler(), filter_schema)

    _print_records(console, records)


@command(store_app, name="update", no_args_is_help=True)
def store_update(console: ConsoleDI, target: SchemaStoreDI, id_: IdArgument) -> None:
    """Ask for the whole record again and replace it."""
    with store_errors():
        target.store.get(id_)  # fail before asking

    record = ask_or_abort(target.schema, ask_data)

    with store_errors([record]):
        target.store.update(id_, record)

    console.print(f"[green]Updated record:[/] {id_}")


@command(store_app, name="delete", aliases=("rm",), no_args_is_help=True)
def store_delete(
    console: ConsoleDI,
    target: SchemaStoreDI,
    id_: IdArgument,
    yes: Annotated[  # noqa: FBT002 - typer flag
        bool, typer.Option("-y", "--yes", help="Delete without asking")
    ] = False,
) -> None:
    """Delete one record."""
    with store_errors():
        target.store.get(id_)

    if not yes:
        typer.confirm(f"Delete record {id_}?", abort=True)

    with store_errors():
        target.store.delete(id_)

    console.print(f"[green]Deleted record:[/] {id_}")


@command(store_app, name="migrate", no_args_is_help=True)
def store_migrate(console: ConsoleDI, target: SchemaStoreDI) -> None:
    """Add the schema properties the store is missing as new columns, keeping every row."""
    with store_errors():
        added = target.store.migrate()

    if added:
        console.print(f"[green]Added columns:[/] {', '.join(added)}")
    else:
        console.print("[green]Nothing to migrate[/]")


@command(store_app, name="import", no_args_is_help=True)
def store_import(
    console: ConsoleDI,
    target: SchemaStoreDI,
    file: Annotated[
        Path,
        typer.Option(
            "-d",
            "--data",
            help="Data file to import, every row must match the schema",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
) -> None:
    """Add every row of a data file, or none if one row does not match the schema."""
    properties = target.schema.get("properties") or {}
    records = [
        {
            key: _json_value(value, properties[key])
            for key, value in row.items()
            if key in properties and value is not None  # an empty cell is a missing value
        }
        for row in read_data_file(readers, file)
    ]
    errors = [
        f"Row {idx}: {error}"
        for idx, record in enumerate(records, start=1)
        if (error := check_value(target.schema, record)) is not None
    ]

    if errors:
        msg = "Nothing imported, rows not matching the schema:\n" + "\n".join(errors)
        raise typer.BadParameter(msg)

    with store_errors():
        ids = target.store.add(records)

    console.print(f"[green]Imported {len(ids)} records[/]")


@command(store_app, name="export", no_args_is_help=True)
def store_export(
    console: ConsoleDI,
    target: SchemaStoreDI,
    destination: Annotated[
        Path,
        typer.Argument(
            metavar="TARGET",
            help="New store file to copy every record into, ids and timestamps included",
            dir_okay=False,
            resolve_path=True,
            show_default=False,
        ),
    ],
) -> None:
    """Copy every record into a new store, of any supported extension."""
    if destination.exists():
        msg = f"'{destination.name}' already exists, export only creates new stores"
        raise typer.BadParameter(msg)

    copy = target.open(destination)

    with store_errors():
        ids = copy.add(target.store.all(), keep_meta=True)

    console.print(f"[green]Exported {len(ids)} records to:[/] {destination}")


def _json_value(value: Any, schema: dict[str, Any]) -> Any:
    """Turn a date read from Excel into the ISO text the schema validates."""
    if isinstance(value, datetime) and schema.get("format") == "date":
        return value.date().isoformat()

    if isinstance(value, date):  # datetime too
        return value.isoformat()

    return value


def _print_records(console: Console, records: Data) -> None:
    if not records:
        console.print("[yellow]No records[/]")

        return

    table = Table(*map(escape, records[0]), box=None, header_style="bold")

    for record in records:
        table.add_row(*(escape(_cell(value)) for value in record.values()))

    console.print(table)


def _cell(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def _type_name(schema: dict[str, Any]) -> str:
    """Return a short type name for a json schema: `string`, `date`, `list[string]`, ..."""
    if schema.get("type") == "array":
        return f"list[{_type_name(schema.get('items', {}))}]"

    if "anyOf" in schema:
        return " | ".join(dict.fromkeys(_type_name(option) for option in schema["anyOf"]))

    return schema.get("format") or schema.get("type") or "any"


def _check_mode_options(
    mode: Mode,
    *,
    filename: str | None,
    var: str | None,
    name_by: str | None,
    numbered: bool,
) -> None:
    """Reject the options the chosen mode does not use, instead of silently ignoring them."""
    if mode == "each":
        unused = {"--filename": filename is not None, "--var": var is not None}
        reason = "does not work with --each"
    else:
        unused = {"--name-by": name_by is not None, "--numbered": numbered}
        reason = "only works with --each"

    for option, given in unused.items():
        if given:
            msg = f"{option} {reason}"
            raise typer.BadParameter(msg)


def _fail(message: str) -> NoReturn:
    """Report a runtime failure (not a usage error) and exit with code 1."""
    typer.secho(message, fg="red", err=True)
    raise typer.Exit(1)


def main() -> None:
    """Run the templify application."""
    app()
