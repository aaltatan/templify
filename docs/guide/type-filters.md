# Type filters

Every template gets the [jinja-types](https://pypi.org/project/jinja-types/) filters and
tests: **Python's own methods**, with the same names and arguments, under a namespace.
If you know Python's `str.zfill` or `date.strftime`, you already know the filter.

```jinja
Ref: {{ id | to_str | str.zfill(5) }}
Salary: {{ salary | to_decimal | decimal.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP) | fmt(",.2f") }}
Hired: {{ hired | to_date | date.strftime("%d/%m/%Y") }}
In words: {{ salary | int | ar.to_words }}
{% if code is str.isdigit %}numeric code{% endif %}
```

```text
Ref: 00003
Salary: 1,500.00
Hired: 10/02/2024
In words: ألف وخمسمئة
```

## Namespaces

| Namespace | For | Examples |
|-----------|-----|----------|
| helpers (no prefix) | Converting values | `to_str`, `to_int`, `to_decimal`, `to_date`, `to_datetime`, `to_bool`, `fmt` |
| `str.` | Text | `str.zfill`, `str.title`, `str.replace`, `str.split`, `str.startswith` |
| `int.`, `float.` | Numbers | `int.bit_length`, `float.is_integer` |
| `decimal.` | Exact money | `decimal.quantize`, `decimal.ROUND_HALF_UP` |
| `date.`, `datetime.`, `time.`, `timedelta.` | Dates and times | `date.strftime`, `date.isoformat`, `datetime.date` |
| `list.`, `dict.` | Collections (new values, never changing the old one) | `list.append`, `dict.get` |
| `re.`, `pattern.`, `match.` | Regular expressions | `re.sub`, `re.findall` |
| `uuid.`, `fraction.`, `path.` | Others | `uuid.hex`, `path.stem` |
| `ar.` | Arabic text, numbers and dates | `ar.to_words`, `ar.format_date`, `ar.to_arabic_digits` |

List every member, or one namespace or kind, with
[`templify types`](../reference/commands.md#types):

```bash
templify types -n str -k test
```

```text
 Name           Kinds          Description
 str.endswith   filter, test   Return True if the string ends with `suffix` (or any suffix in a tuple).
 str.isalnum    filter, test   Return True if all characters are alphanumeric.
 ...
```

The complete list is in the [Type filters reference](../reference/types.md).

## Filters, tests and globals

| Kind | Used as | Example |
|------|---------|---------|
| filter | after `\|` | `{{ code \| str.zfill(5) }}` |
| test | after `is` | `{% if code is str.isdigit %}` |
| attribute | a constant inside a namespace | `decimal.ROUND_HALF_UP` |
| global | a function or object | `{{ today() }}`, `{{ now() }}`, `decimal.Decimal("0.01")` |

## Common jobs

| Want | Write | Gives |
|------|-------|-------|
| Pad a number | `{{ id \| to_str \| str.zfill(5) }}` | `00003` |
| Thousands separator | `{{ salary \| fmt(",") }}` | `1,500` |
| Two decimals, rounded half up | `{{ salary \| to_decimal \| decimal.quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP) }}` | `1500.00` |
| A date from JSON or Excel | `{{ hired \| to_date \| date.strftime("%d %B %Y") }}` | `10 February 2024` |
| Today's date | `{{ today() \| date.isoformat }}` | `2026-11-26` |
| Title case | `{{ name \| str.title }}` | `Rama` |
| Replace text | `{{ phone \| str.replace("-", " ") }}` | |
| A value from the command line as a number | `{{ rate \| to_decimal }}` | |

## Arabic

The `ar.` namespace handles Arabic numbers, dates and text.
[`examples/salary-certificate.md`](https://github.com/aaltatan/templify/blob/main/examples/salary-certificate.md):

```jinja
# شهادة راتب

نشهد بأن السيد/ة **{{ name }}** يعمل لدينا في قسم {{ department }} منذ
{{ hired | to_date | ar.format_date("%d %B %Y") }}، وأن راتبه الشهري
{{ salary | ar.format_number }} دولار أمريكي ({{ salary | ar.to_words }} دولار أمريكي لا غير).
```

```bash
templify render --each -t salary-certificate.md -d employees.xlsx -o certificates -n name
```

`certificates/Rama.md`:

```markdown
# شهادة راتب

نشهد بأن السيد/ة **Rama** يعمل لدينا في قسم IT منذ
10 شباط 2024، وأن راتبه الشهري
1,500 دولار أمريكي (ألف وخمسمئة دولار أمريكي لا غير).
```

| Filter | Does | Example |
|--------|------|---------|
| `ar.to_words` | A number in Arabic words (تفقيط) | `1500` → `ألف وخمسمئة` |
| `ar.format_number` | A number with a digit set and separators | `ar.format_number(digits="arabic", grouping="٬", decimal="٫", places=2)` → `١٬٥٠٠٫٠٠` |
| `ar.format_date` | A date with Arabic month names; `%O` is the ordinal day | `ar.format_date("%d %B %Y")` → `10 شباط 2024` |
| `ar.month_name` | The month's name | `كانون الثاني`; `ar.month_name("levant_with_egyptian")` → `كانون الثاني (يناير)` |
| `ar.weekday_name` | The weekday's name | `الاثنين` |
| `ar.ordinal`, `ar.ordinal_adverb` | Ordinals from 1 to 100 | `الثالث`, `ثالثًا` |
| `ar.to_arabic_digits`, `ar.to_latin_digits` | Change the digits | `2026` ↔ `٢٠٢٦` |
| `ar.normalize`, `ar.equals`, `ar.sort` | Compare and sort Arabic text | `{{ names \| ar.sort }}` |
| `ar.duration`, `ar.since` | Durations in words | `أسبوع ويومان` |

`ar.format_date` takes `months="levant"` (default: كانون الثاني، شباط...),
`"egyptian"` (يناير، فبراير...), `"maghreb"` or `"levant_with_egyptian"`.

!!! note "Currencies"
    `ar.to_words` and `ar.format_money` can count a currency (ليرة سورية، قرش), but the
    currency has to be defined in Python, so it is not available from the command line.
    Write the currency name in the template instead, as above.

## Mistakes are caught

A misspelled name is an error with a suggestion, not an empty result:

```text
Template Error: No filter named 'str.zfil'. Did you mean: str.zfill, str.find, str.title?
```
