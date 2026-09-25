"""Template writers: render a template with data and save it, picked by file extension."""

import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from docxtpl import DocxTemplate
from jinja2 import Environment, FileSystemLoader

from .models import Data, DataItem

type Context = dict[str, Any]
"""The variables a template is rendered with."""

ADDITIONAL_CONTEXT = {
    "new_line": "\n",
    "tab": "\t",
    "page_break": "\f",
}
"""Variables available in every template, they win over data columns with the same name."""

# -----------------------
# writer protocol
# -----------------------


class Writer(Protocol):
    """Renders a template with a context and saves the result to a file.

    A writer is built from its template path (see `WriterFactory`),
    so any class with this `write` method and an `__init__(template_path)` is a writer.
    """

    def write(self, context: Context, filepath: Path) -> None:
        """Render the template with `context` and save the result to `filepath`."""
        ...


type WriterFactory = Callable[[Path], Writer]
"""Builds a writer from a template path, usually the writer class itself."""


class InvalidOutputError(Exception):
    """Raised when a rendered template is not valid for its format, like broken JSON."""


# -----------------------
# registry
# -----------------------


class TemplateExtensionNotSupportedError(Exception):
    """Raised when no writer is registered for a template file extension."""

    def __init__(self, extension: str) -> None:
        message = f"Extension '{extension}' is not supported for being a template file"
        super().__init__(message)


class WriterRegistry:
    """Maps template file extensions (case-insensitive, without the dot) to writers.

    Example:
    ```python
    writers = WriterRegistry()


    @writers.writer("txt", "md")
    class TextWriter: ...


    writer = writers.create(Path("letter.md"))  # a TextWriter
    ```

    """

    def __init__(self) -> None:
        self._factories: dict[str, WriterFactory] = {}

    def __contains__(self, extension: str) -> bool:
        """Whether a writer is registered for `extension`."""
        return extension.lower() in self._factories

    def __getitem__(self, extension: str) -> WriterFactory:
        """Return the writer factory registered for `extension`.

        Raises:
            TemplateExtensionNotSupportedError: No writer is registered for `extension`.

        """
        if extension not in self:
            raise TemplateExtensionNotSupportedError(extension)
        return self._factories[extension.lower()]

    @property
    def extensions(self) -> list[str]:
        """The supported extensions, sorted."""
        return sorted(self._factories)

    def writer[T: WriterFactory](self, *extensions: str) -> Callable[[T], T]:
        """Register the decorated class (or factory) as the writer for `extensions`."""

        def decorator(factory: T) -> T:
            for extension in extensions:
                self.add_writer(factory, extension)
            return factory

        return decorator

    def add_writer(self, factory: WriterFactory, extension: str) -> None:
        """Register `factory` as the writer for `extension`, replacing any existing one."""
        self._factories[extension.lower()] = factory

    def create(self, template_path: Path) -> Writer:
        """Build the writer matching the extension of `template_path`.

        Raises:
            TemplateExtensionNotSupportedError: No writer is registered for the extension.

        """
        return self[template_path.suffix.lstrip(".")](template_path)


writers = WriterRegistry()
"""The default registry, used by the CLI `--template` option."""

# -----------------------
# concrete writers
# -----------------------


@writers.writer("docx")
class DocxWriter:
    """Writes Word documents using docxtpl (Jinja2 tags inside a `.docx` file)."""

    def __init__(self, template_path: Path) -> None:
        """Load the template.

        Raises:
            docx.opc.exceptions.PackageNotFoundError: The file is not a valid `.docx`.

        """
        self.template = DocxTemplate(template_path)
        self.template.init_docx()  # fail fast on a corrupted file, docxtpl loads lazily

    def write(self, context: Context, filepath: Path) -> None:
        """Render the template with `context` and save the result to `filepath`.

        Raises:
            jinja2.TemplateError: The template has a syntax error, or failed to render.

        """
        self.template.render(context)
        self.template.save(filepath)


