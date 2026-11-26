---
hide:
  - navigation
---

# templify

**Fill document templates with data, from the command line.**

Point `templify` at a **template** (Word, text, Markdown, HTML or JSON) and a **data
source**: an Excel sheet, a JSON file, or a JSON Schema that templify asks you to fill
in. You get one file per row, one file with every row in it, or one file from a single
record. Before rendering you can **order**, **filter** and **group** the rows.

```bash
templify render --each -t offer.docx -d employees.xlsx -o offers -n name
```

```text
offers/
├── Abdullah.docx
├── Rawaa.docx
├── Rama.docx
└── Omar.docx
```

![templify render --each: one Word file per row](demo/each.gif)

## Why templify

<div class="grid cards" markdown>

-   :material-file-word-outline: **Five template formats**

    ---

    `.docx`, `.txt`, `.md`, `.html` and `.json`. The format comes from the template's
    extension, and every format uses the same [Jinja](https://jinja.palletsprojects.com)
    syntax.

-   :material-table-arrow-right: **Excel, JSON, or typed in**

    ---

    Read the active sheet of a workbook, a JSON list, or answer questions built from a
    JSON Schema.

-   :material-filter-outline: **Order, filter, group**

    ---

    Sort by any columns, keep rows with 47 filter rules, and group rows into one file per
    department, city or customer.

-   :material-database-outline: **Record stores**

    ---

    Keep typed-in records in SQLite, Excel, JSON or JSON Lines. List, search, fix and
    re-render them by id.

-   :material-translate: **Type filters, Arabic included**

    ---

    `str.zfill`, `decimal.quantize`, `date.strftime`, and Arabic number words
    (`ar.to_words`), dates and digits in every template.

-   :material-shield-check-outline: **Safe by default**

    ---

    Nothing is ever overwritten, templates run in Jinja's sandbox, and a JSON template
    that renders broken JSON is rejected.

</div>

## A taste

=== "One file per row"

    ```bash
    # Word offer letters, numbered: 1 - Abdullah.docx, 2 - Rawaa.docx, ...
    templify render --each -t offer.docx -d employees.xlsx -o offers -n name --numbered
    ```

=== "All rows in one file"

    ```bash
    # a Markdown table of the whole team, highest salary first
    templify render -t team.md -d employees.xlsx -o reports --order -salary
    ```

=== "One file per group"

    ```bash
    # one HTML page per department
    templify render --each -t department.html -d employees.xlsx -o departments --group-by department -n department
    ```

=== "One record"

    ```bash
    # a certificate for one person
    templify render --object -t certificate.docx -d rama.json -o certificates
    ```

## Where to go next

- New here? [Install it](install.md), then follow the [user guide](guide/index.md),
  starting with [your first files](guide/first-files.md).
- Have a job to do? See the [recipes](recipes.md): offer letters, mail-merge emails,
  department reports, Arabic salary certificates, Excel to JSON, and more.
- Looking up an option? The [reference](reference/index.md) lists every command,
  option, filter rule, type filter and error.
