# User guide

This guide walks through templify one feature at a time. Each page builds on the
previous one, but you can jump straight to the page you need.

| Page | You will learn |
|------|----------------|
| [First files](first-files.md) | The example data, and your first text, Markdown and Word files |
| [Render modes](modes.md) | All rows in one file, one file per row, or one record |
| [Data sources](data.md) | Excel, JSON, and typing data in from a JSON Schema |
| [Writing templates](templates.md) | Jinja basics, built-in variables, variables from options |
| [Word (docx) templates](word.md) | Tags inside Word, loops over paragraphs and table rows |
| [Text, Markdown and HTML](text.md) | Plain text formats, includes, HTML escaping |
| [JSON templates](json.md) | `tojson`, validated output, exports for APIs |
| [Type filters](type-filters.md) | `str.zfill`, decimals, dates, Arabic words and digits |
| [Output files](output.md) | Folders, file names, numbering, never overwriting |
| [Order and filter](order-filter.md) | Sort rows and keep only some of them |
| [Grouping](grouping.md) | One file per department, or one report of all groups |
| [Storing records](stores.md) | Keep typed-in records in SQLite, Excel or JSON, and re-render them |

## How it works

`render` runs one pipeline:

```text
 read data ──► order ──► filter ──► group ──► render template ──► save file(s)
 (-d / -s)    (--order)  (--filter)  (--group-by)    (-t)              (-o)
```

1. **Read**: the [data source](data.md) becomes a list of rows, each row a set of
   `column: value` pairs.
2. **Order**: rows are sorted by the `--order` columns (optional).
3. **Filter**: rows that do not match `--filter` are dropped (optional).
4. **Group**: rows are grouped by the `--group-by` columns (optional).
5. **Render**: the writer chosen from the template's extension fills the template.
6. **Save**: one file with every row, or with `--each`, one file per row (or per group).

With `--object`, the data is a **single record** instead of a list, so steps 2 to 4 do
not apply.

## Conventions

- Commands are shown as you would type them inside the
  [`examples/`](https://github.com/aaltatan/templify/tree/main/examples) folder.
- `$` at the start of a line marks a command when its output is shown under it.
- Paths in output are shortened to `...`.
