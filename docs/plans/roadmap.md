# Roadmap: record stores and next features

> **This turn's action, once approved:** save this file as `docs/plans/roadmap.md` in the repo
> and change nothing else. The phases below are run later, one per session
> ("run phase N of docs/plans/roadmap.md"). Each phase ends green on
> `uv run pytest`, `uv run ruff check`, `uv run ruff format --check` and `uv run mypy`, and is its own commit.

## Phases

- [x] **Phase 1: Store core.** `src/templify/stores.py`: `Column`, registry, `Store` protocol,
  encode/decode, ids + timestamps, and the four repositories (sqlite, xlsx, json, jsonl) with
  `init`/`add`/`all`/`get`/`update`/`delete`, plus `search`/`get_many`. `tests/test_stores.py`.
  Add `openpyxl` to dependencies. (Sections: Records and ids; Design.)
- [x] **Phase 2: `store` CLI (CRUD).** `store init/add/list/get/search/update/delete`,
  `cli/dependencies/store.py`, CLI tests. (Section: CLI, first 7 rows.)
- [x] **Phase 3: render integration.** `--store` saves the answers; `--store --id` regenerates
  from the store. (Section: CLI, `render`.)
- [x] **Phase 4: migrate / import / export.** `Store.migrate`, `store migrate/import/export`.
  (Section: CLI, last 3 rows.)
- [x] **Phase 5: Docs.** README "Storing records" + "Extending templify", bump the minor version.
- [ ] **Future phases** (each needs its own short design pass first): see the end of this file.

## Context

`templify render -s schema.json` asks the user for records with schemify, renders them, and throws
the answers away. The user wants the answers kept in a store file and managed later: a registry +
repository pattern, each store with `init` (create the starter file: sqlite db + table, xlsx
workbook + sheet + header, ...), CRUD methods, search, and re-rendering stored records by id.

Decisions (from the user):
- Stores: sqlite (`sqlite`, `db`, `sqlite3`), `xlsx`, `json`, `jsonl`.
- Code lives in templify: new `src/templify/stores.py`, beside `writers.py`.
- One table/sheet per schema, named from the schema `title` (fallback: schema file stem).
  Top-level `properties` are the columns, in schema order; nested objects/arrays are JSON text
  in sqlite/xlsx (native JSON in json/jsonl).
- CLI: a `templify store ...` command group, plus `--store` / `--id` on `render`.

## Records and ids

- Every stored record gets an integer `id` (first column), assigned by the store:
  sqlite `INTEGER PRIMARY KEY AUTOINCREMENT`; xlsx/json/jsonl `max(id) + 1` (ids never reused
  while the max row exists — fine for a local file).
- Every record also gets `created_at` and `updated_at` (`datetime.now(UTC)`, decoded back to
  `datetime`), set by `add`; `update` refreshes `updated_at` only. Column order:
  `id, <schema columns>, created_at, updated_at`.
- A schema that already has an `id`, `created_at` or `updated_at` property is rejected with a
  clear `StoreError`.
- Records read back include `id`, so templates can use `{{ id }}`.
- Values are decoded back to Python using the schema column type/format, the same for every store
  (one shared `_decode(value, column)`): `date` / `date-time` → `date` / `datetime`,
  `object` / `array` → `json.loads`, `boolean` → `bool`. Without this, a regenerated
  `{{ hired.strftime(...) }}` would break on a string. Encode is the mirror `_encode`.

## Design — `src/templify/stores.py` (new)

Mirror `WriterRegistry` in [writers.py](src/templify/writers.py) (same method names, same
error style), so the codebase keeps one registry shape.

- `Column` — small frozen dataclass `(name, type, format)` from `schema["properties"]`;
  `columns_from_schema(schema)`, `table_name(schema, schema_path)`.
