# Filter rules

Every rule `--filter` and `store search` accept, with its arguments in `args` order.
`templify filters` prints the same list. How to write and combine rules is in
[Order and filter](../guide/order-filter.md).

```json
{"name": "<rule>", "args": ["<column>", <value>], "kwargs": {}, "inverse": false}
```

- The first argument is always the **column** (`key`).
- The argument names are also the `kwargs` names: `{"key": "salary", "value": 1400}`.
- Values are converted to the rule's type: `"5"` works for `int__eq`.
- `"inverse": true` keeps the rows that do **not** match.
- `date__*` rules compare the day only, and accept Excel dates and ISO strings.
  `datetime__*` rules need real datetimes (Excel date cells).
- For `decimal__*`, the value can be a string (`"10.50"`), an integer, or a float
  rounded to 2 decimals.

## Boolean and null

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `is_true` | `key`: string | `key` is `true` |
| `is_null` | `key`: string | `key` is empty (`null`) |

## Text

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `string__eq` | `key`: string, `value`: string | `key` equals `value` |
| `string__regex` | `key`: string, `pattern`: string | `key` matches the regular expression `pattern` |
| `string__contains` | `key`: string, `value`: string | `key` contains `value` |
| `string__icontains` | `key`: string, `value`: string | `key` contains `value`, ignoring case |
| `string__is_in` | `key`: string, `value`: list[string] | `key` is one of the `value` list |
| `string__iis_in` | `key`: string, `value`: list[string] | `key` is one of the `value` list, ignoring case |
| `string__startswith` | `key`: string, `value`: string | `key` starts with `value` |
| `string__istartswith` | `key`: string, `value`: string | `key` starts with `value`, ignoring case |
| `string__endswith` | `key`: string, `value`: string | `key` ends with `value` |
| `string__iendswith` | `key`: string, `value`: string | `key` ends with `value`, ignoring case |
| `string__length_eq` | `key`: string, `value`: integer | the length of `key` equals `value` |
| `string__length_gt` | `key`: string, `value`: integer | the length of `key` is greater than `value` |
| `string__length_ge` | `key`: string, `value`: integer | the length of `key` is greater than or equal to `value` |
| `string__length_lt` | `key`: string, `value`: integer | the length of `key` is less than `value` |
| `string__length_le` | `key`: string, `value`: integer | the length of `key` is less than or equal to `value` |

## Whole numbers

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `int__eq` | `key`: string, `value`: integer | `key` equals `value` |
| `int__gt` | `key`: string, `value`: integer | `key` is greater than `value` |
| `int__ge` | `key`: string, `value`: integer | `key` is greater than or equal to `value` |
| `int__lt` | `key`: string, `value`: integer | `key` is less than `value` |
| `int__le` | `key`: string, `value`: integer | `key` is less than or equal to `value` |

## Decimal numbers (float)

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `float__eq` | `key`: string, `value`: number | `key` equals `value` |
| `float__gt` | `key`: string, `value`: number | `key` is greater than `value` |
| `float__ge` | `key`: string, `value`: number | `key` is greater than or equal to `value` |
| `float__lt` | `key`: string, `value`: number | `key` is less than `value` |
| `float__le` | `key`: string, `value`: number | `key` is less than or equal to `value` |

## Exact decimals (money)

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `decimal__eq` | `key`: string, `value`: string | number | `key` equals `value` |
| `decimal__gt` | `key`: string, `value`: string | number | `key` is greater than `value` |
| `decimal__ge` | `key`: string, `value`: string | number | `key` is greater than or equal to `value` |
| `decimal__lt` | `key`: string, `value`: string | number | `key` is less than `value` |
| `decimal__le` | `key`: string, `value`: string | number | `key` is less than or equal to `value` |

## Dates

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `date__eq` | `key`: string, `value`: date | `key` equals `value`, comparing the day only |
| `date__gt` | `key`: string, `value`: date | `key` is greater than `value`, comparing the day only |
| `date__ge` | `key`: string, `value`: date | `key` is greater than or equal to `value`, comparing the day only |
| `date__lt` | `key`: string, `value`: date | `key` is less than `value`, comparing the day only |
| `date__le` | `key`: string, `value`: date | `key` is less than or equal to `value`, comparing the day only |

## Date and time

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `datetime__eq` | `key`: string, `value`: date-time | `key` equals `value` |
| `datetime__gt` | `key`: string, `value`: date-time | `key` is greater than `value` |
| `datetime__ge` | `key`: string, `value`: date-time | `key` is greater than or equal to `value` |
| `datetime__lt` | `key`: string, `value`: date-time | `key` is less than `value` |
| `datetime__le` | `key`: string, `value`: date-time | `key` is less than or equal to `value` |

## UUIDs

| Rule | Arguments | Keeps rows where |
|------|-----------|------------------|
| `uuid__eq` | `key`: string, `value`: uuid | `key` equals `value` |
| `uuid__gt` | `key`: string, `value`: uuid | `key` is greater than `value` |
| `uuid__ge` | `key`: string, `value`: uuid | `key` is greater than or equal to `value` |
| `uuid__lt` | `key`: string, `value`: uuid | `key` is less than `value` |
| `uuid__le` | `key`: string, `value`: uuid | `key` is less than or equal to `value` |
