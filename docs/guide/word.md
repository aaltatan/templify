# Word (docx) templates

A Word template is a normal `.docx` that you write in Word (or LibreOffice Writer), with
Jinja tags typed into the text. templify fills it with
[docxtpl](https://docxtpl.readthedocs.io/) and keeps all your formatting: fonts,
headers, footers, logos, tables, page size.

You do **not** need Word installed to render.

## A letter per row

[`examples/offer.docx`](https://github.com/aaltatan/templify/blob/main/examples/offer.docx):

```text
Job offer

Dear {{ name }},

We are happy to welcome you to the {{ department }} team in our {{ city }} office.
Your monthly salary is {{ "{:,}".format(salary) }} USD, starting on
{{ hired | date.strftime("%d %B %Y") }}.

Best regards,
HR department
```

```bash
templify render --each -t offer.docx -d employees.xlsx -o offers -n name
```

`offers/Rama.docx` reads:

```text
Dear Rama,

We are happy to welcome you to the IT team in our Homs office.
Your monthly salary is 1,500 USD, starting on 10 February 2024.
```

!!! warning "Keep each tag in one piece"
    Type every `{{ ... }}` in **one go, with one formatting**. If half of `{{ name }}`
    is bold, or Word's spell-checker splits it, Word stores it in pieces and Jinja
    cannot read it. If a tag does not work, delete it and type it again. Format the
    whole tag instead: a bold `{{ name }}` prints the name in bold.

## Word's own tags

docxtpl adds tags for Word's structure. A normal `{% ... %}` leaves an empty
paragraph behind; these remove the paragraph, row or cell that holds them:

| Tag | Removes | Use it for |
|-----|---------|------------|
| `{%p ... %}` | The whole paragraph | Loops and conditions around paragraphs |
| `{%tr ... %}` | The whole table row | One table row per record |
| `{%tc ... %}` | The whole table cell | Repeating columns |
| `{%r ... %}` | The run (a piece of formatted text) | Conditions inside a line |

Write each `{%p %}` and `{%tr %}` tag **alone** in its own paragraph or row.

## All rows in one document

One Word file with a page per person, ready to print in one go.
[`examples/all-offers.docx`](https://github.com/aaltatan/templify/blob/main/examples/all-offers.docx):

```text
{%p for e in objects %}
{{ e.name }}                                  ← Heading 1
Department: {{ e.department }}, {{ e.city }}
{%p if not loop.last %}
<page break>
{%p endif %}
{%p endfor %}
```

```bash
templify render -t all-offers.docx -d employees.xlsx -o print --order name
```

The page break between `{%p if not loop.last %}` and `{%p endif %}` is a real one
(++ctrl+enter++ in Word), so the document does not end with a blank page. A quicker
alternative is `{{ page_break }}` at the end of a line.

## A table row per record

[`examples/staff-table.docx`](https://github.com/aaltatan/templify/blob/main/examples/staff-table.docx)
has a 4-row table:

| Name | Department | City | Salary |
|------|------------|------|--------|
| `{%tr for e in objects %}` | | | |
| `{{ e.name }}` | `{{ e.department }}` | `{{ e.city }}` | `{{ "{:,}".format(e.salary) }}` |
| `{%tr endfor %}` | | | |

Under the table: `Total: {{ "{:,}".format(objects | sum(attribute="salary")) }} USD`.

```bash
templify render -t staff-table.docx -d employees.xlsx -o print --title "Staff list"
```

The rows with the `{%tr %}` tags disappear, and the middle row repeats once per
person. The header row and the table style stay as you designed them.

## One record

[`examples/certificate.docx`](https://github.com/aaltatan/templify/blob/main/examples/certificate.docx)
uses `object`:

```text
Certificate of employment

This is to certify that {{ object.name }} works in our {{ object.department }}
department in {{ object.city }}.

Certificate no. {{ object.id | default(0) | to_str | str.zfill(5) }}
```

```bash
templify render --object -t certificate.docx -d rama.json -o certificates
```

`Certificate no. 00003`. With a [store](stores.md), the id comes from the store, so
every certificate gets its own number.

## Line breaks, tabs and page breaks

| In the template | In Word |
|-----------------|---------|
| `{{ new_line }}` | a line break inside the paragraph |
| `{{ tab }}` | a tab |
| `{{ page_break }}` | a page break |

A value with `\n` in it (an address typed on several lines, say) also becomes line
breaks.

## More

Images, rich text, sub-documents and more are in the
[docxtpl documentation](https://docxtpl.readthedocs.io/). Everything it supports works
in templify templates.
