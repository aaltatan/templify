# templify

A command line tool that fills document templates with data.

Point it at a **template** (Word, text, Markdown, HTML or JSON) and a **data file** (Excel or JSON). templify renders one file per row, or one file with every row in it. Before rendering, you can **order**, **filter** and **group** the data.

```bash
templify m -t offer.docx -d employees.xlsx -o offers -k name
```

```text
offers/
├── Abdullah.docx
├── Rawaa.docx
├── Rama.docx
└── Omar.docx
```

---

## Table of contents

- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Commands](#commands)
  - [`multiple-templates` (`m`)](#multiple-templates-m)
  - [`single-template` (`s`)](#single-template-s)
  - [`filters-json-schema` (`fjs`)](#filters-json-schema-fjs)
- [Data sources](#data-sources)
- [Templates](#templates)
  - [Supported formats](#supported-formats)
  - [Jinja2 in 60 seconds](#jinja2-in-60-seconds)
  - [Built-in variables](#built-in-variables)
  - [Word (`.docx`) templates](#word-docx-templates)
  - [JSON templates](#json-templates)
  - [HTML templates](#html-templates)
- [Output files](#output-files)
- [Ordering](#ordering)
- [Filtering](#filtering)
  - [Filter schema](#filter-schema)
  - [Filter rules reference](#filter-rules-reference)
- [Grouping](#grouping)
- [Cookbook](#cookbook)
- [Errors](#errors)
- [Extending templify](#extending-templify)
- [Development](#development)

---

## Features

- **Many template formats**: `.docx`, `.txt`, `.md`, `.html`, `.htm` and `.json`. The writer is picked automatically from the template's extension.
- **Many data sources**: Excel (`.xlsx`) and JSON (`.json`).
- **Two output modes**: one file per row (`multiple-templates`), or every row in one file (`single-template`).
- **Ordering** by any number of columns, ascending or descending.
- **Filtering** with a JSON filter language: 50+ rules for strings, numbers, decimals, dates, datetimes and UUIDs. Rules combine with `all` / `any`, nest, and can be inverted.
- **Grouping** by one or more columns, e.g. one file per department listing its employees.
- **Safe output**: existing files are never overwritten, invalid filename characters are replaced, and missing folders are created.
- **Validated JSON output**: a JSON template that renders invalid JSON is rejected before anything is saved.
- **Clear errors** for bad templates, bad data, unknown columns and bad filters, instead of Python tracebacks.
- **Extensible**: add a new data reader, template writer or filter rule with one decorator.

## Installation

Requires **Python 3.12+**.

Install it as a global command from PyPI with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install templify-cli
```

or with [pipx](https://pipx.pypa.io/):

```bash
pipx install templify-cli
```

Or run it from a clone without installing:

```bash
uv sync
```

```bash
uv run templify --help
```

## Quick start

**1. Prepare your data**, e.g. `employees.xlsx`. The first row holds the column names:

| name     | department | city     | salary | hired      | email                |
| -------- | ---------- | -------- | -----: | ---------- | -------------------- |
| Abdullah | Sales      | Homs     |   1200 | 2021-04-01 | abdullah@example.com |
| Rawaa    | IT         | Damascus |   1800 | 2023-09-15 | rawaa@example.com    |
| Rama     | IT         | Homs     |   1500 | 2024-02-10 | rama@example.com     |
| Omar     | Sales      | Aleppo   |   1100 | 2024-11-03 |                      |

**2. Write a template** that uses the column names as variables, e.g. `welcome.txt`:

```jinja
Hello {{ name }},
You joined {{ department }} on {{ hired.strftime("%d/%m/%Y") }}.
```

**3. Run templify:**

```bash
templify m -t welcome.txt -d employees.xlsx -o welcome -k name
```

`welcome/Rama.txt`:

```text
Hello Rama,
You joined IT on 10/02/2024.
```

> The same data file is used in every example below.

## How it works

Every command runs the same pipeline:

```text
 read data ──► order ──► filter ──► group ──► render template ──► save file(s)
  (-d)        (--order)  (--filter)  (--group-by)    (-t)              (-o)
```

1. **Read**: the data file becomes a list of rows, each row a set of `column: value` pairs.
2. **Order**: rows are sorted by `--order` columns (optional).
3. **Filter**: rows not matching `--filter` are dropped (optional).
4. **Group**: rows are grouped by `--group-by` columns (optional).
5. **Render**: the writer chosen from the template extension renders the rows.
6. **Save**:
   - `multiple-templates` saves one file per row, or per group when grouping.
   - `single-template` saves one file containing every row.

## Commands

```bash
templify --help
```

| Command               | Aliases               | What it does                                 |
| --------------------- | --------------------- | -------------------------------------------- |
| `multiple-templates`  | `multiple`, `m`       | Render **one file per row** (or per group)   |
| `single-template`     | `single`, `s`         | Render **one file** with all the rows        |
| `filters-json-schema` | `filters-schema`, `fjs` | List the filter rules and their arguments  |

### `multiple-templates` (`m`)

Renders the template once **per row**. Each row's columns are the template variables: `{{ name }}`, `{{ salary }}`, ...

```bash
templify m -t <template> -d <data> -o <output-dir> [OPTIONS]
```

| Option             | Short | Description                                                          | Default          |
| ------------------ | ----- | -------------------------------------------------------------------- | ---------------- |
| `--template`       | `-t`  | Template file. **Required.**                                         |                  |
| `--data`           | `-d`  | Data file. **Required.**                                             |                  |
| `--output`         | `-o`  | Output directory, created if missing. **Required.**                  |                  |
| `--filename-key`   | `-k`  | Column whose value names each file                                   | `template-<n>`   |
| `--index`          | `-i`  | Prefix each filename with its row number: `1 - Rama.docx`            | off              |
| `--order`          |       | Column to order by, `-column` for descending. Repeatable             |                  |
| `--filter`         |       | JSON [filter schema](#filter-schema)                                 |                  |
| `--group-by`       |       | Column to [group](#grouping) by. Repeatable                          |                  |
| `--group-items`    |       | Variable name holding each group's rows                              | `items`          |

Example:

```bash
templify m -t offer.docx -d employees.xlsx -o offers -k name --index
```

```text
offers/
├── 1 - Abdullah.docx
├── 2 - Rawaa.docx
├── 3 - Rama.docx
└── 4 - Omar.docx
```

### `single-template` (`s`)

Renders the template **once**, with every row in a list variable (`data` by default). The template loops over it.

```bash
templify s -t <template> -d <data> -o <output-dir> [OPTIONS]
```

| Option            | Short | Description                                                | Default                |
| ----------------- | ----- | ---------------------------------------------------------- | ---------------------- |
| `--template`      | `-t`  | Template file. **Required.**                               |                        |
| `--data`          | `-d`  | Data file. **Required.**                                   |                        |
| `--output`        | `-o`  | Output directory, created if missing. **Required.**        |                        |
| `--filename`      | `-f`  | Output filename **without** extension                      | the template's name    |
| `--data-variable` | `-v`  | Name of the list variable inside the template              | `data`                 |
| `--order`         |       | Column to order by, `-column` for descending. Repeatable   |                        |
| `--filter`        |       | JSON [filter schema](#filter-schema)                       |                        |
| `--group-by`      |       | Column to [group](#grouping) by. Repeatable                |                        |
| `--group-items`   |       | Variable name holding each group's rows                    | `items`                |

Example with `team.md`:

```jinja
# Team report

| # | Name | Department | Salary |
|---|------|------------|-------:|
{% for e in data -%}
| {{ loop.index }} | {{ e.name }} | {{ e.department }} | {{ "{:,}".format(e.salary) }} |
{% endfor %}
**Total salaries:** {{ data | sum(attribute="salary") }}
```

```bash
templify s -t team.md -d employees.xlsx -o reports --order -salary
```

`reports/team.md`:

```markdown
# Team report

| # | Name | Department | Salary |
|---|------|------------|-------:|
| 1 | Rawaa | IT | 1,800 |
| 2 | Rama | IT | 1,500 |
| 3 | Abdullah | Sales | 1,200 |
| 4 | Omar | Sales | 1,100 |

**Total salaries:** 5600
```

Rename the output and the loop variable:

```bash
templify s -t team.md -d employees.xlsx -o reports -f "2024 team" -v employees
```

The template then loops with `{% for e in employees %}`, and the file is saved as `reports/2024 team.md`.

### `filters-json-schema` (`fjs`)

Lists every filter rule you can use in `--filter`, with its arguments (in `args` order) and description:

```bash
templify fjs
```

```text
 Rule                 Arguments                         Description
 is_true              key: string                       Keep records where `key` is `true`.
 is_null              key: string                       Keep records where `key` is empty (`null`).
 int__eq              key: string, value: integer       Keep records where `key` equals `value`.
 ...
 string__regex        key: string, pattern: string      Keep records where `key` matches the regular expression `pattern`.
 string__is_in        key: string, value: list[string]  Keep records where `key` is one of the `value` list.
 ...
 date__ge             key: string, value: date          Keep records where `key` is greater than or equal to `value`, comparing the day only.
 ...
```

The argument names are also the `kwargs` names: `{"key": "salary", "value": 1400}`.

## Data sources

The reader is chosen from the data file extension, ignoring case.

| Extension | Format                                                                      |
| --------- | --------------------------------------------------------------------------- |
| `.xlsx`   | Excel workbook: the **active sheet**, first row = column names              |
| `.json`   | A JSON **list of objects**: `[{"name": "Rama", ...}, ...]`                  |

**Excel notes**

- The first row holds the column names, and each following row is one record.
- Fully blank rows are skipped.
- Formula cells give their **last calculated value**, not the formula text. A file created by a script and never opened in Excel has no calculated values yet, so those cells come back empty.
- Values keep their type: numbers stay numbers, dates become Python `datetime`s (so `{{ hired.strftime("%Y") }}` works), and empty cells become `None`.

**JSON notes**

- Must be a list of objects. An object, a list of numbers and so on are rejected with a clear error.
- Read as UTF-8, so Arabic and other non-Latin text works.
- JSON has no date type, so dates are strings (`"2024-02-10"`). The [`date__*` filter rules](#dates) understand both forms.

`employees.json`:

```json
[
  {
    "name": "Abdullah",
    "department": "Sales",
    "city": "Homs",
    "salary": 1200,
    "hired": "2021-04-01",
    "email": "abdullah@example.com"
  }
]
```

## Templates

### Supported formats

The writer is chosen from the **template extension**, ignoring case. The output file gets the same extension.

| Extension                     | Writer       | Engine                                           |
| ----------------------------- | ------------ | ------------------------------------------------ |
| `.docx`                       | `DocxWriter` | [docxtpl](https://docxtpl.readthedocs.io/) (Jinja2 inside Word) |
| `.txt`, `.md`, `.html`, `.htm` | `TextWriter` | [Jinja2](https://jinja.palletsprojects.com/)    |
| `.json`                       | `JsonWriter` | Jinja2 + validates that the output is JSON       |

Any other extension is rejected, and the error lists the supported ones.

### Jinja2 in 60 seconds

All templates use [Jinja2](https://jinja.palletsprojects.com/en/stable/templates/) syntax:

| Syntax                                     | Meaning                                  |
| ------------------------------------------ | ---------------------------------------- |
| `{{ name }}`                               | Print a variable                         |
| `{{ e.name }}` or `{{ e["name"] }}`        | Print a field of a row                   |
| `{% for e in data %} ... {% endfor %}`     | Loop                                     |
| `{{ loop.index }}`                         | 1-based loop counter                     |
| `{% if salary > 1400 %} ... {% endif %}`   | Condition                                |
| `{{ name \| upper }}`                      | Filter: `upper`, `lower`, `title`, `length`, `sum`, `default`, `tojson`, ... |
| `{{ email or "no email" }}`                | Fallback for empty values                |
| `{{ hired.strftime("%d/%m/%Y") }}`         | Format an Excel date                     |
| `{{ "{:,.2f}".format(salary) }}`           | Format a number: `1,200.00`              |
| `{# comment #}`                            | Comment, not rendered                    |
| `{%- ... -%}`                              | Trim the whitespace around a tag         |
| `{% include "header.txt" %}`               | Include another file from the template's folder (text formats) |

A variable that doesn't exist renders as an empty string instead of failing.

### Built-in variables

These are always available, in both modes:

| Variable         | Value  | In `.docx` it becomes |
| ---------------- | ------ | --------------------- |
| `{{ new_line }}` | `\n`   | a line break          |
| `{{ tab }}`      | `\t`   | a tab                 |
| `{{ page_break }}` | `\f` | a page break          |

> If your data has a column with one of these names, the built-in value wins.

### Word (`.docx`) templates

Write Jinja2 tags directly in the Word document. Keep each tag in the **same formatting** (don't bold half of `{{ name }}`), otherwise Word splits it into pieces and Jinja can't read it.

`offer.docx`:

```text
Dear {{ name }},
Welcome to the {{ department }} team in {{ city }}. Your salary is {{ salary }}$.
```

docxtpl adds special tags for Word structure:

| Tag                                 | Use                                                     |
| ----------------------------------- | ------------------------------------------------------- |
| `{%p for e in data %}` ... `{%p endfor %}` | Loop over **paragraphs**: each tag sits on its own paragraph |
| `{%tr for e in data %}` ... `{%tr endfor %}` | Loop over **table rows**: one row per record          |
| `{%tc ... %}`                       | Loop over table cells                                   |
| `{%r ... %}`                        | Tag applied to a run                                    |

**One Word file, one page per employee** (`all-offers.docx`, three paragraphs):

```text
{%p for e in data %}
{{ e.name }} - {{ e.department }}{{ page_break }}
{%p endfor %}
```

```bash
templify s -t all-offers.docx -d employees.xlsx -o offers
```

**A Word table with one row per employee**: create a 2-row table. Put `{%tr for e in data %}` and `{%tr endfor %}` in rows of their own, around a row containing `{{ e.name }}`, `{{ e.salary }}`, ...

See the [docxtpl documentation](https://docxtpl.readthedocs.io/) for images, rich text and more.

### JSON templates

A `.json` template is rendered like text, then **validated**. If the result isn't valid JSON, nothing is saved and you get an error that points at the problem.

Always write values through the `tojson` filter. It adds quotes and escapes characters like `"` for you, and turns `None` into `null` and `True` into `true`.

`profile.json`:

```jinja
{
  "name": {{ name | tojson }},
  "department": {{ department | tojson }},
  "email": {{ email | tojson }},
  "senior": {{ (salary > 1400) | tojson }}
}
```

```bash
templify m -t profile.json -d employees.json -o profiles -k name
```

`profiles/Omar.json`:

```json
{
  "name": "Omar",
  "department": "Sales",
  "email": null,
  "senior": false
}
```

Dump the whole (ordered / filtered / grouped) dataset:

```jinja
{{ data | tojson(indent=2) }}
```

```bash
templify s -t all.json -d employees.xlsx -o export -f employees --order name
```

> `tojson` sorts object keys alphabetically.

**Why use `tojson`?** With `"name": "{{ name }}"`, a name like `Ra"ma` produces broken JSON:

```text
Invalid value: Template Error: Rendered output is not valid JSON: Expecting ',' delimiter: line 1 column 14 (char 13)
```

### HTML templates

`department.html`:

```jinja
<!DOCTYPE html>
<html>
<body>
  <h1>{{ department }} department</h1>
  <ul>
  {%- for e in items %}
    <li>{{ e.name }} ({{ e.city }})</li>
  {%- endfor %}
  </ul>
  <p>{{ items | length }} employees</p>
</body>
</html>
```

```bash
templify m -t department.html -d employees.xlsx -o departments --group-by department -k department
```

> Values are **not** HTML-escaped, so `<b>` in your data stays bold. If the data isn't trusted, escape it with `{{ value | e }}`.

## Output files

| Situation                                   | Result                                              |
| ------------------------------------------- | --------------------------------------------------- |
| No `-k`                                     | `template-1.txt`, `template-2.txt`, ...             |
| `-k name`                                   | `Rama.txt`                                          |
| `-k name -i`                                | `3 - Rama.txt`                                      |
| The `-k` column is empty or missing for a row | That row falls back to `template-<n>.txt`         |
| The value has invalid characters: `a/b:c?`  | They become `_`: `a_b_c_.txt`                       |
| The value is a number: `-k id`              | `42.txt`                                            |
| The file already exists                     | A short random suffix is added: `Rama-3f9a1c2e.txt`. **Nothing is ever overwritten** |
| The output folder doesn't exist             | It is created, including parent folders             |
| `single-template` without `-f`              | Named after the template: `team.md` → `team.md`     |

Output files are written as **UTF-8**, with the template's line endings kept as they are.

## Ordering

`--order <column>` sorts ascending, and `--order -<column>` sorts descending. Repeat it to sort by several columns. The first one has the highest priority.

```bash
# highest salary first
templify s -t names.txt -d employees.xlsx -o out --order -salary

# by department A→Z, then by salary high→low inside each department
templify s -t names.txt -d employees.xlsx -o out --order department --order -salary
```

```text
Rawaa Rama Abdullah Omar
```

Ordering by a column that doesn't exist fails with the list of available columns.

## Filtering

`--filter` takes a JSON string that describes which rows to **keep**.

> **Quoting on the command line**
>
> - **bash / zsh / PowerShell 7.3+**: wrap the JSON in single quotes: `--filter '{"name": ...}'`
> - **cmd.exe**: escape the inner quotes: `--filter "{\"name\": ...}"`

### Filter schema

**A single rule** (a *predicate*) has exactly four keys:

```json
{
  "name": "string__eq",
  "args": ["department", "IT"],
  "kwargs": {},
  "inverse": false
}
```

| Key       | Meaning                                                                             |
| --------- | ----------------------------------------------------------------------------------- |
| `name`    | Rule name, see the [rules reference](#filter-rules-reference)                       |
| `args`    | Positional arguments: **the column first**, then the value(s)                       |
| `kwargs`  | The same arguments by name, e.g. `{"key": "salary", "value": 1400}`. Use `{}` otherwise |
| `inverse` | `true` negates the rule: "NOT equal", "does NOT contain", ...                       |

```bash
# IT only
templify s -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": false}'
# → Rawaa Rama

# everyone except IT
templify s -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": true}'
# → Abdullah Omar

# same rule, arguments by name
templify s -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "int__gt", "args": [], "kwargs": {"key": "salary", "value": 1400}, "inverse": false}'
# → Rawaa Rama
```

**Combine rules** with an *expression*: exactly two keys, `operator` and `expressions`.

| `operator` | Keeps a row when                  |
| ---------- | --------------------------------- |
| `all`      | **every** expression matches (AND) |
| `any`      | **at least one** matches (OR)      |

```bash
# in Homs AND earning at least 1300
templify s -t names.txt -d employees.xlsx -o out --filter '{
  "operator": "all",
  "expressions": [
    {"name": "string__eq", "args": ["city", "Homs"], "kwargs": {}, "inverse": false},
    {"name": "int__ge", "args": ["salary", 1300], "kwargs": {}, "inverse": false}
  ]
}'
# → Rama

# in Aleppo OR earning more than 1700
templify s -t names.txt -d employees.xlsx -o out --filter '{
  "operator": "any",
  "expressions": [
    {"name": "string__eq", "args": ["city", "Aleppo"], "kwargs": {}, "inverse": false},
    {"name": "int__gt", "args": ["salary", 1700], "kwargs": {}, "inverse": false}
  ]
}'
# → Rawaa Omar
```

Expressions **nest** to any depth:

```bash
# IT AND (in Damascus OR hired since 2024)
templify s -t names.txt -d employees.xlsx -o out --filter '{
  "operator": "all",
  "expressions": [
    {"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": false},
    {
      "operator": "any",
      "expressions": [
        {"name": "string__eq", "args": ["city", "Damascus"], "kwargs": {}, "inverse": false},
        {"name": "date__ge", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}
      ]
    }
  ]
}'
# → Rawaa Rama
```

> **Empty cells**: a comparison rule on an empty cell (e.g. `string__endswith` on a missing email) stops with
> `Filter failed on a data value (empty cell or wrong type?)`. Skip empty cells first by adding
> `{"name": "is_null", "args": ["email"], "kwargs": {}, "inverse": true}` to an `all` expression.

### Filter rules reference

The first argument is always the **column**. `value` is converted to the rule's type, so `"5"` works for `int__eq`.

#### Boolean & null

| Rule      | Arguments  | Keeps rows where           |
| --------- | ---------- | -------------------------- |
| `is_true` | `[column]` | the value is `true`        |
| `is_null` | `[column]` | the value is empty / `null` |

#### Numbers: `int__*`, `float__*`, `decimal__*`

| Suffix | Arguments         | Keeps rows where |
| ------ | ----------------- | ---------------- |
| `eq`   | `[column, value]` | `column == value` |
| `gt`   | `[column, value]` | `column > value`  |
| `ge`   | `[column, value]` | `column >= value` |
| `lt`   | `[column, value]` | `column < value`  |
| `le`   | `[column, value]` | `column <= value` |

For example: `int__ge`, `float__lt` and `decimal__eq`. For `decimal__*`, the value can be a string (`"10.50"`), an integer, or a float rounded to 2 decimals.

#### Strings: `string__*`

| Rule                  | Arguments          | Keeps rows where                         |
| --------------------- | ------------------ | ---------------------------------------- |
| `string__eq`          | `[column, text]`   | equals `text`                            |
| `string__contains`    | `[column, text]`   | contains `text`                          |
| `string__icontains`   | `[column, text]`   | contains `text`, ignoring case           |
| `string__startswith`  | `[column, text]`   | starts with `text`                       |
| `string__istartswith` | `[column, text]`   | starts with `text`, ignoring case        |
| `string__endswith`    | `[column, text]`   | ends with `text`                         |
| `string__iendswith`   | `[column, text]`   | ends with `text`, ignoring case          |
| `string__is_in`       | `[column, [a, b]]` | is one of the list                       |
| `string__iis_in`      | `[column, [a, b]]` | is one of the list, ignoring case        |
| `string__regex`       | `[column, pattern]` | matches the [regular expression](https://docs.python.org/3/library/re.html) |
| `string__length_eq`   | `[column, n]`      | length `== n` (also `_gt`, `_ge`, `_lt`, `_le`) |

```bash
# lives in Homs or Aleppo
--filter '{"name": "string__is_in", "args": ["city", ["Homs", "Aleppo"]], "kwargs": {}, "inverse": false}'
# → Abdullah Rama Omar

# name starts with "Ra"
--filter '{"name": "string__regex", "args": ["name", "^Ra"], "kwargs": {}, "inverse": false}'
# → Rawaa Rama
```

#### Dates: `date__*` <a id="dates"></a>

`date__eq`, `date__gt`, `date__ge`, `date__lt`, `date__le`, with arguments `[column, "YYYY-MM-DD"]`.

They compare the **day only** and accept every form a date comes in:

- Excel date cells, where the time part is ignored
- ISO strings from JSON: `"2024-02-10"` or `"2024-02-10T08:30:00"`

```bash
# hired in 2024 or later (Excel dates)
templify s -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "date__ge", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}'
# → Rama Omar

# hired before 2024 (JSON string dates)
templify s -t names.txt -d employees.json -o out \
  --filter '{"name": "date__lt", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}'
# → Abdullah Rawaa

# hired during 2024: combine two rules
--filter '{"operator": "all", "expressions": [
  {"name": "date__ge", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false},
  {"name": "date__le", "args": ["hired", "2024-12-31"], "kwargs": {}, "inverse": false}
]}'
```

#### Datetimes: `datetime__*`

`datetime__eq`, `datetime__gt`, `datetime__ge`, `datetime__lt`, `datetime__le`, with arguments `[column, "YYYY-MM-DDTHH:MM:SS"]`. They compare down to the second. The column must hold real datetimes, i.e. Excel date cells. For JSON string dates, use `date__*`.

#### UUIDs: `uuid__*`

`uuid__eq`, `uuid__gt`, `uuid__ge`, `uuid__lt`, `uuid__le`, with arguments `[column, "uuid-string"]`.

## Grouping

`--group-by <column>` merges rows that share the same value into **one group**. Each group is a new row holding:

- the group-by column(s), with the shared value
- `items` (rename it with `--group-items`), the list of the original rows in that group

```text
rows:                                  groups (--group-by department):
{name: Abdullah, department: Sales}    {department: Sales, items: [Abdullah, Omar]}
{name: Rawaa,    department: IT}   ──► {department: IT,    items: [Rawaa, Rama]}
{name: Rama,     department: IT}
{name: Omar,     department: Sales}
```

Groups appear in the order their first row appears. Grouping runs **after** ordering and filtering, so `--order` also sorts the rows inside every group, and `--filter` decides which rows get grouped.

**One file per group**, with `multiple-templates`: `-k` can name files after the group column.

```bash
templify m -t department.html -d employees.xlsx -o departments --group-by department -k department
```

```text
departments/
├── Sales.html
└── IT.html
```

**One report of all groups**, with `single-template`: loop over groups, then over each group's rows.

`by-city.txt`:

```jinja
{% for group in data -%}
{{ group.city }} / {{ group.department }}:
{%- for e in group.people %} {{ e.name }}{% endfor %}
{% endfor %}
```

```bash
templify s -t by-city.txt -d employees.xlsx -o out \
  --order city --group-by city --group-by department --group-items people
```

```text
Aleppo / Sales: Omar
Damascus / IT: Rawaa
Homs / Sales: Abdullah
Homs / IT: Rama
```

Useful group-level expressions:

```jinja
{{ items | length }}                        {# rows in the group #}
{{ items | sum(attribute="salary") }}       {# total of a column #}
{{ items | map(attribute="name") | join(", ") }}   {# "Rawaa, Rama" #}
{{ (items | sum(attribute="salary")) / (items | length) }}   {# average #}
```

**Grouping errors**

| Problem                                                  | Message                                             |
| -------------------------------------------------------- | --------------------------------------------------- |
| The column doesn't exist                                 | `Key 'country' not found in data, Available keys: ...` |
| `--group-items` equals a group-by column                 | `Items key 'city' can not be one of the group by keys` |
| The column holds lists or objects (JSON)                 | `Can not group by unhashable values ...`            |

## Cookbook

**Offer letters in Word, one per employee, numbered:**

```bash
templify m -t offer.docx -d employees.xlsx -o offers -k name -i
```

**Only employees hired this year, newest first:**

```bash
templify m -t offer.docx -d employees.xlsx -o new-hires -k name --order -hired \
  --filter '{"name": "date__ge", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}'
```

**Emails only for people who have an email address:**

```bash
templify m -t email.txt -d employees.xlsx -o emails -k email \
  --filter '{"name": "is_null", "args": ["email"], "kwargs": {}, "inverse": true}'
```

**A Markdown salary report per department:**

`department.md`:

```jinja
# {{ department }}

{% for e in items -%}
- {{ e.name }}: {{ e.salary }}
{% endfor %}
Total: {{ items | sum(attribute="salary") }}
```

```bash
templify m -t department.md -d employees.xlsx -o reports -k department --group-by department --order -salary
```

**Convert Excel to JSON:**

```bash
templify s -t all.json -d employees.xlsx -o export -f employees
```

with `all.json` containing `{{ data | tojson(indent=2) }}`.

**One JSON file per record, for an API import:**

```bash
templify m -t profile.json -d employees.xlsx -o api -k email
```

**A single printable Word file, one page per employee:**

```bash
templify s -t all-offers.docx -d employees.xlsx -o print --order name
```

**Name files with two columns**: templify names files from one column, so add a combined column to your data (an Excel formula like `=A2&" - "&B2` works once the file is saved in Excel), then use `-k full_title`.

## Errors

templify reports problems as short messages and exits with code `2`:

| Problem                                          | Example message                                                        |
| ------------------------------------------------ | ---------------------------------------------------------------------- |
| Unsupported template extension                   | `Template extension 'pdf' is not supported, supported: docx, htm, ...` |
| Unsupported data extension                       | `Extension csv is not supported`                                       |
| File doesn't exist / is a folder                 | `File '...' does not exist.`                                           |
| Jinja syntax error in the template               | `Template Error: unexpected '}'`                                       |
| Corrupted `.docx` template                       | `Could not load template 't.docx': ...`                                |
| Corrupted `.xlsx` / JSON not a list of objects   | `Could not read data file 'data.json': JSON data must be a list of objects` |
| JSON template rendered invalid JSON              | `Template Error: Rendered output is not valid JSON: ...`               |
| `--order` / `--group-by` column doesn't exist    | `Key 'salary' not found in data, Available keys: name, age`            |
| `--filter` isn't valid JSON                      | `Expecting property name enclosed in double quotes: ...`               |
| Unknown filter rule                              | `Rule 'nope' does not exist. Available rules: is_true, is_null, ...`   |
| Invalid value for a rule                         | `Argument 'value' with value 'soon' failed to process, ...`            |
| Filter hit an empty cell or wrong type           | `Filter failed on a data value (empty cell or wrong type?): ...`       |

## Extending templify

Each extension point is a registry filled with a decorator. Add your code, and the CLI picks it up automatically, including `--help` and the error messages.

### A new data source

`src/templify/readers.py`: a function that takes a path and returns a list of dicts.

```python
import csv


@readers.reader("csv")
def read_csv(filepath: Path) -> Data:
    with filepath.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
```

### A new template format

`src/templify/writers.py`: a class built from the template path that implements the `Writer` protocol, i.e. a `write(context, filepath)` method.

```python
class Writer(Protocol):
    def write(self, context: Context, filepath: Path) -> None: ...
```

Text-based formats can simply be added to `TextWriter`:

```python
@writers.writer("txt", "md", "html", "htm", "xml", "csv")
class TextWriter: ...
```

A format with its own engine gets its own class:

```python
@writers.writer("pptx")
class PptxWriter:
    def __init__(self, template_path: Path) -> None:
        self.template_path = template_path

    def write(self, context: Context, filepath: Path) -> None:
        ...  # render context into the template and save to filepath
```

A format that needs validation can extend `TextWriter` and override `render`, the way `JsonWriter` does.

### A new filter rule

`src/templify/filter_rules.py`: the first two parameters are the row and the column. `processors` converts the values coming from the filter JSON.

```python
@rules.rule(processors=float)
def float__between(d: dict[str, Any], key: str, low: float, high: float) -> bool:
    return low <= d[key] <= high
```

```bash
--filter '{"name": "float__between", "args": ["salary", 1200, 1600], "kwargs": {}, "inverse": false}'
```

## Development

```bash
uv sync
```

Run the tests. Coverage (lines and branches) is printed after every run:

```bash
uv run pytest
```

Lint and format:

```bash
uvx ruff check src tests
```

```bash
uvx ruff format src tests
```

### Project structure

```text
src/templify/
├── models.py            # Data / DataItem types
├── readers.py           # data sources: ReaderRegistry, read_excel, read_json
├── writers.py           # Writer protocol, WriterRegistry, Docx/Text/Json writers,
│                        #   write_single / write_multiple, file naming
├── transformers.py      # order_by_data, filter_data, group_by_data
├── filter_rules.py      # every --filter rule
└── cli/
    ├── main.py          # the commands
    ├── help.py          # long --help texts
    └── dependencies/
        ├── data.py      # -d, --order, --filter, --group-by pipeline
        ├── template.py  # -t (picks the writer) and -o
        └── console.py   # rich console
tests/
├── test_readers.py
├── test_writers.py
├── test_transformers.py
├── test_filter_rules.py
└── test_cli.py          # end-to-end user scenarios
```

## License

templify is free software, released under the [GNU General Public License v3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html) (see `LICENSE`).
