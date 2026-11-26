# Storing records

`render -s` asks for records and forgets them once the files are written. A **store**
keeps them in a file, so you can list, search, fix and re-render them later: a small
register of certificates issued, visitors, contracts, or anything you type in.

## Store files

The store type comes from the file extension:

| Extension | Store |
|-----------|-------|
| `.sqlite`, `.db`, `.sqlite3` | One SQLite table |
| `.xlsx` | One sheet; row 1 is the header |
| `.json` | A JSON list of records, readable again with `render -d` |
| `.jsonl` | One JSON record per line |

The **schema** decides the shape:

- The table (or sheet) is named after the schema's `title`, or the schema file name
  without `.json`.
- Every top-level property is a column, in schema order. Nested objects and arrays are
  JSON text in SQLite and Excel, and plain JSON in `.json` / `.jsonl`.
- Every record also gets an `id` (the first column, given by the store, never reused
  while a higher id exists), and `created_at` and `updated_at` (UTC). A schema cannot
  declare these three properties itself.
- Values read back keep their types: `date` / `date-time` properties become dates (so
  `{{ hired.strftime("%d/%m/%Y") }}` works), objects and arrays become dicts and lists,
  and booleans stay booleans. SQLite stores `integer` and `boolean` as `INTEGER`,
  `number` as `REAL`, and everything else as `TEXT`.

## Save while rendering

Add `--store` to a `render -s` command. The answers are saved **before** rendering, so a
template error never loses them, and templates can use `{{ id }}`:

```text
templify render --object -s person.schema.json --store people.sqlite -t certificate.docx -o certificates
```

Re-render stored records with `--id`, without asking anything. `--id` is repeatable,
and `--order`, `--filter` and `--group-by` still apply:

```text
templify render --object -s person.schema.json --store people.sqlite --id 3 -t certificate.docx
templify render -s person.schema.json --store people.sqlite --id 1 --id 2 -t names.txt -f picked
```

`--object` takes exactly one `--id`. `--store` only works with `-s` (not `-d`), and
`--id` needs `--store`.

## The `store` commands

Every command takes the schema (`-s`) and the store `PATH`:

| Command | Does |
|---------|------|
| `store init -s S PATH` | Create the file and its table or sheet (does nothing if they exist) |
| `store add -s S PATH` | Ask for records and add them; prints the new ids |
| `store list -s S PATH` (`ls`) | Show every record |
| `store get -s S PATH ID` | Show one record |
| `store search -s S PATH --filter JSON` | Show the records matching a [filter](order-filter.md#filter) |
| `store update -s S PATH ID` | Ask for the whole record again and replace it |
| `store delete -s S PATH ID` (`rm`) | Delete a record after a confirmation (`-y` / `--yes` skips it) |
| `store migrate -s S PATH` | Add new schema properties as columns, keeping every row |
| `store import -s S PATH -d FILE` | Add every row of an `.xlsx` / `.json` file, or none if one row is invalid |
| `store export -s S PATH TARGET` | Copy every record, ids and timestamps included, into a new store |

A full round trip with the example files:

```bash
templify store init -s person.schema.json people.sqlite
templify store import -s person.schema.json people.sqlite -d employees.json
templify store list -s person.schema.json people.sqlite
templify store get -s person.schema.json people.sqlite 3
templify store search -s person.schema.json people.sqlite --filter '{"name": "string__eq", "args": ["city", "Homs"], "kwargs": {}, "inverse": false}'
templify store delete -s person.schema.json people.sqlite 4 --yes
templify store export -s person.schema.json people.sqlite people.xlsx
templify render --object -s person.schema.json --store people.sqlite --id 3 -t certificate.docx -o certificates
```

The first three print:

```text
Store ready
Imported 4 records
 id  name      department  city      hired       created_at                        updated_at
 1   Abdullah  Sales       Homs      2021-04-01  2026-11-26 02:10:25.142463+00:00  2026-11-26 02:10:25.142463+00:00
 2   Rawaa     IT          Damascus  2023-09-15  ...
 3   Rama      IT          Homs      2024-02-10  ...
 4   Omar      Sales       Aleppo    2024-11-03  ...
```

`import` keeps only the schema's columns (here `name`, `department`, `city`, `hired`),
and treats empty cells as missing values. The last line renders the stored record 3,
without asking anything.

`export` only creates **new** stores: it refuses a target that already exists. Use it to
share the register as Excel, or to move from JSON to SQLite as it grows.

## Changing the schema

Add a property to the schema (say `"phone": {"type": "string"}`), then:

```text
$ templify store migrate -s person.schema.json people.sqlite
Added columns: phone
```

`migrate` never drops or retypes a column: properties you remove keep their data.

## When saving fails

If the store cannot be written (for example, the workbook is open in Excel), the run
exits with code 1, and the error prints the answers as JSON, so nothing you typed is
lost:

```text
Store Error: [Errno 13] Permission denied: 'people.xlsx'
The answers were not saved:
[
  {
    "name": "Rama",
    ...
  }
]
```
