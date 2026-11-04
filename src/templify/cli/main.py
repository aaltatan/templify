# ruff: noqa: PLR0913
"""The templify command line application."""

from pathlib import Path
from typing import Annotated, Any

import typer
from jinja2 import TemplateError
from pyspecification import get_expression_json_schema
from rich.markup import escape
from rich.progress import track
from rich.table import Table
from schemify.cli.dependencies.schema import FilledDataOptionDI, FilledListOptionDI
from typer_di import TyperDI
from typer_swissknife import command

from templify.cli.dependencies.console import ConsoleDI
from templify.cli.dependencies.data import DataDI
from templify.cli.dependencies.template import OutputDirDI, Template, TemplateDI
from templify.filter_rules import rules
from templify.writers import InvalidOutputError, write_multiple, write_single

from .help import MULTIPLE_TEMPLATES_HELP_TEXT, SINGLE_TEMPLATE_HELP_TEXT

FilenameOption = Annotated[
    str | None,
    typer.Option(
        "-f",
        "--filename",
        help="Output filename without extension [default: template filename]",
    ),
]

DataVariableOption = Annotated[
    str,
    typer.Option(
        "-v",
        "--data-variable",
        help="Name of the variable that holds the data inside the template",
    ),
]

app = TyperDI(
    name="templify",
    help="A CLI application for templating documents",
    no_args_is_help=True,
)


@command(
    app,
    name="filters-json-schema",
    aliases=("filters-schema", "fjs"),
    help="List the filter rules, their arguments and description",
)
def print_filter_schema(console: ConsoleDI) -> None:
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


def _type_name(schema: dict[str, Any]) -> str:
    """Return a short type name for a json schema: `string`, `date`, `list[string]`, ..."""
    if schema.get("type") == "array":
        return f"list[{_type_name(schema.get('items', {}))}]"

    if "anyOf" in schema:
        return " | ".join(dict.fromkeys(_type_name(option) for option in schema["anyOf"]))

    return schema.get("format") or schema.get("type") or "any"


@command(
    app,
    name="single-template",
    aliases=("single", "s"),
    no_args_is_help=True,
    help=SINGLE_TEMPLATE_HELP_TEXT,
)
def generate_single_file(
    console: ConsoleDI,
    data: DataDI,
    template: TemplateDI,
    output_dir: OutputDirDI,
    filename: FilenameOption = None,
    data_variable: DataVariableOption = "data",
) -> None:
    """Generate a single file from all the records."""
    _write_single_file(console, template, output_dir, data, filename, data_variable)


@command(
    app,
    name="schema-template",
    aliases=("schema", "js"),
    no_args_is_help=True,
    help=(
        "Ask for one object matching a JSON Schema file, then render it into a single file. "
        "The template reads it as `data` (see -v): Hello {{ data.name }}"
    ),
)
def generate_from_schema(
    console: ConsoleDI,
    template: TemplateDI,
    output_dir: OutputDirDI,
    data: FilledDataOptionDI,
    filename: FilenameOption = None,
    data_variable: DataVariableOption = "data",
) -> None:
    """Generate a single file from the data entered for a schema."""
    _write_single_file(console, template, output_dir, data, filename, data_variable)


@command(
    app,
    name="schema-list-template",
    aliases=("schema-list", "jsl"),
    no_args_is_help=True,
    help=(
        "Ask for a list of items matching a JSON Schema file, then render them into a single "
        "file. The template loops over `data` (see -v): {% for p in data %}{{ p.name }}{% endfor %}"
    ),
)
def generate_from_schema_list(
    console: ConsoleDI,
    template: TemplateDI,
    output_dir: OutputDirDI,
    data: FilledListOptionDI,
    filename: FilenameOption = None,
    data_variable: DataVariableOption = "data",
) -> None:
    """Generate a single file from the list of items entered for a schema."""
    _write_single_file(console, template, output_dir, data, filename, data_variable)


def _write_single_file(
    console: ConsoleDI,
    template: Template,
    output_dir: Path,
    data: Any,
    filename: str | None,
    data_variable: str,
) -> None:
    """Render `data` into one file under `data_variable` and report where it was saved."""
    try:
        filepath = write_single(
            template.writer,
            data,
            output_dir=output_dir,
            filename=filename or template.path.stem,
            extension=template.extension,
            data_variable=data_variable,
        )
    except (TemplateError, InvalidOutputError) as e:
        msg = f"Template Error: {e}"
        raise typer.BadParameter(msg) from e
    else:
        console.print(f"[green]File generated successfully:[/] {filepath}")


@command(
    app,
    name="multiple-templates",
    aliases=("multiple", "m"),
    no_args_is_help=True,
    help=MULTIPLE_TEMPLATES_HELP_TEXT,
)
def generate_multiple_files(
    console: ConsoleDI,
    data: DataDI,
    template: TemplateDI,
    output_dir: OutputDirDI,
    filename_key: Annotated[
        str | None,
        typer.Option(
            "-k",
            "--filename-key",
            help="Column used to name each generated file [default: template-<index>]",
        ),
    ] = None,
    include_index: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "-i",
            "--index",
            help="Prefix each filename with its row index",
        ),
    ] = False,
) -> None:
    """Generate one file per record (or per group)."""
    files = write_multiple(
        template.writer,
        data,
        output_dir=output_dir,
        extension=template.extension,
        filename_key=filename_key,
        include_index=include_index,
    )

    try:
        for _ in track(files, description="Generating", total=len(data), console=console):
            pass
    except (TemplateError, InvalidOutputError) as e:
        msg = f"Template Error: {e}"
        raise typer.BadParameter(msg) from e
    else:
        console.print(f"[green]{len(data)} files generated successfully in:[/] {output_dir}")


def main() -> None:
    """Run the templify command line application."""
    app()


if __name__ == "__main__":
    main()
