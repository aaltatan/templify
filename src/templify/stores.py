"""Record stores: keep the records asked from a schema in a file, picked by file extension.

A store is a repository over one table (sqlite), sheet (xlsx) or file (json, jsonl).
Every record gets an `id`, `created_at` and `updated_at`, beside the schema columns.
"""

import contextlib
import json
import sqlite3
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, ClassVar, Protocol

import openpyxl
from pyrecords import Data, DataItem, filter_data, get_compiler
from pyspecification import ExpressionWrapperDict, PredicateDict
from schemify import Schema

META_COLUMNS = ("id", "created_at", "updated_at")
"""The columns every store adds, a schema can not declare them."""

# -----------------------
# errors
# -----------------------


class StoreError(Exception):
    """Raised when a store can not be built, read or written."""


class RecordNotFoundError(StoreError):
    """Raised when no record has the requested id."""

    def __init__(self, id_: int) -> None:
        super().__init__(f"No record with id {id_}")


class StoreExtensionNotSupportedError(Exception):
    """Raised when no store is registered for a file extension."""

    def __init__(self, extension: str, supported: list[str]) -> None:
        message = (
            f"Store extension '{extension}' is not supported, supported: {', '.join(supported)}"
        )
        super().__init__(message)


# -----------------------
# columns
# -----------------------


@dataclass(frozen=True)
class Column:
    """A stored column, from a top-level schema property."""

    name: str
    type: str | None = None
    format: str | None = None


_TIMESTAMP = Column("", "string", "date-time")


def columns_from_schema(schema: Schema) -> list[Column]:
    """Return the schema's top-level properties as columns, in schema order.

    Raises:
        StoreError: The schema has no properties, or declares `id`, `created_at` or `updated_at`.

    """
    properties: dict[str, Any] = schema.get("properties") or {}

    if not properties:
        msg = "The schema has no properties to store"
        raise StoreError(msg)

    reserved = [name for name in META_COLUMNS if name in properties]

    if reserved:
        msg = f"The schema can not declare {', '.join(reserved)}, every store adds them"
        raise StoreError(msg)

    return [Column(name, _type_of(prop), prop.get("format")) for name, prop in properties.items()]


def table_name(schema: Schema, schema_path: Path) -> str:
    """Return the table (or sheet) name: the schema `title`, else the schema file stem."""
    return str(schema.get("title") or schema_path.stem)


def _type_of(prop: dict[str, Any]) -> str | None:
    type_ = prop.get("type")

    if isinstance(type_, list):
        return next((t for t in type_ if t != "null"), None)

    return type_


def _encode(value: Any, *, native_json: bool = False) -> Any:
    """Turn a value into what the store file can hold: dates as ISO text, nested as JSON text."""
    if isinstance(value, date):  # datetime too
        return value.isoformat()

    if isinstance(value, (dict, list)) and not native_json:
        return json.dumps(value, ensure_ascii=False)

    return value


def _decode(value: Any, column: Column) -> Any:  # noqa: PLR0911
    """Turn a stored value back into Python, using the column type and format."""
    if value is None:
        return None

    if column.format == "date-time" and isinstance(value, str):
        return datetime.fromisoformat(value)

    if column.format == "date":
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            return date.fromisoformat(value)

    if column.type in {"object", "array"} and isinstance(value, str):
        return json.loads(value)

    if column.type == "boolean":
        return bool(value)

    return value


def _decode_row(row: dict[str, Any], columns: list[Column]) -> DataItem:
    record = {"id": row["id"]}
    record.update({column.name: _decode(row.get(column.name), column) for column in columns})
    record["created_at"] = _decode(row.get("created_at"), _TIMESTAMP)
    record["updated_at"] = _decode(row.get("updated_at"), _TIMESTAMP)

    return record


def _now() -> datetime:
    return datetime.now(UTC)


# -----------------------
# store protocol
# -----------------------


class Store(Protocol):
    """A repository of records, built from its path, table name and columns (`StoreFactory`)."""

    def init(self) -> None:
        """Create the file and table/sheet, does nothing if they exist."""
        ...

    def add(self, records: Data, *, keep_meta: bool = False) -> list[int]:
        """Append `records` and return their new ids, creating the store if missing.

        `keep_meta` keeps the records' own `id`, `created_at` and `updated_at` (for export).
        """
        ...

    def all(self) -> Data:
        """Return every record, ordered by id."""
        ...

    def get(self, id_: int) -> DataItem:
        """Return the record with `id_`, raises `RecordNotFoundError`."""
        ...

    def update(self, id_: int, record: DataItem) -> None:
        """Replace the record's columns, raises `RecordNotFoundError`."""
        ...

    def delete(self, id_: int) -> None:
        """Delete the record with `id_`, raises `RecordNotFoundError`."""
        ...

    def migrate(self) -> list[str]:
        """Add the schema columns the store is missing and return their names.

        Removed or retyped properties are left alone, no data is lost.
        """
        ...


