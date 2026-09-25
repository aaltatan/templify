# ruff: noqa: PLR0913
"""The templify command line application."""

from typing import Annotated, Any

import typer
from jinja2 import TemplateError
from pyspecification import get_expression_json_schema
from rich.markup import escape
from rich.progress import track
from rich.table import Table
from typer_di import TyperDI
from typer_swissknife import command

from templify.cli.dependencies.console import ConsoleDI
from templify.cli.dependencies.data import DataDI
from templify.cli.dependencies.template import OutputDirDI, TemplateDI
from templify.filter_rules import rules
from templify.writers import InvalidOutputError, write_multiple, write_single

from .help import MULTIPLE_TEMPLATES_HELP_TEXT, SINGLE_TEMPLATE_HELP_TEXT

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
    filename: Annotated[
        str | None,
        typer.Option(
            "-f",
            "--filename",
            help="Output filename without extension [default: template filename]",
        ),
    ] = None,
    data_variable: Annotated[
        str,
        typer.Option(
            "-v",
            "--data-variable",
            help="Name of the variable that holds the data inside the template",
        ),
    ] = "data",
) -> None:
    """Generate a single file from all the records."""
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
