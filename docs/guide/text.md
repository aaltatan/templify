# Text, Markdown and HTML

`.txt`, `.md`, `.html` and `.htm` templates are plain Jinja. The output is written as
**UTF-8**, and the template's line endings are kept as they are.

## Text

Good for emails, messages, config files, SQL, CSV: anything that is plain text.
[`examples/email.txt`](https://github.com/aaltatan/templify/blob/main/examples/email.txt):

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

The filter skips Omar, who has no email. See [Recipes](../recipes.md#mail-merge-emails).

## Markdown

Markdown is text with a little structure, so it is ideal for reports that are read on
GitHub, in a wiki, or converted to PDF or Word later with a tool like
[Pandoc](https://pandoc.org).

```bash
templify render -t team.md -d employees.xlsx -o reports --order -salary
```

!!! tip "Whitespace in loops"
    `{% for %}` and `{% endfor %}` lines leave empty lines behind. Add a `-` to trim
    them: `{% for e in objects -%}` removes the line break after the tag. That is how
    `team.md` keeps its table rows together.

## HTML

[`examples/department.html`](https://github.com/aaltatan/templify/blob/main/examples/department.html):

```jinja
<!DOCTYPE html>
<html>
<body>
  <h1>{{ department }} department</h1>
  <ul>
  {%- for e in items %}
    <li>{{ e.name }} ({{ e.city }})</li>
  {%- endfor %}
  </ul>
  <p>{{ items | length }} employees</p>
</body>
</html>
```

```bash
templify render --each -t department.html -d employees.xlsx -o departments --group-by department -n department
```

`departments/IT.html`:

```html
<!DOCTYPE html>
<html>
<body>
  <h1>IT department</h1>
  <ul>
    <li>Rawaa (Damascus)</li>
    <li>Rama (Homs)</li>
  </ul>
  <p>2 employees</p>
</body>
</html>
```

!!! warning "Values are not HTML-escaped"
    `<b>` in your data stays bold, because one template engine serves text, Markdown
    and JSON too. If the data is not trusted, escape it: `{{ e.name | e }}`.

## Including other files

Text templates can include other files **from the template's folder**: a shared
header, footer or style sheet.

```jinja
{% include "header.html" %}
<h1>{{ department }}</h1>
{% include "footer.html" %}
```

The included files are templates too, and see the same variables. `{% extends %}` and
`{% import %}` work the same way. Word templates cannot include files.