type StoreFactory = Callable[[Path, str, list[Column]], Store]
"""Builds a store from its file path, table name and columns, usually the store class itself."""


def search(store: Store, filter_schema: ExpressionWrapperDict | PredicateDict) -> Data:
    """Return the records matching `filter_schema`, the same filter language as `--filter`."""
    # shortcut: loads every record then filters in Python, push down to SQL if stores get large
    return filter_data(store.all(), get_compiler(), filter_schema)


def get_many(store: Store, ids: Sequence[int]) -> Data:
    """Return the records with `ids`, in the given order, raises `RecordNotFoundError`."""
    by_id = {record["id"]: record for record in store.all()}

    for id_ in ids:
        if id_ not in by_id:
            raise RecordNotFoundError(id_)

    return [by_id[id_] for id_ in ids]


# -----------------------
# registry
# -----------------------


class StoreRegistry:
    """Maps store file extensions (case-insensitive, without the dot) to stores.

    Example:
    ```python
    stores = StoreRegistry()


    @stores.store("csv")
    class CsvStore: ...


    store = stores.create(Path("people.csv"), "people", columns)  # a CsvStore
    ```

    """

    def __init__(self) -> None:
        self._factories: dict[str, StoreFactory] = {}

    def __contains__(self, extension: str) -> bool:
        """Whether a store is registered for `extension`."""
        return extension.lower() in self._factories

    def __getitem__(self, extension: str) -> StoreFactory:
        """Return the store factory registered for `extension`.

        Raises:
            StoreExtensionNotSupportedError: No store is registered for `extension`.

        """
        if extension not in self:
            raise StoreExtensionNotSupportedError(extension, self.extensions)

        return self._factories[extension.lower()]

    @property
    def extensions(self) -> list[str]:
        """The supported extensions, sorted."""
        return sorted(self._factories)

    def store[T: StoreFactory](self, *extensions: str) -> Callable[[T], T]:
        """Register the decorated class (or factory) as the store for `extensions`."""

        def decorator(factory: T) -> T:
            for extension in extensions:
                self.add_store(factory, extension)

            return factory

        return decorator

    def add_store(self, factory: StoreFactory, extension: str) -> None:
        """Register `factory` as the store for `extension`, replacing any existing one."""
        self._factories[extension.lower()] = factory

    def create(self, path: Path, table: str, columns: list[Column]) -> Store:
        """Build the store matching the extension of `path`.

        Raises:
            StoreExtensionNotSupportedError: No store is registered for the extension.

        """
        return self[path.suffix.lstrip(".")](path, table, columns)


stores = StoreRegistry()
"""The default registry, used by the CLI `store` commands and `render --store`."""

# -----------------------
# concrete stores
# -----------------------


def _require(path: Path) -> None:
    if not path.exists():
        msg = f"Store '{path}' does not exist, create it with: templify store init"
        raise StoreError(msg)


def _quote(name: str) -> str:
    """Quote an SQL identifier, the names come from the schema."""
    return '"' + name.replace('"', '""') + '"'


