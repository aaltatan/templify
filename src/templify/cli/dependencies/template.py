"""The template and output options: `--template` and `--output`."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from jinja2 import TemplateError
from typer_di import Depends

from templify.writers import Writer, writers

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


def _check_if_extension_is_supported(file: Path) -> Path:
    extension = file.suffix.lstrip(".")

    if extension not in writers:
        supported = ", ".join(writers.extensions)
        message = f"Template extension '{extension}' is not supported, supported: {supported}"
        raise typer.BadParameter(message)

    return file


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
            callback=_check_if_extension_is_supported,
        ),
    ],
) -> Template:
    try:
        return Template(path=template_path, writer=writers.create(template_path))
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
            help="Path to the output directory",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
) -> Path:
    return output_path


# -----------------------
# DI
# -----------------------

TemplateDI = Annotated[Template, Depends(_get_template)]
"""Injects the `--template` file with the writer matching its extension."""

OutputDirDI = Annotated[Path, Depends(_get_output_dir)]
"""Injects the `--output` directory."""
