# Recipes

Complete, real-world jobs. Every template and data file used here is in
[`examples/`](https://github.com/aaltatan/templify/tree/main/examples).

## Offer letters for new hires

**Job:** a Word offer letter for everyone hired this year, newest first, numbered so
the printed stack matches the list.

```bash
templify render --each -t offer.docx -d employees.xlsx -o new-hires -n name --numbered --order -hired \
  --filter '{"name": "date__ge", "args": ["hired", "2024-01-01"], "kwargs": {}, "inverse": false}'
```

```text
new-hires/
├── 1 - Omar.docx
└── 2 - Rama.docx
```

- `--order -hired` puts the newest hire first.
- `--numbered` counts after the order and filter, so the numbers have no gaps.
- The letterhead, logo and fonts all come from `offer.docx`. Design it once in Word.

## Mail-merge emails

**Job:** a personal welcome email for each person, skipping the ones with no address.

[`email.txt`](https://github.com/aaltatan/templify/blob/main/examples/email.txt):

```jinja
To: {{ email }}
Subject: Welcome to the {{ department }} team

Dear {{ name }},

Welcome aboard! Your first day in our {{ city }} office is coming up.
Your monthly salary will be {{ "{:,.2f}".format(salary) }} USD.

Best regards,
HR
```

```bash
templify render --each -t email.txt -d employees.xlsx -o emails -n email \
  --filter '{"name": "is_null", "args": ["email"], "kwargs": {}, "inverse": true}'
```

```text
emails/
├── abdullah@example.com.txt
├── rama@example.com.txt
└── rawaa@example.com.txt
```

Each file is named after its recipient, ready to paste into a mail client or to send
from a script. Make it `email.html` for formatted emails.

## One printable file for the whole team

**Job:** everyone's page in one Word document, sorted by name, to print in one go.

```bash
templify render -t all-offers.docx -d employees.xlsx -o print --order name
```

See [All rows in one document](guide/word.md#all-rows-in-one-document).

## A staff list as a Word table

```bash
templify render -t staff-table.docx -d employees.xlsx -o print -f "IT staff" --title "IT staff" \
  --filter '{"name": "string__eq", "args": ["department", "IT"], "kwargs": {}, "inverse": false}'
```

The table gets one row per IT employee and a total under it. `--title` fills the
heading, and `-f` names the file.

## A report per department

**Job:** a Markdown salary summary for each department head, highest salary first.

```bash
templify render --each -t department.md -d employees.xlsx -o reports -n department --group-by department --order -salary
```

```text
reports/
├── IT.md
└── Sales.md
```

As HTML pages for an intranet instead:

```bash
templify render --each -t department.html -d employees.xlsx -o departments --group-by department -n department
```

## A quarterly report with a title

**Job:** the same report template every quarter, with the quarter and company passed
in on the command line.

```bash
templify render -t report.md -d employees.xlsx -o reports -f q3-2026 --title "Q3 2026 headcount" --company Tawazon
```

Every unknown `--option` becomes a template variable. See
[Variables from the command line](guide/templates.md#variables-from-the-command-line).

## Arabic salary certificates

**Job:** a شهادة راتب for each employee, with the salary written in words (تفقيط) and
the hiring date with Arabic month names.

```bash
templify render --each -t salary-certificate.md -d employees.xlsx -o certificates -n name
```

```markdown
# شهادة راتب

نشهد بأن السيد/ة **Rama** يعمل لدينا في قسم IT منذ
10 شباط 2024، وأن راتبه الشهري
1,500 دولار أمريكي (ألف وخمسمئة دولار أمريكي لا غير).
```

The same filters work in Word: put the text in a right-to-left paragraph of a `.docx`
template. See [Arabic](guide/type-filters.md#arabic).

## Certificates with a register

**Job:** HR issues employment certificates at the desk. Each one needs a unique number,
and HR must be able to reprint any certificate later.

```text
templify store init -s person.schema.json certificates.sqlite
templify render --object -s person.schema.json --store certificates.sqlite -t certificate.docx -o issued
```

templify asks for the person's details, saves them in `certificates.sqlite`, and
renders the certificate with the record's `id` as its number (`Certificate no. 00005`).

Later:

```text
templify store list -s person.schema.json certificates.sqlite
templify render --object -s person.schema.json --store certificates.sqlite --id 5 -t certificate.docx -o reprints
```

## Excel to JSON

**Job:** hand the employee sheet to a developer or an API as JSON.

One line of template is enough
([`all.json`](https://github.com/aaltatan/templify/blob/main/examples/all.json)):

```bash
templify render -t all.json -d employees.xlsx -o export -f employees --order name
```

Excel date cells come out as ISO date and time: `"hired": "2024-02-10T00:00:00"`. To
write the day only, choose the order of the keys, or leave columns out, write the fields
yourself.
[`export.json`](https://github.com/aaltatan/templify/blob/main/examples/export.json):

```jinja
[
{%- for e in objects %}
  {
    "id": {{ e.id | tojson }},
    "name": {{ e.name | tojson }},
    "department": {{ e.department | tojson }},
    "salary": {{ e.salary | tojson }},
    "hired": {{ e.hired | to_date | date.isoformat | tojson }},
    "email": {{ e.email | tojson }}
  }{{ "," if not loop.last }}
{%- endfor %}
]
```

```bash
templify render -t export.json -d employees.xlsx -o export -f employees
```

## One JSON file per record, for an API import

```bash
templify render --each -t profile.json -d employees.xlsx -o api -n email \
  --filter '{"name": "is_null", "args": ["email"], "kwargs": {}, "inverse": true}'
```

Each file is valid JSON, checked before it is saved, and named after the email. Post
them one by one:

=== "PowerShell"

    ```powershell
    Get-ChildItem api/*.json | ForEach-Object {
        Invoke-RestMethod -Method Post -Uri https://api.example.com/people -ContentType application/json -InFile $_.FullName
    }
    ```

=== "bash"

    ```text
    for f in api/*.json; do curl -X POST -H "Content-Type: application/json" --data @"$f" https://api.example.com/people; done
    ```

## A daily job

**Job:** every morning, render the letters for an export the HR system drops overnight,
into a dated folder, and stop if anything is wrong.

=== "PowerShell"

    ```powershell
    $day = Get-Date -Format yyyy-MM-dd
    templify render --each -t offer.docx -d \\server\exports\new-hires.xlsx -o "letters\$day" -n name
    if ($LASTEXITCODE -ne 0) { throw "templify failed with exit code $LASTEXITCODE" }
    ```

=== "bash"

    ```text
    set -e
    templify render --each -t offer.docx -d /mnt/exports/new-hires.xlsx -o "letters/$(date +%F)" -n name
    ```

A new folder each day means re-runs never mix with earlier results. Exit codes are in
[Errors and exit codes](reference/errors.md).

## Name files with two columns

templify names files after **one** column. For `Rama - IT.docx`, add a combined column
to the data. In Excel, a formula such as `=B2&" - "&C2` works once the file is saved in
Excel (formulas give their last calculated value). Then use `-n full_title`.