@stores.store("sqlite", "db", "sqlite3")
class SqliteStore:
    """One sqlite table, nested objects and arrays stored as JSON text."""

    _SQL_TYPES: ClassVar = {"integer": "INTEGER", "boolean": "INTEGER", "number": "REAL"}

    def __init__(self, path: Path, table: str, columns: list[Column]) -> None:
        self.path = path
        self.table = _quote(table)
        self.columns = columns

    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with contextlib.closing(sqlite3.connect(self.path)) as conn, conn:  # one transaction
            conn.row_factory = sqlite3.Row

            yield conn

    def init(self) -> None:
        """Create the database file and table, does nothing if they exist."""
        columns = ", ".join(
            f"{_quote(c.name)} {self._SQL_TYPES.get(c.type or '', 'TEXT')}" for c in self.columns
        )

        with self._connect() as conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} ("
                f'"id" INTEGER PRIMARY KEY AUTOINCREMENT, {columns}, '
                '"created_at" TEXT, "updated_at" TEXT)'
            )

    def add(self, records: Data, *, keep_meta: bool = False) -> list[int]:
        """Insert `records` in one transaction and return their ids."""
        self.init()

        names = [c.name for c in self.columns] + ["created_at", "updated_at"]

        if keep_meta:
            names.insert(0, "id")

        sql = (
            f"INSERT INTO {self.table} ({', '.join(map(_quote, names))}) "  # noqa: S608
            f"VALUES ({', '.join('?' * len(names))})"
        )
        now = _now()
        ids: list[int] = []

        with self._connect() as conn:
            for record in records:
                row = (
                    {"created_at": now, "updated_at": now, **record}
                    if keep_meta
                    else {**record, "created_at": now, "updated_at": now}
                )
                cursor = conn.execute(sql, [_encode(row.get(name)) for name in names])

                assert cursor.lastrowid is not None  # set by INSERT

                ids.append(cursor.lastrowid)

        return ids

    def all(self) -> Data:
        """Return every record, ordered by id."""
        _require(self.path)

        with self._connect() as conn:
            rows = conn.execute(f'SELECT * FROM {self.table} ORDER BY "id"').fetchall()  # noqa: S608

        return [_decode_row(dict(row), self.columns) for row in rows]

    def get(self, id_: int) -> DataItem:
        """Return the record with `id_`."""
        _require(self.path)

        with self._connect() as conn:
            row = conn.execute(
                f'SELECT * FROM {self.table} WHERE "id" = ?',  # noqa: S608
                (id_,),
            ).fetchone()

        if row is None:
            raise RecordNotFoundError(id_)

        return _decode_row(dict(row), self.columns)

    def update(self, id_: int, record: DataItem) -> None:
        """Replace the record's columns and refresh `updated_at`."""
        _require(self.path)

        names = [c.name for c in self.columns] + ["updated_at"]
        values = [_encode(record.get(c.name)) for c in self.columns] + [_encode(_now())]
        assignments = ", ".join(f"{_quote(name)} = ?" for name in names)

        with self._connect() as conn:
            cursor = conn.execute(
                f'UPDATE {self.table} SET {assignments} WHERE "id" = ?',  # noqa: S608
                [*values, id_],
            )

        if cursor.rowcount == 0:
            raise RecordNotFoundError(id_)

    def delete(self, id_: int) -> None:
        """Delete the record with `id_`."""
        _require(self.path)

        with self._connect() as conn:
            cursor = conn.execute(f'DELETE FROM {self.table} WHERE "id" = ?', (id_,))  # noqa: S608

        if cursor.rowcount == 0:
            raise RecordNotFoundError(id_)

    def migrate(self) -> list[str]:
        """Add the missing schema columns with `ALTER TABLE ADD COLUMN`."""
        _require(self.path)
        self.init()  # the table may be missing

        with self._connect() as conn:
            existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({self.table})")}
            missing = [c for c in self.columns if c.name not in existing]

            for column in missing:
                conn.execute(
                    f"ALTER TABLE {self.table} ADD COLUMN {_quote(column.name)} "
                    f"{self._SQL_TYPES.get(column.type or '', 'TEXT')}"
                )

        return [c.name for c in missing]


