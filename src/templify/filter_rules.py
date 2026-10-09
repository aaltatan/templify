"""Filter rules for the `--filter` option, each keeps the records matching a condition.

The first argument of every rule is the column (`key`), and values coming from the filter
JSON are converted to the rule type, so `{"name": "int__gt", "args": ["age", "30"]}` works.
The conversion is declared on the `value` type with a `Process` marker.
"""

import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from pyspecification import Process, SubscriptableRulesRegistry

rules = SubscriptableRulesRegistry[dict[str, Any], str, bool](
    operator="logical",
    check_key_existence=True,
)
"""The registry of every filter rule, keyed by rule name."""

# -----------------------
# bool
# -----------------------


@rules.rule()
def is_true(d: dict[str, Any], key: str) -> bool:
    """Keep records where `key` is `true`."""
    return d[key] is True


@rules.rule()
def is_null(d: dict[str, Any], key: str) -> bool:
    """Keep records where `key` is empty (`null`)."""
    return d[key] is None


# -----------------------
# int
# -----------------------

type IntValue = Annotated[int, Process(int)]


@rules.rule()
def int__eq(d: dict[str, Any], key: str, value: IntValue) -> bool:
    """Keep records where `key` equals `value`."""
    return d[key] == value


@rules.rule()
def int__gt(d: dict[str, Any], key: str, value: IntValue) -> bool:
    """Keep records where `key` is greater than `value`."""
    return d[key] > value


@rules.rule()
def int__ge(d: dict[str, Any], key: str, value: IntValue) -> bool:
    """Keep records where `key` is greater than or equal to `value`."""
    return d[key] >= value


@rules.rule()
def int__lt(d: dict[str, Any], key: str, value: IntValue) -> bool:
    """Keep records where `key` is less than `value`."""
    return d[key] < value


@rules.rule()
def int__le(d: dict[str, Any], key: str, value: IntValue) -> bool:
    """Keep records where `key` is less than or equal to `value`."""
    return d[key] <= value


# -----------------------
# float
# -----------------------

type FloatValue = Annotated[float, Process(float)]


@rules.rule()
def float__eq(d: dict[str, Any], key: str, value: FloatValue) -> bool:
    """Keep records where `key` equals `value`."""
    return d[key] == value


@rules.rule()
def float__gt(d: dict[str, Any], key: str, value: FloatValue) -> bool:
    """Keep records where `key` is greater than `value`."""
    return d[key] > value


@rules.rule()
def float__ge(d: dict[str, Any], key: str, value: FloatValue) -> bool:
    """Keep records where `key` is greater than or equal to `value`."""
    return d[key] >= value


@rules.rule()
def float__lt(d: dict[str, Any], key: str, value: FloatValue) -> bool:
    """Keep records where `key` is less than `value`."""
    return d[key] < value


@rules.rule()
def float__le(d: dict[str, Any], key: str, value: FloatValue) -> bool:
    """Keep records where `key` is less than or equal to `value`."""
    return d[key] <= value


# -----------------------
# string
# -----------------------


