"""The templify command line application."""

from typing import Annotated, Any, NoReturn

import typer
from jinja2 import TemplateError
from pyspecification import get_expression_json_schema
from rich.markup import escape
from rich.progress import track
from rich.table import Table
from typer_di import TyperDI
from typer_swissknife import command

from templify.cli.dependencies.console import ConsoleDI
from templify.cli.dependencies.data import DataDI, Mode, ModeDI
from templify.cli.dependencies.template import OutputDirDI, TemplateDI
from templify.filter_rules import rules
from templify.writers import InvalidOutputError, write_multiple, write_single

from .help import RENDER_HELP_TEXT

app = TyperDI(
    name="templify",
    help="Fill Word, text, Markdown, HTML and JSON templates with data",
    no_args_is_help=True,
)


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
) -> None:
    """Render the template with the data, into one file or one file per row."""
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
