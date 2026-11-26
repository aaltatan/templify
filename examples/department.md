# {{ department }}

{% for e in items -%}
- {{ e.name }}: {{ e.salary }}
{% endfor %}
Total: {{ items | sum(attribute="salary") }}