@rules.rule()
def string__eq(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` equals `value`."""
    return d[key] == value


@rules.rule()
def string__regex(d: dict[str, Any], key: str, pattern: str) -> bool:
    """Keep records where `key` matches the regular expression `pattern`."""
    return re.search(pattern, d[key]) is not None


@rules.rule()
def string__contains(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` contains `value`."""
    return value in d[key]


@rules.rule()
def string__icontains(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` contains `value`, ignoring case."""
    return value.lower() in d[key].lower()


@rules.rule()
def string__is_in(d: dict[str, Any], key: str, value: list[str]) -> bool:
    """Keep records where `key` is one of the `value` list."""
    return d[key] in value


@rules.rule()
def string__iis_in(d: dict[str, Any], key: str, value: list[str]) -> bool:
    """Keep records where `key` is one of the `value` list, ignoring case."""
    return d[key].lower() in [item.lower() for item in value]


@rules.rule()
def string__startswith(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` starts with `value`."""
    return d[key].startswith(value)


@rules.rule()
def string__istartswith(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` starts with `value`, ignoring case."""
    return d[key].lower().startswith(value.lower())


@rules.rule()
def string__endswith(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` ends with `value`."""
    return d[key].endswith(value)


@rules.rule()
def string__iendswith(d: dict[str, Any], key: str, value: str) -> bool:
    """Keep records where `key` ends with `value`, ignoring case."""
    return d[key].lower().endswith(value.lower())


@rules.rule()
def string__length_eq(d: dict[str, Any], key: str, value: int) -> bool:
    """Keep records where the length of `key` equals `value`."""
    return len(d[key]) == value


@rules.rule()
def string__length_gt(d: dict[str, Any], key: str, value: int) -> bool:
    """Keep records where the length of `key` is greater than `value`."""
    return len(d[key]) > value


@rules.rule()
def string__length_ge(d: dict[str, Any], key: str, value: int) -> bool:
    """Keep records where the length of `key` is greater than or equal to `value`."""
    return len(d[key]) >= value


@rules.rule()
def string__length_lt(d: dict[str, Any], key: str, value: int) -> bool:
    """Keep records where the length of `key` is less than `value`."""
    return len(d[key]) < value


@rules.rule()
def string__length_le(d: dict[str, Any], key: str, value: int) -> bool:
    """Keep records where the length of `key` is less than or equal to `value`."""
    return len(d[key]) <= value


# -----------------------
# decimal
# -----------------------


def _process_decimal(value: str | float) -> Decimal:
    if isinstance(value, (str, int)):
        return Decimal(value)

    if isinstance(value, float):
        return Decimal.from_float(value).quantize(Decimal("0.01"))

    msg = f"Unexpected type {type(value)}"
    raise TypeError(msg)


type DecimalValue = Annotated[Decimal, Process(_process_decimal)]


@rules.rule()
def decimal__eq(d: dict[str, Any], key: str, value: DecimalValue) -> bool:
    """Keep records where `key` equals `value`."""
    return d[key] == value


@rules.rule()
def decimal__gt(d: dict[str, Any], key: str, value: DecimalValue) -> bool:
    """Keep records where `key` is greater than `value`."""
    return d[key] > value


@rules.rule()
def decimal__ge(d: dict[str, Any], key: str, value: DecimalValue) -> bool:
    """Keep records where `key` is greater than or equal to `value`."""
    return d[key] >= value


@rules.rule()
def decimal__lt(d: dict[str, Any], key: str, value: DecimalValue) -> bool:
    """Keep records where `key` is less than `value`."""
    return d[key] < value


@rules.rule()
def decimal__le(d: dict[str, Any], key: str, value: DecimalValue) -> bool:
    """Keep records where `key` is less than or equal to `value`."""
    return d[key] <= value


# -----------------------
# datetime
# -----------------------

type DatetimeValue = Annotated[datetime, Process(datetime.fromisoformat)]


@rules.rule()
def datetime__eq(d: dict[str, Any], key: str, value: DatetimeValue) -> bool:
    """Keep records where `key` equals `value`."""
    return d[key] == value


@rules.rule()
def datetime__gt(d: dict[str, Any], key: str, value: DatetimeValue) -> bool:
    """Keep records where `key` is greater than `value`."""
    return d[key] > value


@rules.rule()
def datetime__ge(d: dict[str, Any], key: str, value: DatetimeValue) -> bool:
    """Keep records where `key` is greater than or equal to `value`."""
    return d[key] >= value


@rules.rule()
def datetime__lt(d: dict[str, Any], key: str, value: DatetimeValue) -> bool:
    """Keep records where `key` is less than `value`."""
    return d[key] < value


@rules.rule()
def datetime__le(d: dict[str, Any], key: str, value: DatetimeValue) -> bool:
    """Keep records where `key` is less than or equal to `value`."""
    return d[key] <= value


# -----------------------
# date
# -----------------------


def _to_date(value: date | str) -> date:
    """Accept dates, datetimes (like Excel cells) and ISO strings (like JSON values)."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(value).date()

    msg = f"Can not convert {type(value).__name__} '{value}' to a date"
    raise TypeError(msg)


type DateValue = Annotated[date, Process(datetime.fromisoformat), Process(datetime.date)]
"""An ISO date or datetime string from the filter JSON, keeping the day only."""


@rules.rule()
def date__eq(d: dict[str, Any], key: str, value: DateValue) -> bool:
    """Keep records where `key` equals `value`, comparing the day only."""
    return _to_date(d[key]) == value


@rules.rule()
def date__gt(d: dict[str, Any], key: str, value: DateValue) -> bool:
    """Keep records where `key` is greater than `value`, comparing the day only."""
    return _to_date(d[key]) > value


@rules.rule()
def date__ge(d: dict[str, Any], key: str, value: DateValue) -> bool:
    """Keep records where `key` is greater than or equal to `value`, comparing the day only."""
    return _to_date(d[key]) >= value


@rules.rule()
def date__lt(d: dict[str, Any], key: str, value: DateValue) -> bool:
    """Keep records where `key` is less than `value`, comparing the day only."""
    return _to_date(d[key]) < value


@rules.rule()
def date__le(d: dict[str, Any], key: str, value: DateValue) -> bool:
    """Keep records where `key` is less than or equal to `value`, comparing the day only."""
    return _to_date(d[key]) <= value


# -----------------------
# uuid
# -----------------------

type UUIDValue = Annotated[uuid.UUID, Process(uuid.UUID)]


@rules.rule()
def uuid__eq(d: dict[str, Any], key: str, value: UUIDValue) -> bool:
    """Keep records where `key` equals `value`."""
    return d[key] == value


@rules.rule()
def uuid__gt(d: dict[str, Any], key: str, value: UUIDValue) -> bool:
    """Keep records where `key` is greater than `value`."""
    return d[key] > value


@rules.rule()
def uuid__ge(d: dict[str, Any], key: str, value: UUIDValue) -> bool:
    """Keep records where `key` is greater than or equal to `value`."""
    return d[key] >= value


@rules.rule()
def uuid__lt(d: dict[str, Any], key: str, value: UUIDValue) -> bool:
    """Keep records where `key` is less than `value`."""
    return d[key] < value


@rules.rule()
def uuid__le(d: dict[str, Any], key: str, value: UUIDValue) -> bool:
    """Keep records where `key` is less than or equal to `value`."""
    return d[key] <= value
