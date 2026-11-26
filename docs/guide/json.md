# JSON templates

A `.json` template is rendered like text, then **validated**. If the result is not
valid JSON, nothing is saved and the error points at the problem.

## Always use `tojson`

Write every value through the `tojson` filter. It adds the quotes, escapes characters
like `"`, and turns `None` into `null` and `True` into `true`.

[`examples/profile.json`](https://github.com/aaltatan/templify/blob/main/examples/profile.json):

```jinja
{
  "name": {{ name | tojson }},
  "department": {{ department | tojson }},
  "email": {{ email | tojson }},
  "senior": {{ (salary > 1400) | tojson }}
}
```

```bash
templify render --each -t profile.json -d employees.json -o profiles -n name
```

`profiles/Omar.json`:

```json
{
  "name": "Omar",
  "department": "Sales",
  "email": null,
  "senior": false
}
```

**Why?** With `"name": "{{ name }}"`, a name like `Ra"ma` gives broken JSON, and
templify refuses to save it:

```text
Template Error: Rendered output is not valid JSON: Expecting ',' delimiter: line 1 column 14 (char 13)
```

## The whole dataset

[`examples/all.json`](https://github.com/aaltatan/templify/blob/main/examples/all.json)
is one line:

```jinja
{{ objects | tojson(indent=2) }}
```

```bash
templify render -t all.json -d employees.json -o export -f employees --order name
```

The ordered, filtered and grouped rows, as one JSON file. `tojson` sorts the keys of
each object alphabetically.

!!! warning "Excel dates and `tojson`"
    `tojson` cannot write Python dates, and Excel date cells are dates. Dumping
    `employees.xlsx` this way fails. Write the fields yourself and convert the dates
    to text with `to_date | date.isoformat`:

    ```jinja
    [
    {%- for e in objects %}
      {"name": {{ e.name | tojson }}, "hired": {{ e.hired | to_date | date.isoformat | tojson }}}{{ "," if not loop.last }}
    {%- endfor %}
    ]
    ```

    See [Excel to JSON](../recipes.md#excel-to-json) for the full recipe.

## Shapes for APIs

Templates can reshape the data, not only copy it: rename keys, nest objects, add
constant fields.

```jinja
{
  "employee": {
    "fullName": {{ name | tojson }},
    "contact": {"email": {{ email | tojson }}},
    "team": {{ department | lower | tojson }}
  },
  "source": "hr-export",
  "active": true
}
```

One file per record with `--each`, ready for a bulk API import, or one array with the
default mode.
