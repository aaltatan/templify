# {{ title }}

Prepared by {{ company }} for {{ objects | length }} employees.

{% for e in objects -%}
- {{ e.name }} ({{ e.department }})
{% endfor %}
