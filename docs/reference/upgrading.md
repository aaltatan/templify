# Upgrading

## From 0.6 to 0.7

0.7 renders every template in Jinja's **immutable sandbox**, with the
[jinja-types](types.md) filters added:

| 0.6 | 0.7 |
|-----|-----|
| `{{ items.append(x) }}` changes `items` | Fails: `access to attribute 'append' of 'list' object is unsafe` |
| | Build a new list instead: `{% set more = items + [x] %}` or `{{ items \| list.append(x) }}` |
| Unknown filter: `No filter named 'str.zfil'.` | Adds `Did you mean: str.zfill?` |
| | New `templify types` (`t`) command |

## From 0.2 to 0.3

| 0.2 | 0.3 and later |
|-----|---------------|
| `templify single-template` / `s` | `templify render` |
| `templify multiple-templates` / `m` | `templify render --each` |
| `templify schema-template` / `js` | `templify render --object -s ...` |
| `templify schema-list-template` / `jsl` | `templify render -s ...` |
| `templify filters-json-schema` / `fjs` | `templify filters` |
| `-k` / `--filename-key` | `-n` / `--name-by` |
| `-i` / `--index` | `--numbered` |
| `--group-items` | `--items-var` |
| `-v` / `--data-variable`, default `data` | `-v` / `--var`, default `objects` |
| `-o` required | `-o` optional, default current folder |
| Template errors exit with code 2 | Exit with code 1 (usage errors stay 2) |