@writers.writer("txt", "md", "html", "htm")
class TextWriter:
    """Writes plain text files using Jinja2, saved as UTF-8.

    Templates can `{% include %}` other files from the template's folder.
    Output is not HTML-escaped.
    """

    def __init__(self, template_path: Path) -> None:
        """Load the template.

        Raises:
            jinja2.TemplateSyntaxError: The template has a syntax error.

        """
        env = Environment(  # noqa: S701 - output is not only html, escaping would corrupt txt/json
            loader=FileSystemLoader(template_path.parent),
            keep_trailing_newline=True,
        )
        self.template = env.get_template(template_path.name)

    def render(self, context: Context) -> str:
        """Render the template with `context` and return the text."""
        return self.template.render(context)

    def write(self, context: Context, filepath: Path) -> None:
        """Render the template with `context` and save the result to `filepath`."""
        filepath.write_text(self.render(context), encoding="utf-8", newline="")


@writers.writer("json")
class JsonWriter(TextWriter):
    """Same as `TextWriter`, but refuses to save output that is not valid JSON."""

    def render(self, context: Context) -> str:
        """Render the template with `context` and return the text.

        Raises:
            InvalidOutputError: The rendered text is not valid JSON.

        """
        content = super().render(context)

        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            message = f"Rendered output is not valid JSON: {e}"
            raise InvalidOutputError(message) from e

        return content


# -----------------------
# write modes
# -----------------------


def write_single(  # noqa: PLR0913
    writer: Writer,
    data: Data,
    *,
    output_dir: Path,
    filename: str,
    extension: str,
    data_variable: str = "data",
) -> Path:
    """Render all the data into one file, the template loops over `data_variable`.

    Args:
        writer: Renders and saves the file.
        data: The records, available in the template as `data_variable`.
        output_dir: Where to save the file, created if missing.
        filename: The file name without extension.
        extension: The file extension, without the dot.
        data_variable: The template variable holding `data`.

    Returns:
        The saved file path. A random suffix is added if the file already exists.

    """
    filepath = _generate_filepath(filename, output_dir, extension)
    writer.write({data_variable: data, **ADDITIONAL_CONTEXT}, filepath)
    return filepath


def write_multiple(  # noqa: PLR0913
    writer: Writer,
    data: Data,
    *,
    output_dir: Path,
    extension: str,
    filename_key: str | None = None,
    include_index: bool = False,
) -> Iterator[Path]:
    """Render one file per record, yielding each saved file path.

    Files are written lazily, one per iteration, so callers can report progress.

    Args:
        writer: Renders and saves each file.
        data: The records, each record's columns are the template variables.
        output_dir: Where to save the files, created if missing.
        extension: The files extension, without the dot.
        filename_key: The column naming each file, `template-<n>` when missing or empty.
        include_index: Prefix each filename with the record number: `1 - Rama`.

    Yields:
        Each saved file path. A random suffix is added if the file already exists.

    """
    for idx, item in enumerate(data, start=1):
        filename = _get_filename(item, idx, filename_key, include_index=include_index)
        filepath = _generate_filepath(filename, output_dir, extension)
        writer.write({**item, **ADDITIONAL_CONTEXT}, filepath)
        yield filepath


# -----------------------
# utils
# -----------------------

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize_filename(filename: str) -> str:
    return _INVALID_FILENAME_CHARS.sub("_", filename).strip(" .")


def _get_filename(
    item: DataItem,
    idx: int,
    filename_key: str | None = None,
    *,
    include_index: bool = False,
) -> str:
    value = item.get(filename_key) if filename_key else None
    filename = _sanitize_filename(str(value)) if value is not None else ""

    if not filename:
        return f"template-{idx}"

    return f"{idx} - {filename}" if include_index else filename


def _generate_filepath(filename: str, output_dir: Path, extension: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{filename}.{extension}"

    while filepath.exists():
        filepath = output_dir / f"{filename}-{uuid4().hex[:8]}.{extension}"

    return filepath
