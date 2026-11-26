# First files

This page takes you from nothing to text, Markdown and Word files in a few minutes.
Open a terminal in the
[`examples/`](https://github.com/aaltatan/templify/tree/main/examples) folder.

## The data

`employees.xlsx` (and the same rows in `employees.json`). The first row holds the
column names:

| id | name | department | city | salary | hired | email |
|---:|------|------------|------|-------:|-------|-------|
| 1 | Abdullah | Sales | Homs | 1200 | 2021-04-01 | abdullah@example.com |
| 2 | Rawaa | IT | Damascus | 1800 | 2023-09-15 | rawaa@example.com |
| 3 | Rama | IT | Homs | 1500 | 2024-02-10 | rama@example.com |
| 4 | Omar | Sales | Aleppo | 1100 | 2024-11-03 | |

Omar has no email: that empty cell matters in a few examples.

## The example files

| File | What it is | Used in |
|------|------------|---------|
| `employees.xlsx`, `employees.json` | The 4 rows above | everywhere |
| `rama.json` | One record (a JSON object) | [`--object`](modes.md#one-record-object) |
| `person.schema.json` | A JSON Schema to type people in | [Data sources](data.md#typing-the-data-in), [Stores](stores.md) |
| `welcome.txt` | A two-line welcome note | this page |
| `names.txt` | Every name on one line | [Order and filter](order-filter.md) |
| `team.md` | A Markdown team table with a total | [Render modes](modes.md) |
| `report.md` | A report with a title from the command line | [Templates](templates.md#variables-from-the-command-line) |
| `letter.md` | A letter for one record | [Render modes](modes.md#one-record-object) |
| `email.txt` | A welcome email | [Recipes](../recipes.md#mail-merge-emails) |
| `department.html`, `department.md` | One page per department | [Grouping](grouping.md) |
| `by-city.txt` | A report of groups | [Grouping](grouping.md) |
| `profile.json`, `all.json`, `export.json` | JSON output | [JSON templates](json.md), [Excel to JSON](../recipes.md#excel-to-json) |
| `offer.docx` | A Word offer letter | [Word](word.md) |
| `all-offers.docx` | Every person in one Word file, one page each | [Word](word.md#all-rows-in-one-document) |
| `staff-table.docx` | A Word table, one row per person | [Word](word.md#a-table-row-per-record) |
| `certificate.docx` | A certificate for one record | [Word](word.md), [Stores](stores.md) |
| `salary-certificate.md` | An Arabic salary certificate | [Type filters](type-filters.md#arabic) |

## A text file per person

`welcome.txt`:

```jinja
Hello {{ name }},
You joined {{ department }} on {{ hired.strftime("%d/%m/%Y") }}.
```

The column names are the variables. Render one file per row:

```bash
templify render --each -t welcome.txt -d employees.xlsx -o welcome -n name
```

```text
4 files generated successfully in: .../examples/welcome
```

`welcome/Rama.txt`:

```text
Hello Rama,
You joined IT on 10/02/2024.
```

- `--each` writes one file per row.
- `-o welcome` is the output folder. It is created if it does not exist.
- `-n name` names each file after the `name` column: `Rama.txt`.

## One Markdown report of everyone

`team.md` loops over all the rows, which are in the variable `objects`:

```jinja
# Team report

| # | Name | Department | Salary |
|---|------|------------|-------:|
{% for e in objects -%}
| {{ loop.index }} | {{ e.name }} | {{ e.department }} | {{ "{:,}".format(e.salary) }} |
{% endfor %}
**Total salaries:** {{ objects | sum(attribute="salary") }}
```

Without `--each`, templify writes **one** file:

```bash
templify render -t team.md -d employees.xlsx -o reports --order -salary
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

`--order -salary` sorts by salary, highest first.

## Word letters

`offer.docx` is a normal Word document with Jinja tags typed into it:

```text
Job offer

Dear {{ name }},

We are happy to welcome you to the {{ department }} team in our {{ city }} office.
Your monthly salary is {{ "{:,}".format(salary) }} USD, starting on
{{ hired | date.strftime("%d %B %Y") }}.
```

```bash
templify render --each -t offer.docx -d employees.xlsx -o offers -n name --numbered
```

```text
offers/
├── 1 - Abdullah.docx
├── 2 - Rawaa.docx
├── 3 - Rama.docx
└── 4 - Omar.docx
```

`--numbered` adds the row number in front, so the files stay in data order.

## Running it twice

Run the first command again, and templify does **not** overwrite anything: the new
files get a short random suffix, like `Rama-3f9a1c2e.txt`. See
[Output files](output.md).

## Next

Learn the three [render modes](modes.md).
