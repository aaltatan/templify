# Render modes

`render` has three modes. The mode decides what the template sees and how many files
are written:

| Mode | Data | Writes | The template sees |
|------|------|--------|-------------------|
| *(default)* | a list of rows | **one file** with all the rows | the rows as a list, `objects`: `{% for e in objects %}` |
| `--each` | a list of rows | **one file per row** (or per group) | each row's columns: `{{ name }}`, `{{ salary }}` |
| `--object` | a **single record** | **one file** | the record as `object`: `{{ object.name }}` |

## All rows in one file (default)

Use it for reports, lists, exports: anything that shows many rows together.

```bash
templify render -t team.md -d employees.xlsx -o reports --order -salary
```

The rows are in `objects`. Rename the variable with `-v` and the file with `-f`:

```bash
templify render -t team.md -d employees.xlsx -o reports -f "2024 team"
```

The file is saved as `reports/2024 team.md`. With `-v employees`, the template loops
with `{% for e in employees %}` instead: handy when one template is shared with another
tool that uses that name.

| Option | Default | Meaning |
|--------|---------|---------|
| `-f, --filename` | the template's name | Output file name, without extension |
| `-v, --var` | `objects` | The variable holding the rows |

## One file per row (`--each`)

Use it for letters, certificates, emails, profiles: one document per person, product
or customer.

```bash
templify render -t offer.docx -d employees.xlsx -o offers --each -n name --numbered
```

![templify render --each](../demo/each.gif)

Each row's **columns are the variables**: `{{ name }}`, `{{ salary }}`. There is no
`objects` in this mode.

| Option | Default | Meaning |
|--------|---------|---------|
| `-n, --name-by` | `template-<n>` | The column naming each file |
| `--numbered` | off | Prefix each file name with its row number: `1 - Rama.docx` |

With [`--group-by`](grouping.md), `--each` writes one file per **group** instead.

## One record (`--object`)

Use it when the data is **one** thing: a single certificate, an invoice, a contract,
typed in on the spot or read from a JSON object.

`letter.md`:

```jinja
Dear {{ object.name }},

This letter confirms that you work in our {{ object.department }} department in {{ object.city }}.
```

```bash
templify render -t letter.md -d rama.json --object -o letters
```

`rama.json` is a JSON **object**, not a list:

```json
{"id": 3, "name": "Rama", "department": "IT", "city": "Homs", "salary": 1500, "hired": "2024-02-10", "email": "rama@example.com"}
```

With `-s`, templify asks for the fields instead of reading a file:

```text
templify render -t letter.md -s person.schema.json --object
```

![templify render --object -s](../demo/schema.gif)

`-f` and `-v` work here too (`-v` defaults to `object`). `--order`, `--filter` and
`--group-by` do not: there is only one record.

## Options that do not fit the mode

An option used in a mode that does not take it is an error, never silently ignored:

```text
$ templify render -t team.md -d employees.xlsx -n name
Invalid value: --name-by only works with --each

$ templify render --each -t welcome.txt -d employees.xlsx -f all
Invalid value: --filename does not work with --each

$ templify render --each --object -t letter.md -d rama.json
Invalid value: --each and --object can not be used together
```