class _FileStore:
    """CRUD over a list of raw rows, the subclasses only read and save the whole file."""

    native_json = True

    def __init__(self, path: Path, table: str, columns: list[Column]) -> None:
        self.path = path
        self.table = table
        self.columns = columns

    @property
    def header(self) -> list[str]:
        return ["id", *(c.name for c in self.columns), "created_at", "updated_at"]

    def _exists(self) -> bool:
        return self.path.exists()

    def _rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _save(self, rows: list[dict[str, Any]]) -> None:
        raise NotImplementedError

    def _encode_row(self, record: DataItem) -> dict[str, Any]:
        return {
            name: _encode(record.get(name), native_json=self.native_json) for name in self.header
        }

    def _index(self, rows: list[dict[str, Any]], id_: int) -> int:
        for idx, row in enumerate(rows):
            if row.get("id") == id_:
                return idx

        raise RecordNotFoundError(id_)

    def init(self) -> None:
        """Create the store file, does nothing if it exists."""
        if not self._exists():
            self._save([])

    def add(self, records: Data, *, keep_meta: bool = False) -> list[int]:
        """Append `records` and return their ids: the max id plus one, and so on."""
        self.init()

        rows = self._rows()
        next_id = max((row["id"] for row in rows), default=0) + 1
        now = _now()
        ids: list[int] = []

        for record in records:
            meta = {"id": next_id, "created_at": now, "updated_at": now}
            row = {**meta, **record} if keep_meta else {**record, **meta}
            rows.append(self._encode_row(row))
            ids.append(row["id"])
            next_id = max(next_id, row["id"]) + 1

        self._save(rows)

        return ids

    def all(self) -> Data:
        """Return every record, ordered by id."""
        _require(self.path)

        rows = sorted(self._rows(), key=lambda row: row["id"])

        return [_decode_row(row, self.columns) for row in rows]

    def get(self, id_: int) -> DataItem:
        """Return the record with `id_`."""
        _require(self.path)

        rows = self._rows()

        return _decode_row(rows[self._index(rows, id_)], self.columns)

    def update(self, id_: int, record: DataItem) -> None:
        """Replace the record's columns and refresh `updated_at`."""
        _require(self.path)

        rows = self._rows()
        idx = self._index(rows, id_)
        old = rows[idx]
        rows[idx] = self._encode_row(
            {**record, "id": id_, "created_at": old.get("created_at"), "updated_at": _now()}
        )

        self._save(rows)

    def delete(self, id_: int) -> None:
        """Delete the record with `id_`."""
        _require(self.path)

        rows = self._rows()
        del rows[self._index(rows, id_)]

        self._save(rows)

    def migrate(self) -> list[str]:
        """Nothing to add: a record missing a key already reads it as `None`."""
        _require(self.path)

        return []


def _write_atomic(path: Path, text: str) -> None:
    """Write through a temp file, so a failure never leaves a half-written store."""
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


@stores.store("json")
class JsonStore(_FileStore):
    """A JSON list of records, the same shape `render -d` reads."""

    def _rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = json.loads(self.path.read_text(encoding="utf-8"))

        return rows

    def _save(self, rows: list[dict[str, Any]]) -> None:
        _write_atomic(self.path, json.dumps(rows, ensure_ascii=False, indent=2, default=str))


@stores.store("jsonl")
class JsonlStore(_FileStore):
    """One JSON record per line."""

    def _rows(self) -> list[dict[str, Any]]:
        lines = self.path.read_text(encoding="utf-8").splitlines()

        return [json.loads(line) for line in lines if line.strip()]

    def _save(self, rows: list[dict[str, Any]]) -> None:
        lines = (json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows)
        _write_atomic(self.path, "".join(lines))


@stores.store("xlsx")
class XlsxStore(_FileStore):
    """One sheet named after the table, row 1 is the header, nested values as JSON text."""

    native_json = False

    def __init__(self, path: Path, table: str, columns: list[Column]) -> None:
        super().__init__(path, table, columns)

        self.sheet_name = table.translate(str.maketrans("", "", "[]:*?/\\"))[:31] or "Sheet"

    def _exists(self) -> bool:
        return (
            self.path.exists() and self.sheet_name in openpyxl.load_workbook(self.path).sheetnames
        )

    def _rows(self) -> list[dict[str, Any]]:
        sheet = openpyxl.load_workbook(self.path)[self.sheet_name]
        rows = sheet.iter_rows(values_only=True)
        header = [str(name) for name in next(rows, ())]

        return [
            dict(zip(header, row, strict=False)) for row in rows if any(v is not None for v in row)
        ]

    def _save(self, rows: list[dict[str, Any]]) -> None:
        if self.path.exists():
            wb = openpyxl.load_workbook(self.path)
        else:
            wb = openpyxl.Workbook()
            wb.remove(wb.worksheets[0])

        if self.sheet_name in wb.sheetnames:
            del wb[self.sheet_name]

        # existing columns first (even ones the schema dropped, no data loss), new ones appended
        header = list(dict.fromkeys([*(name for row in rows for name in row), *self.header]))
        sheet = wb.create_sheet(self.sheet_name)
        sheet.append(header)

        for row in rows:
            sheet.append([row.get(name) for name in header])

        wb.save(self.path)

    def migrate(self) -> list[str]:
        """Append the missing schema columns to the header row."""
        _require(self.path)
        self.init()  # the sheet may be missing

        sheet = openpyxl.load_workbook(self.path)[self.sheet_name]
        existing = next(sheet.iter_rows(max_row=1, values_only=True), ())
        missing = [name for name in self.header if name not in existing]

        if missing:
            self._save(self._rows())  # rewriting the sheet appends the new header cells

        return missing
