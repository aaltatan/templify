import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl
import pytest
from pyrecords import readers

from templify.stores import (
    Column,
    RecordNotFoundError,
    Store,
    StoreError,
    StoreExtensionNotSupportedError,
    columns_from_schema,
    get_many,
    search,
    stores,
    table_name,
)

EXTENSIONS = ["sqlite", "xlsx", "json", "jsonl"]

SCHEMA: dict[str, Any] = {
    "title": "people",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "hired": {"type": "string", "format": "date"},
        "active": {"type": "boolean"},
        "address": {"type": "object"},
        "tags": {"type": ["array", "null"]},
        "age": {"type": "integer"},
    },
}

RAMA = {
    "name": "Rama",
    "hired": "2024-01-15",
    "active": True,
    "address": {"city": "Homs"},
    "tags": ["a", "ب"],
    "age": 25,
}


def make_store(tmp_path: Path, extension: str, schema: dict[str, Any] = SCHEMA) -> Store:
    return stores.create(
        tmp_path / f"people.{extension}",
        table_name(schema, Path("x.json")),
        columns_from_schema(schema),
    )


@pytest.fixture(params=EXTENSIONS)
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Store:
    return make_store(tmp_path, request.param)


def test_init_creates_starter_file_and_is_idempotent(tmp_path: Path) -> None:
    for extension in EXTENSIONS:
        make_store(tmp_path, extension).init()
        make_store(tmp_path, extension).init()

    with sqlite3.connect(tmp_path / "people.sqlite") as conn:
        columns = [row[1] for row in conn.execute('PRAGMA table_info("people")')]

    assert columns == ["id", *SCHEMA["properties"], "created_at", "updated_at"]

    sheet = openpyxl.load_workbook(tmp_path / "people.xlsx")["people"]

    assert next(sheet.iter_rows(values_only=True))[0] == "id"
    assert json.loads((tmp_path / "people.json").read_text()) == []
    assert (tmp_path / "people.jsonl").read_text() == ""


def test_add_auto_inits_and_round_trips(store: Store) -> None:
    assert store.add([RAMA, {"name": "Rawaa"}]) == [1, 2]
    assert store.add([{"name": "Abdullah"}]) == [3]

    rama = store.get(1)

    assert rama["hired"] == date(2024, 1, 15)
    assert rama["active"] is True
    assert rama["address"] == {"city": "Homs"}
    assert rama["tags"] == ["a", "ب"]
    assert rama["age"] == 25
    assert isinstance(rama["created_at"], datetime)
    assert rama["created_at"] == rama["updated_at"]
    assert [r["name"] for r in store.all()] == ["Rama", "Rawaa", "Abdullah"]
    assert store.get(2)["address"] is None


def test_update_and_delete(store: Store) -> None:
    store.add([RAMA, {"name": "Rawaa"}, {"name": "Abdullah"}])
    created = store.get(1)["created_at"]

    store.update(1, {"name": "Rama A."})
    updated = store.get(1)

    assert updated["name"] == "Rama A."
    assert updated["hired"] is None
    assert updated["created_at"] == created
    assert updated["updated_at"] > created

    store.delete(2)

    assert [r["id"] for r in store.all()] == [1, 3]
    assert store.add([{"name": "New"}]) == [4]  # ids not reused while the max row exists

    for call in (lambda: store.get(9), lambda: store.update(9, {}), lambda: store.delete(9)):
        with pytest.raises(RecordNotFoundError):
            call()


def test_missing_store_file(store: Store) -> None:
    with pytest.raises(StoreError, match="store init"):
        store.all()


def test_search_and_get_many(store: Store) -> None:
    store.add([RAMA, {"name": "Rawaa"}, {"name": "Abdullah"}])
    found = search(
        store,
        {"name": "string__startswith", "args": ["name", "Ra"], "kwargs": {}, "inverse": False},
    )

    assert [r["id"] for r in found] == [1, 2]
    assert [r["name"] for r in get_many(store, [3, 1])] == ["Abdullah", "Rama"]

    with pytest.raises(RecordNotFoundError):
        get_many(store, [1, 7])


@pytest.mark.parametrize("extension", EXTENSIONS)
def test_quoted_identifiers(tmp_path: Path, extension: str) -> None:
    schema = {"title": 'my "table"', "properties": {'a "b"': {"type": "string"}}}
    store = make_store(tmp_path, extension, schema)
    store.add([{'a "b"': "x"}])

    assert store.get(1)['a "b"'] == "x"


def test_reserved_property_rejected() -> None:
    with pytest.raises(StoreError, match="id, created_at"):
        columns_from_schema({"properties": {"id": {}, "created_at": {}, "x": {}}})


def test_table_name_falls_back_to_schema_stem() -> None:
    assert table_name({}, Path("person.schema.json")) == "person.schema"


def test_unsupported_extension(tmp_path: Path) -> None:
    with pytest.raises(StoreExtensionNotSupportedError, match="sqlite"):
        stores.create(tmp_path / "people.csv", "people", [Column("name")])


def test_json_store_is_readable_as_data(tmp_path: Path) -> None:
    store = make_store(tmp_path, "json")
    store.add([RAMA])

    assert readers["json"](tmp_path / "people.json")[0]["address"] == {"city": "Homs"}


@pytest.mark.parametrize("extension", EXTENSIONS)
def test_migrate_adds_new_property_and_keeps_rows(tmp_path: Path, extension: str) -> None:
    old = {"title": "people", "properties": {"name": {"type": "string"}, "gone": {}}}
    make_store(tmp_path, extension, old).add([{"name": "Rama", "gone": "kept"}])

    new = {
        "title": "people",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
    }
    store = make_store(tmp_path, extension, new)
    added = store.migrate()

    assert added == ([] if extension.startswith("json") else ["age"])
    assert store.migrate() == []

    store.add([{"name": "Rawaa", "age": 33}])

    assert [(r["name"], r["age"]) for r in store.all()] == [("Rama", None), ("Rawaa", 33)]
    assert make_store(tmp_path, extension, old).get(1)["gone"] == "kept"  # no data loss


def test_export_keeps_ids_values_and_timestamps(tmp_path: Path) -> None:
    source = make_store(tmp_path, "sqlite")
    source.add([RAMA, {"name": "Rawaa"}, {"name": "Abdullah"}])
    source.delete(2)
    expected = source.all()

    for extension in ("xlsx", "json"):
        copy = make_store(tmp_path, extension)
        copy.add(source.all(), keep_meta=True)

        assert copy.all() == expected

        source = copy

    assert source.add([{"name": "New"}]) == [4]