- `Store` Protocol (the repository), every store implements:
  - `init() -> None` — create the file and table/sheet; idempotent.
  - `add(records: Data) -> list[int]` — append, return the new ids; auto-`init()` if file missing.
  - `all() -> Data`
  - `get(id) -> DataItem` — raises `RecordNotFoundError`.
  - `update(id, record: DataItem) -> None` — replace the record's columns; raises `RecordNotFoundError`.
  - `delete(id) -> None` — raises `RecordNotFoundError`.
  - `migrate() -> list[str]` — add schema columns missing from an existing table/sheet/records
    (sqlite `ALTER TABLE ADD COLUMN`; xlsx append header cells; json/jsonl nothing to do since
    missing keys already read as `None`), return the added names. Removed or retyped properties
    are left alone (no data loss).
- `search(store, filter_schema) -> Data` — one module function, not per store: `store.all()` then
  pyrecords `filter_data` with `get_compiler()`, i.e. the same JSON filter language as `--filter`
  (`templify filters` already lists its rules).
  `# shortcut: loads every record then filters in Python, push down to SQL if stores get large`.
- `get_many(store, ids) -> Data` — keeps the given order, raises `RecordNotFoundError` for a missing id.
- `StoreFactory = Callable[[Path, str, list[Column]], Store]`; `StoreRegistry` (`store(*extensions)`
  decorator, `add_store`, `__contains__`, `__getitem__`, `extensions`, `create(path, table, columns)`);
  `StoreExtensionNotSupportedError`, `StoreError`, `RecordNotFoundError(StoreError)`;
  `stores = StoreRegistry()`.

Concrete repositories:
- `SqliteStore` — stdlib `sqlite3`. Types: `integer`/`boolean` → `INTEGER`, `number` → `REAL`,
  else `TEXT`. Identifiers quoted `"..."` with `"` doubled (names come from the schema); values
  always as `?` parameters. Writes inside `with conn:` (one transaction). Dates stored ISO text.
- `XlsxStore` — `openpyxl` (add to `dependencies` in pyproject.toml, now imported directly).
  Sheet name: strip `[]:*?/\`, max 31 chars; row 1 = header `id, <columns>`. `update`/`delete`
  find the row by the `id` cell (`delete_rows`). Every write = load, change, save.
- `JsonStore` — the file is a JSON list of records (the shape `-d data.json` reads, so a store can
  be fed back to `render -d`). Load, change, write via temp file + `Path.replace` (no half-written
  file). `ensure_ascii=False`, `indent=2`, `default=str`.
- `JsonlStore` — one record per line. `add` appends lines; `update`/`delete` rewrite the file via
  temp file + `Path.replace`.
- The three file-based stores share a tiny base (`_rows()` / `_save(rows)`) so CRUD logic is
  written once; sqlite has its own SQL.

## CLI

New `store` group in [cli.py](src/templify/cli/cli.py) (`TyperDI` sub-app, `app.add_typer(..., name="store")`,
alias via `typer_swissknife.command` like the existing commands). Every command takes
`-s schema.json` + the store `PATH` (schema gives the table name and column types). A shared
dependency in a new `src/templify/cli/dependencies/store.py` builds the store, reusing
`load_schema` / `ask_or_abort` from `schemify.cli.dependencies.schema` (already used in data.py).

| Command | Does |
|---|---|
| `store init -s S PATH` | create the starter file/table |
| `store add -s S PATH` | ask records (`ask_list`) and save, print new ids |
| `store list -s S PATH` | rich `Table` of all records |
| `store get -s S PATH ID` | one record |
| `store search -s S PATH --filter JSON` | matching records (reuses `_get_filter_schema` parsing from data.py) |
| `store update -s S PATH ID` | re-ask the whole record (`ask_data`), replace it |
| `store delete -s S PATH ID` | delete (asks `typer.confirm`, `--yes` to skip) |
| `store migrate -s S PATH` | add new schema columns, print them |
| `store import -s S PATH -d FILE` | read FILE with pyrecords `readers`, keep schema columns, validate each row with schemify `check_value`, `add` them all (all-or-nothing: validate every row first) |
| `store export -s S PATH TARGET` | `all()` from PATH, `add` into a new store at TARGET (any registered extension); ids and timestamps are copied as-is, so `add` takes an internal `keep_meta` flag used only here |

`render` ([data.py](src/templify/cli/dependencies/data.py), in `_read`):
- `--store PATH` with `-s` → ask as today, save the answers (`[data]` in `--object` mode) **before**
  order/filter/group/render, so a template error never loses answers.
- `--store PATH --id N` (repeatable) with `-s` → regenerate: load those records instead of asking;
  `--object` requires exactly one `--id`. Existing `--order` / `--filter` / `--group-by` then apply.
- `--store` with `-d`, or `--id` without `--store` → `typer.BadParameter`.

Errors: unsupported extension → `BadParameter` before any question is asked;
`RecordNotFoundError` → `BadParameter`; `StoreError`, `sqlite3.Error`, `OSError` (xlsx open in
Excel) → red message + exit 1 (existing `_fail`). If saving freshly asked answers fails, the
message includes the answers as JSON so they can be recovered.

## Tests

- `tests/test_stores.py`, parametrized over the four extensions: `init` creates the file
  (sqlite `PRAGMA table_info`, xlsx header, json `[]`, jsonl empty) and is idempotent; `add`
  returns increasing ids and auto-inits; `get`/`all` round-trip dates, nested objects and booleans;
  `update` and `delete` work and raise `RecordNotFoundError` for a missing id; ids not reused
  after deleting a middle row; `search` with a filter schema; schema with `id` property rejected;
  quoted identifiers with `"`; unsupported extension; json store readable by pyrecords `readers["json"]`;
  `created_at`/`updated_at` set and refreshed; `migrate` adds a new property and keeps old rows;
  export sqlite → xlsx → json keeps ids, values and timestamps; import rejects the whole file when one row is invalid.
