# Team report

| # | Name | Department | Salary |
|---|------|------------|-------:|
{% for e in objects -%}
| {{ loop.index }} | {{ e.name }} | {{ e.department }} | {{ "{:,}".format(e.salary) }} |
{% endfor %}
**Total salaries:** {{ objects | sum(attribute="salary") }}
