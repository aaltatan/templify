"""The template and output options: `--template` and `--output`."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from jinja2 import TemplateError
from typer_di import Depends

from templify.writers import TemplateExtensionNotSupportedError, Writer, writers

# -----------------------
# template
# -----------------------


@dataclass(frozen=True)
class Template:
    """A template file and the writer chosen from its extension."""

    path: Path
    writer: Writer

    @property
    def extension(self) -> str:
        """The template extension, lowercase and without the dot: `docx`."""
        return self.path.suffix.lstrip(".").lower()


def _get_template(
    template_path: Annotated[
        Path,
        typer.Option(
            "-t",
            "--template",
            help=f"Path to the template file ({', '.join(writers.extensions)})",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
) -> Template:
    try:
        return Template(path=template_path, writer=writers.create(template_path))
    except TemplateExtensionNotSupportedError as e:
        raise typer.BadParameter(str(e)) from e
    except TemplateError as e:
        msg = f"Template Error: {e}"
        raise typer.BadParameter(msg) from e
    except Exception as e:
        msg = f"Could not load template '{template_path.name}': {e}"
        raise typer.BadParameter(msg) from e


# -----------------------
# output
# -----------------------


def _get_output_dir(
    output_path: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output",
            help=r"Path to the output directory \[default: current directory]",
            show_default=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path(),
) -> Path:
    return output_path


# -----------------------
# DI
# -----------------------

TemplateDI = Annotated[Template, Depends(_get_template)]
"""Injects the `--template` file with the writer matching its extension."""

OutputDirDI = Annotated[Path, Depends(_get_output_dir)]
"""Injects the `--output` directory."""
