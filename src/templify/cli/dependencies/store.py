"""The store options: `-s / --schema` and the store `PATH`."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from zipfile import BadZipFile

import typer
from pyrecords import Data
from schemify import Schema
from schemify.cli.dependencies.schema import load_schema
from typer_di import Depends

from templify.stores import (
    RecordNotFoundError,
    Store,
    StoreError,
    StoreExtensionNotSupportedError,
    columns_from_schema,
    stores,
    table_name,
)


@dataclass(frozen=True)
class SchemaStore:
    """A store and the schema giving its table name and columns."""

    schema: Schema
    store: Store


def open_store(schema: Schema, schema_path: Path, path: Path) -> Store:
    """Build the store at `path` for `schema`, without touching the file.

    Raises:
        typer.BadParameter: The extension is not supported, or the schema can not be stored.

    """
    try:
        return stores.create(path, table_name(schema, schema_path), columns_from_schema(schema))
    except (StoreExtensionNotSupportedError, StoreError) as e:
        raise typer.BadParameter(str(e)) from e


@contextmanager
def store_errors(unsaved: Data | None = None) -> Iterator[None]:
    """Report store failures, with the `unsaved` answers as JSON so they can be recovered.

    Raises:
        typer.BadParameter: No record has the requested id.
        typer.Exit: The store could not be read or written, exit code 1.

    """
    try:
        yield
    except RecordNotFoundError as e:
        raise typer.BadParameter(str(e)) from e
    except (StoreError, sqlite3.Error, OSError, ValueError, BadZipFile) as e:
        message = f"Store Error: {e}"

        if unsaved:
            answers = json.dumps(unsaved, ensure_ascii=False, indent=2, default=str)
            message += f"\nThe answers were not saved:\n{answers}"

        typer.secho(message, fg="red", err=True)

        raise typer.Exit(1) from e


def _get_schema_store(
    schema_path: Annotated[
        Path,
        typer.Option(
            "-s",
            "--schema",
            help="Path to the JSON Schema file, it gives the table name and columns",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    path: Annotated[
        Path,
        typer.Argument(
            metavar="PATH",
            help=f"Path to the store file ({', '.join(stores.extensions)})",
            dir_okay=False,
            resolve_path=True,
            show_default=False,
        ),
    ],
) -> SchemaStore:
    schema = load_schema(schema_path)

    return SchemaStore(schema, open_store(schema, schema_path, path))


SchemaStoreDI = Annotated[SchemaStore, Depends(_get_schema_store)]
"""Injects the store at `PATH` with the `--schema` it was built from."""
