# Errors and exit codes

| Exit | Meaning |
|------|---------|
| `0` | Success |
| `1` | A template failed **while rendering** a row, or a store could not be read or written |
| `2` | Bad input: options, data, filters, or a template that cannot be loaded (syntax error, unknown filter) |

Errors are short messages, not Python tracebacks. With `--each`, files already written
for earlier rows stay on disk when a later row fails.

## Command line

| Message | Fix |
|---------|-----|
| `Give exactly one data source: -d / --data or -s / --schema` | Use one of them |
| `--name-by only works with --each` (and `--numbered`) | Add `--each`, or drop the option |
| `--filename does not work with --each` (and `--var`) | Use `-n` to name the files |
| `--each and --object can not be used together` | Pick one mode |
| `--order, --filter and --group-by do not work with --object` | There is only one record |
| `--store only works with -s / --schema` | Stores hold typed-in records; use `store import` for files |
| `--id needs --store` | Add `--store PATH` |
| `--object takes exactly one --id` | One record, one id |
| `Invalid value for '-t' / '--template': file 'nope.txt' does not exist.` | Check the path |

## Templates

| Message | Exit | Fix |
|---------|------|-----|
| `Template extension 'pdf' is not supported, supported: docx, htm, html, json, md, txt` | 2 | Use a supported format |
| `Template Error: unexpected '}'` | 2 | A Jinja syntax error: check the `{{ }}` and `{% %}` pairs |
| `Template Error: No filter named 'str.zfil'. Did you mean: str.zfill, str.find, str.title?` | 2 | Fix the name; `templify types` lists them all |
| `Could not load template 't.docx': File is not a zip file` | 2 | The `.docx` is damaged, or not really a Word file |
| `Template Error: access to attribute 'append' of 'list' object is unsafe.` | 1 | The sandbox blocks changing data; build a new value instead ([sandbox](../guide/templates.md#the-sandbox)) |
| `Template Error: 'str object' has no attribute 'strftime'` | 1 | A JSON date is text: use `{{ hired \| to_date \| date.strftime(...) }}` |
| `Template Error: Rendered output is not valid JSON: Expecting ',' delimiter: ...` | 1 | Write values through `tojson` ([JSON templates](../guide/json.md)) |

A template that misspells a **variable** (`{{ nmae }}`) does not fail: it prints an
empty string. Check new templates once.

## Data

| Message | Fix |
|---------|-----|
| `Extension 'csv' is not supported for being a data file` | Use `.xlsx` or `.json` ([other formats](../guide/data.md#other-formats)) |
| `Could not read data file 'data.json': JSON data must be a list of objects` | A list for the default mode and `--each`, an object for `--object` |
| `Could not read data file 'x.xlsx': File is not a zip file` | The workbook is damaged, or not really `.xlsx` |
| `"Key 'salry' not found in data, Available keys: id, name, ..."` | `--order` or `--group-by` names a column that does not exist |

## Filters

| Message | Fix |
|---------|-----|
| `Expecting property name enclosed in double quotes: line 1 column 2 (char 1)` | The `--filter` JSON is broken; check the [quoting](../guide/order-filter.md#quoting-on-the-command-line) |
| `Rule 'nope' does not exist. Available rules: is_true, is_null, ...` | See [Filter rules](filter-rules.md) |
| `Argument 'value' with value 'soon' failed to process, invalid literal for int() ...` | The value does not fit the rule's type |
| `Filter failed on a data value (empty cell or wrong type?): 'NoneType' object has no attribute 'endswith'` | An empty cell: [skip it first](../guide/order-filter.md#empty-cells) |

## Grouping

| Message | Fix |
|---------|-----|
| `Key 'country' not found in data, Available keys: ...` | Check the column name |
| `Items key 'city' can not be one of the group by keys` | Give `--items-var` another name |
| `Can not group by unhashable values (like lists or objects): ...` | Group by a column of plain values |

## Stores

| Message | Exit | Fix |
|---------|------|-----|
| `Store extension 'csv' is not supported, supported: db, json, jsonl, sqlite, sqlite3, xlsx` | 2 | Use a supported extension |
| `Store Error: Store '...x.sqlite' does not exist, create it with: templify store init` | 1 | Run `store init` first |
| `No record with id 4` | 2 | Check the id with `store list` |
| `'people.json' already exists, export only creates new stores` | 2 | Export to a new file name |
| `Nothing imported, rows not matching the schema: Row 2: ...` | 2 | Fix those rows; nothing was imported |
| `Store Error: ...` and `The answers were not saved: [...]` | 1 | Close the file in Excel (or fix the cause), then add the printed answers again |

## Types

| Message | Fix |
|---------|-----|
| `No members match, namespaces: ar, date, ...` | Check `-n` and `-k` |

## Still stuck

Open an [issue](https://github.com/aaltatan/templify/issues) with the command, the
message, and a small template and data file that show the problem.
