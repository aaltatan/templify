# Data sources

`render` takes **exactly one** data source:

| Option | Source |
|--------|--------|
| `-d, --data` | A data file. The reader comes from its extension, ignoring case. |
| `-s, --schema` | A JSON Schema. templify asks for the data matching it. |

Giving both, or neither, is an error:

```text
Invalid value: Give exactly one data source: -d / --data or -s / --schema
```

## Excel (`.xlsx`)

The **active sheet** is read: the one that was open when the workbook was last saved.

- The first row holds the column names, and each following row is one record.
- Fully blank rows are skipped.
- **Formula cells give their last calculated value**, not the formula text. A file
  created by a script and never opened in Excel has no calculated values yet, so those
  cells come back empty. Open and save it in Excel once.
- Values keep their type:

| Excel cell | In the template |
|------------|-----------------|
| Text | a string |
| Number | an `int` or `float`: `{{ salary + 100 }}` works |
| Date | a Python `datetime`: `{{ hired.strftime("%Y") }}` works |
| Empty | `None`: `{{ email or "no email" }}` |

!!! tip "Leading zeros"
    An ID like `00042` typed into a number cell becomes `42`. Format such columns as
    **Text** in Excel, or pad them back in the template with
    `{{ id | to_str | str.zfill(5) }}`.

## JSON (`.json`)

A **list of objects**, one per record:

```json
[
  {"id": 1, "name": "Abdullah", "department": "Sales", "city": "Homs", "salary": 1200, "hired": "2021-04-01", "email": "abdullah@example.com"},
  {"id": 4, "name": "Omar", "department": "Sales", "city": "Aleppo", "salary": 1100, "hired": "2024-11-03", "email": null}
]
```

- Read as UTF-8, so Arabic and other non-Latin text works.
- An object, a list of numbers, and so on are rejected with a clear error.
- **JSON has no date type**, so dates are strings (`"2024-02-10"`). `hired.strftime(...)`
  fails on a string. Convert first with `to_date`, which accepts both a string and an
  Excel date:

    ```jinja
    {{ hired | to_date | date.strftime("%d/%m/%Y") }}
    ```

    The [`date__*` filter rules](order-filter.md#dates) accept both forms too.

For [`--object`](modes.md#one-record-object), the file holds a single JSON **object**
instead of a list.

## Other formats

CSV and other formats are not read directly. Open a CSV in Excel and save it as
`.xlsx`, or convert it to JSON. Adding a reader is a few lines of Python: see
[Extending templify](../reference/extending.md#a-new-data-source).

## Typing the data in

No data file? Give a [JSON Schema](https://json-schema.org), and templify asks for each
record with [schemify](https://github.com/aaltatan/schemify-cli).
[`examples/person.schema.json`](https://github.com/aaltatan/templify/blob/main/examples/person.schema.json):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Person",
  "type": "object",
  "properties": {
    "name": { "title": "Name", "type": "string" },
    "department": { "title": "Department", "type": "string", "enum": ["IT", "Sales", "HR"] },
    "city": { "title": "City", "type": "string" },
    "hired": { "title": "Hired on", "type": "string", "format": "date" }
  },
  "required": ["name", "department", "city"],
  "additionalProperties": false
}
```

| Mode | templify asks for |
|------|-------------------|
| default, `--each` | a **list**: one record after another, until you answer **No** |
| `--object` | **one** record |

```text
templify render --each -t letter.md -s person.schema.json -n name
templify render --object -t certificate.docx -s person.schema.json
```

![templify render -s: typing a list of records](../demo/schema-list.gif)

- `title` is the question, `type` and `format` pick the input, and `enum` gives a list
  to choose from.
- Answers are checked against the schema (`minimum`, `pattern`, `required`, ...).
- ++ctrl+c++ cancels without writing anything.
- The answers are forgotten after rendering. To keep them, add a
  [store](stores.md).

!!! note "With `--each`, the template uses the columns directly"
    `letter.md` uses `{{ object.name }}`, so it is meant for `--object`. A template for
    `--each` uses `{{ name }}`.
