# Writing templates

## Formats

The writer is chosen from the **template's extension**, ignoring case. The output file
gets the same extension.

| Extension | Engine | Page |
|-----------|--------|------|
| `.docx` | [docxtpl](https://docxtpl.readthedocs.io/): Jinja inside Word | [Word templates](word.md) |
| `.txt`, `.md`, `.html`, `.htm` | [Jinja](https://jinja.palletsprojects.com/) | [Text, Markdown and HTML](text.md) |
| `.json` | Jinja, then the output is checked to be valid JSON | [JSON templates](json.md) |

Any other extension is rejected, and the error lists the supported ones:

```text
Invalid value: Template extension 'pdf' is not supported, supported: docx, htm, html, json, md, txt
```

## Jinja in 60 seconds

Every format uses [Jinja](https://jinja.palletsprojects.com/en/stable/templates/):

| Syntax | Meaning |
|--------|---------|
| `{{ name }}` | Print a variable |
| `{{ e.name }}` or `{{ e["name"] }}` | Print a field of a row (use brackets for names with spaces) |
| `{% for e in objects %} ... {% endfor %}` | Loop |
| `{{ loop.index }}` | 1-based loop counter (`loop.first`, `loop.last` too) |
| `{% if salary > 1400 %} ... {% elif %} ... {% else %} ... {% endif %}` | Condition |
| `{{ name \| upper }}` | A filter: `upper`, `lower`, `title`, `length`, `sum`, `default`, `join`, `tojson`, ... |
| `{{ email or "no email" }}` | Fallback for an empty value |
| `{{ hired.strftime("%d/%m/%Y") }}` | Format an Excel date |
| `{{ "{:,.2f}".format(salary) }}` | Format a number: `1,200.00` |
| `{% set total = objects \| sum(attribute="salary") %}` | A variable inside the template |
| `{# comment #}` | Comment, not rendered |
| `{%- ... -%}` | Trim the whitespace around a tag |

**A variable that does not exist renders as an empty string** instead of failing.
That keeps templates forgiving for optional columns, but it also means a typo like
`{{ nmae }}` prints nothing. Check the output of a new template once.

## Built-in variables

These are always available, in every mode:

| Variable | Value | In `.docx` it becomes |
|----------|-------|-----------------------|
| `{{ new_line }}` | `\n` | a line break |
| `{{ tab }}` | `\t` | a tab |
| `{{ page_break }}` | `\f` | a page break |

If your data has a column with one of these names, the built-in value wins.

## Variables from the command line

Any **other** `--key value` (or `--key=value`) becomes a template variable, in every
mode. Use it for things that are the same for every row: a title, a date, a company
name.

`report.md`:

```jinja
# {{ title }}

Prepared by {{ company }} for {{ objects | length }} employees.

{% for e in objects -%}
- {{ e.name }} ({{ e.department }})
{% endfor %}
```

```bash
templify render -t report.md -d employees.xlsx -o reports --title "Q3 report" --company Tawazon
```

```markdown
# Q3 report

Prepared by Tawazon for 4 employees.

- Abdullah (Sales)
- Rawaa (IT)
- Rama (IT)
- Omar (Sales)
```

- Dashes become underscores: `--due-date 2026-12-01` gives `{{ due_date }}`.
- Values are **strings**. Convert them in the template: `{{ rate | to_decimal }}`,
  `{{ due_date | to_date }}`.
- With `--each`, a data column with the same name wins over the option. So do
  `objects` / `object` (or your `--var`) and the built-in variables.

## The sandbox

Templates render in Jinja's **immutable sandbox**. They can read data and call harmless
methods, but they cannot change lists or dicts, or reach Python internals:

```text
Template Error: access to attribute 'append' of 'list' object is unsafe.
```

Build new values instead of changing old ones:

```jinja
{% set more = items + [extra] %}
{{ items | list.append(extra) }}
```

So a template from someone else cannot read your files or run commands.

## Type filters

On top of the Jinja built-ins, every template gets the
[jinja-types](https://pypi.org/project/jinja-types/) filters: Python's own methods under
a namespace (`str.zfill`, `decimal.quantize`, `date.strftime`, `ar.to_words`, ...). See
[Type filters](type-filters.md).
