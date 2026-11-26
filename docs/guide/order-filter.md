# Order and filter

`--order` sorts the rows and `--filter` keeps only some of them. They run before
grouping and rendering: **order → filter → group → render**. Neither works with
`--object`, which has only one record.

`names.txt`, used on this page, prints every name on one line:

```jinja
{% for e in objects %}{{ e.name }}{% if not loop.last %} {% endif %}{% endfor %}
```

## Order

`--order <column>` sorts ascending, and `--order -<column>` descending. Repeat it to
sort by several columns. The first one has the highest priority.

```bash
# highest salary first
templify render -t names.txt -d employees.xlsx -o out --order -salary

# by department A→Z, then by salary high→low inside each department
templify render -t names.txt -d employees.xlsx -o out --order department --order -salary
```

```text
Rawaa Rama Abdullah Omar
```

The order decides the order of rows in a report, and the numbering of `--each --numbered`
files. A column that does not exist is reported with the ones that do:

```text
Invalid value: "Key 'salry' not found in data, Available keys: id, name, department, city, salary, hired, email"
```

## Filter

`--filter` takes a small JSON document that says which rows to **keep**. One rule:

```json
{"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": false}
```

| Key | Meaning |
|-----|---------|
| `name` | The rule, see [Filter rules](../reference/filter-rules.md) or `templify filters` |
| `args` | Positional arguments: **the column first**, then the value(s) |
| `kwargs` | The same arguments by name, e.g. `{"key": "salary", "value": 1400}`; `{}` otherwise |
| `inverse` | `true` keeps the rows that do **not** match |

All four keys are required.

```bash
# IT only
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": false}'
# → Rawaa Rama

# everyone except IT
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": true}'
# → Abdullah Omar

# the same rule, arguments by name
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "int__gt", "args": [], "kwargs": {"key": "salary", "value": 1400}, "inverse": false}'
# → Rawaa Rama
```

Values are converted to the rule's type, so `"1400"` and `1400` both work for
`int__gt`.

### More rules

```bash
# lives in Homs or Aleppo
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "string__is_in", "args": ["city", ["Homs", "Aleppo"]], "kwargs": {}, "inverse": false}'
# → Abdullah Rama Omar

# name starts with "Ra"
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "string__regex", "args": ["name", "^Ra"], "kwargs": {}, "inverse": false}'
# → Rawaa Rama

# has an email address
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "is_null", "args": ["email"], "kwargs": {}, "inverse": true}'
# → Abdullah Rawaa Rama
```

### Dates

`date__eq`, `date__gt`, `date__ge`, `date__lt` and `date__le` take
`[column, "YYYY-MM-DD"]`. They compare the **day only**, and accept Excel date cells as
well as ISO strings from JSON (`"2024-02-10"` or `"2024-02-10T08:30:00"`):

```bash
# hired in 2024 or later (Excel dates)
templify render -t names.txt -d employees.xlsx -o out \
  --filter '{"name": "date__ge", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}'
# → Rama Omar

# hired before 2024 (JSON string dates)
templify render -t names.txt -d employees.json -o out \
  --filter '{"name": "date__lt", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}'
# → Abdullah Rawaa
```

`datetime__*` rules compare down to the second, and need real datetimes (Excel date
cells). For JSON string dates, use `date__*`.

## Combining rules

Wrap rules in an expression with `operator` and `expressions`:

| `operator` | Keeps a row when |
|------------|------------------|
| `all` | **every** expression matches (AND) |
| `any` | **at least one** matches (OR) |

```bash
# in Homs AND earning at least 1300
templify render -t names.txt -d employees.xlsx -o out --filter '{
  "operator": "all",
  "expressions": [
    {"name": "string__eq", "args": ["city", "Homs"], "kwargs": {}, "inverse": false},
    {"name": "int__ge", "args": ["salary", 1300], "kwargs": {}, "inverse": false}
  ]
}'
# → Rama

# in Aleppo OR earning more than 1700
templify render -t names.txt -d employees.xlsx -o out --filter '{
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
templify render -t names.txt -d employees.xlsx -o out --filter '{
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

## Empty cells

A comparison on an empty cell (for example `string__endswith` on Omar's missing email)
stops the run:

```text
Invalid value: Filter failed on a data value (empty cell or wrong type?): ...
```

Skip empty cells first, with `is_null` inverted, inside an `all`:

```bash
templify render -t names.txt -d employees.xlsx -o out --filter '{
  "operator": "all",
  "expressions": [
    {"name": "is_null", "args": ["email"], "kwargs": {}, "inverse": true},
    {"name": "string__endswith", "args": ["email", "@example.com"], "kwargs": {}, "inverse": false}
  ]
}'
```

## Quoting on the command line

| Shell | Write |
|-------|-------|
| bash, zsh, PowerShell 7.3+ | Single quotes around the JSON: `--filter '{"name": ...}'` |
| Windows PowerShell 5 | Put the JSON in a file: `--filter (Get-Content it.filter.json -Raw)` |
| cmd.exe | Double quotes, inner quotes escaped: `--filter "{\"name\": ...}"` |

Long filters are easier to keep in a file:

=== "bash"

    ```text
    templify render -t names.txt -d employees.xlsx --filter "$(cat it.filter.json)"
    ```

=== "PowerShell"

    ```powershell
    templify render -t names.txt -d employees.xlsx --filter (Get-Content it.filter.json -Raw)
    ```
