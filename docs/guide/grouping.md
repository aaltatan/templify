# Grouping

`--group-by <column>` merges rows that share a value into **one group**. Each group is
a new row holding:

- the group-by column(s), with the shared value,
- `items` (rename it with `--items-var`): the list of the original rows in the group.

```text
rows:                                  groups (--group-by department):
{name: Abdullah, department: Sales}    {department: Sales, items: [Abdullah, Omar]}
{name: Rawaa,    department: IT}   ──► {department: IT,    items: [Rawaa, Rama]}
{name: Rama,     department: IT}
{name: Omar,     department: Sales}
```

- Groups appear in the order their first row appears.
- Grouping runs **after** ordering and filtering: `--order` also sorts the rows inside
  every group, and `--filter` decides which rows get grouped.

## One file per group

With `--each`, each group is one file. `-n` can name the files after the group column.

`department.md`:

```jinja
# {{ department }}

{% for e in items -%}
- {{ e.name }}: {{ e.salary }}
{% endfor %}
Total: {{ items | sum(attribute="salary") }}
```

```bash
templify render --each -t department.md -d employees.xlsx -o reports -n department --group-by department --order -salary
```

```text
reports/
├── IT.md
└── Sales.md
```

`reports/IT.md`:

```markdown
# IT

- Rawaa: 1800
- Rama: 1500

Total: 3300
```

## One report of all groups

Without `--each`, `objects` is the list of groups. Loop over the groups, then over
each group's rows.

`by-city.txt`:

```jinja
{% for group in objects -%}
{{ group.city }} / {{ group.department }}:
{%- for e in group.people %} {{ e.name }}{% endfor %}
{% endfor %}
```

```bash
templify render -t by-city.txt -d employees.xlsx -o out \
  --order city --group-by city --group-by department --items-var people
```

```text
Aleppo / Sales: Omar
Damascus / IT: Rawaa
Homs / Sales: Abdullah
Homs / IT: Rama
```

Two `--group-by` columns group by both: one group per city **and** department.

## Group expressions

```jinja
{{ items | length }}                                         {# rows in the group #}
{{ items | sum(attribute="salary") }}                        {# total of a column #}
{{ items | map(attribute="name") | join(", ") }}             {# "Rawaa, Rama" #}
{{ (items | sum(attribute="salary")) / (items | length) }}   {# average #}
{{ items | max(attribute="salary") }}                        {# the row with the top salary #}
{{ items | selectattr("city", "equalto", "Homs") | list | length }}   {# rows in Homs #}
```

## Errors

| Problem | Message |
|---------|---------|
| The column does not exist | `Key 'country' not found in data, Available keys: ...` |
| `--items-var` equals a group-by column | `Items key 'city' can not be one of the group by keys` |
| The column holds lists or objects (JSON) | `Can not group by unhashable values (like lists or objects): ...` |
