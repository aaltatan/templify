# Commands and options

```text
templify [--help] <command> [options]
```

| Command | Alias | Does |
|---------|-------|------|
| [`render`](#render) | `r` | Render a template with data, in one of three modes |
| [`filters`](#filters) | `f` | List the filter rules and their arguments |
| [`types`](#types) | `t` | List the jinja-types template filters and tests |
| [`store`](#store) | `s` | Keep records in a store file |

| Global option | Meaning |
|---------------|---------|
| `--install-completion` | Install tab completion for the current shell |
| `--show-completion` | Print the completion script, to install it yourself |
| `--help` | Show help. Works after every command too: `templify render --help` |

## `render`

```text
templify render -t <template> (-d <data> | -s <schema.json>) [--each | --object] [options] [--<variable> <value> ...]
```

### Mode

| Option | Meaning |
|--------|---------|
| *(neither)* | All rows in one file; the template loops over `objects` |
| `--each` | One file per row (or per group); each row's columns are the variables |
| `--object` | The data is a single record, rendered into one file as `object` |

### Template and output

| Option | Default | Meaning |
|--------|---------|---------|
| `-t, --template` | required | `.docx`, `.txt`, `.md`, `.html`, `.htm` or `.json` |
| `-o, --output` | current folder | Output folder, created if missing |

### Data source (one of)

| Option | Meaning |
|--------|---------|
| `-d, --data` | A data file: `.xlsx` or `.json` (a list, or an object with `--object`) |
| `-s, --schema` | A JSON Schema: ask for the data matching it |

### Data options (default and `--each`)

| Option | Default | Meaning |
|--------|---------|---------|
| `--order` | | Column to order by, `-column` for descending. Repeatable. |
| `--filter` | | A [filter](filter-rules.md) as JSON |
| `--group-by` | | Column to group by. Repeatable. |
| `--items-var` | `items` | The variable holding each group's rows |

### Output (default and `--object`)

| Option | Default | Meaning |
|--------|---------|---------|
| `-f, --filename` | the template's name | Output file name, without extension |
| `-v, --var` | `objects`, or `object` with `--object` | The variable holding the data |

### Output (`--each`)

| Option | Default | Meaning |
|--------|---------|---------|
| `-n, --name-by` | `template-<n>` | The column naming each file |
| `--numbered` | off | Prefix each file name with its row number: `1 - Rama` |

### Store

| Option | Meaning |
|--------|---------|
| `--store PATH` | Save the answers to `-s` in this store before rendering, or read `--id` from it |
| `--id ID` | Render these stored records instead of asking. Repeatable; exactly one with `--object`. |

### Template variables

Any other `--key value` or `--key=value` becomes a template variable, `{{ key }}`.
Dashes become underscores, and values are strings.

### Which options go together

Options the chosen mode does not use are **refused**, not ignored:

| Option | Only with |
|--------|-----------|
| `--each` | not with `--object` |
| `-n, --name-by`, `--numbered` | `--each` |
| `-f, --filename`, `-v, --var` | default mode, `--object` |
| `--order`, `--filter`, `--group-by` | default mode, `--each` |
| `-d` | not with `-s` (exactly one of them) |
| `--store` | `-s` |
| `--id` | `--store` |

### Examples

```bash
templify render -t team.md -d employees.xlsx -o reports
templify r --each -t offer.docx -d employees.xlsx -o offers -n name --numbered
templify render --object -t letter.md -d rama.json -o letters
templify render -t report.md -d employees.xlsx -o reports --title "Q3 report" --company Tawazon
```

## `filters`

```text
templify filters
```

List every rule `--filter` accepts, with its arguments (in `args` order, and as
`kwargs` names) and description. The same list is on the
[Filter rules](filter-rules.md) page.

```bash
templify filters
```

## `types`

```text
templify types [-n NAMESPACE] [-k KIND]
```

List the [jinja-types](types.md) members usable in templates.

| Option | Meaning |
|--------|---------|
| `-n, --namespace` | Only this namespace: `str`, `decimal`, `date`, `ar`, ... (`helpers` for names without a prefix). Tab-completes. |
| `-k, --kind` | Only this kind: `filter`, `test`, `attribute` or `global` |

```bash
templify types -n ar
templify t -n str -k test
```

## `store`

```text
templify store <command> -s <schema.json> PATH [options]
```

Every `store` command takes the schema (`-s, --schema`) and the store file `PATH`
(`.sqlite`, `.db`, `.sqlite3`, `.xlsx`, `.json` or `.jsonl`). See
[Storing records](../guide/stores.md).

| Command | Alias | Arguments and options | Does |
|---------|-------|-----------------------|------|
| `init` | | | Create the file and its table or sheet; does nothing if they exist |
| `add` | | | Ask for records and add them; prints the new ids |
| `list` | `ls` | | Show every record |
| `get` | | `ID` | Show one record |
| `search` | | `--filter JSON` (required) | Show the records matching the filter |
| `update` | | `ID` | Ask for the whole record again and replace it |
| `delete` | `rm` | `ID`, `-y, --yes` | Delete a record; `-y` skips the confirmation |
| `migrate` | | | Add new schema properties as columns, keeping every row |
| `import` | | `-d, --data FILE` (required) | Add every row of an `.xlsx` / `.json` file, or none if one row is invalid |
| `export` | | `TARGET` | Copy every record, ids and timestamps included, into a new store file |