- `tests/test_cli.py`, reusing `answer` + `person_schema` fixtures: each `store` command;
  `render -s --store` saves and renders; `render --store --id` regenerates without asking;
  `--object` with two ids rejected; `--store` with `-d` rejected.

## Docs

README: "Storing records" section (stores + extensions, `store` commands, `--store` / `--id`,
type mapping, ids, nested → JSON text) and an "Extending templify" entry for `@stores.store(...)`.
Add the command group to the Commands table.

## Verification

```powershell
uv run pytest
```
```powershell
uv run ruff check; uv run ruff format --check; uv run mypy
```
Manual, for `people.sqlite` and `people.xlsx`: `store init`, `render -s ... --store ...` answering
two people, `store list`, `store search --filter ...`, `store update ... 1`,
`render -s ... --store ... --id 1 -t t.txt -o out`, `store delete ... 2`; open the files to check.

## Not doing (ask if wanted)

Child tables for arrays; dropping/retyping columns in `migrate`; csv store; `update` pre-filling
the old values as defaults (needs schemify support); SQL push-down for search; concurrent writers.

## Future phases (ideas, not designed yet)

Stores:
- [ ] **6. Pre-filled update.** `store update` shows the old values as defaults (schemify `ask_data` needs a `defaults` argument first).
- [ ] **7. Stores as `-d` sources.** A sqlite reader in pyrecords, so `render -d people.sqlite` works.
- [ ] **8. Render log.** Record which files were rendered from which record, and when.
- [ ] **9. CSV store.** One more `@stores.store("csv")`.

Rendering:
- [ ] **10. PDF output.** `--pdf` converts rendered docx/html (LibreOffice `soffice --convert-to pdf`, or docx2pdf on Windows).
- [ ] **11. Dry run / preview.** `--dry-run` lists the files that would be written; `--preview` prints the first rendered text.
- [ ] **12. Overwrite policy.** `--overwrite` / `--skip-existing` beside today's random suffix.
- [ ] **13. Filename templates.** `-n "{{ id }} - {{ name }}"` as a Jinja expression.
- [ ] **14. Merged output.** `--each --merge` joins the generated docx files into one for printing.
- [ ] **15. More template formats.** `.xlsx` (Jinja in cells), `.pptx`, `.eml`.

Data:
- [ ] **16. CSV / TSV readers** in pyrecords.
- [ ] **17. Jinja filters.** Number/date formatting, Arabic number-to-words (tafqit), Hijri dates.
- [ ] **18. Presets.** `templify.toml` named jobs, run with `templify run <name>`.

Developer experience:
- [ ] **19. `templify check`.** Report template variables missing from the data or schema.
- [ ] **20. Shell completion** of column names for `--order`, `--group-by` and `-n`.
