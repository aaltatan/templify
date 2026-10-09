# ruff: noqa: DTZ001 - data readers (Excel) return naive datetimes
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pyspecification import ProcessArgumentError
from templify.cli.dependencies.data import _get_compiler
from templify.filter_rules import _process_decimal, _to_date, rules


def matches(rule: str, value: Any, *args: Any) -> bool:
    schema = {"name": rule, "args": ["v", *args], "kwargs": {}, "inverse": False}
    return _get_compiler().compile(schema)({"v": value})


D = Decimal
U1 = uuid.UUID(int=1)
U2 = uuid.UUID(int=2)
U3 = uuid.UUID(int=3)
DT = datetime(2024, 5, 10, 12, 0)

# (rule, filter args, value that matches, value that does not match)
CASES = [
    # bool
    ("is_true", (), True, 1),
    ("is_null", (), None, ""),
    # int
    ("int__eq", (5,), 5, 6),
    ("int__gt", (5,), 6, 5),
    ("int__ge", (5,), 5, 4),
    ("int__lt", (5,), 4, 5),
    ("int__le", (5,), 5, 6),
    ("int__eq", ("5",), 5, 6),  # processor converts the filter value
    # float
    ("float__eq", (1.5,), 1.5, 1.6),
    ("float__gt", (1.5,), 1.6, 1.5),
    ("float__ge", (1.5,), 1.5, 1.4),
    ("float__lt", (1.5,), 1.4, 1.5),
    ("float__le", (1.5,), 1.5, 1.6),
    # string
    ("string__eq", ("Rama",), "Rama", "rama"),
    ("string__regex", (r"^R\w+a$",), "Rama", "Rami"),
    ("string__contains", ("am",), "Rama", "RAMA"),
    ("string__icontains", ("AM",), "Rama", "Rawaa"),
    ("string__is_in", (["Rama", "Rawaa"],), "Rama", "rama"),
    ("string__iis_in", (["RAMA"],), "rama", "Rawaa"),
    ("string__startswith", ("Ra",), "Rama", "rama"),
    ("string__istartswith", ("RA",), "rama", "Abdullah"),
    ("string__endswith", ("ma",), "Rama", "RAMA"),
    ("string__iendswith", ("MA",), "rama", "Rawaa"),
    ("string__length_eq", (4,), "Rama", "Rawaa"),
    ("string__length_gt", (4,), "Rawaa", "Rama"),
    ("string__length_ge", (4,), "Rama", "Ram"),
    ("string__length_lt", (4,), "Ram", "Rama"),
    ("string__length_le", (4,), "Rama", "Rawaa"),
    # decimal
    ("decimal__eq", ("10.50",), D("10.50"), D("10.51")),
    ("decimal__gt", (10,), D("10.01"), D("10")),
    ("decimal__ge", (10.5,), D("10.50"), D("10.49")),
    ("decimal__lt", ("10",), D("9.99"), D("10")),
    ("decimal__le", ("10",), D("10"), D("10.01")),
    # datetime
    ("datetime__eq", ("2024-05-10T12:00:00",), DT, datetime(2024, 5, 10, 12, 1)),
    ("datetime__gt", ("2024-05-10T12:00:00",), datetime(2024, 5, 10, 12, 1), DT),
    ("datetime__ge", ("2024-05-10T12:00:00",), DT, datetime(2024, 5, 10, 11, 59)),
    ("datetime__lt", ("2024-05-10T12:00:00",), datetime(2024, 5, 10, 11, 59), DT),
    ("datetime__le", ("2024-05-10T12:00:00",), DT, datetime(2024, 5, 10, 12, 1)),
    # date: compares the day only, whatever the data type is
    ("date__eq", ("2024-05-10",), DT, datetime(2024, 5, 11)),
    ("date__eq", ("2024-05-10",), "2024-05-10", "2024-05-11"),
    ("date__eq", ("2024-05-10",), date(2024, 5, 10), date(2024, 5, 11)),
    ("date__eq", ("2024-05-10T23:59:00",), "2024-05-10", "2024-05-11"),
    ("date__gt", ("2024-05-10",), "2024-05-11", DT),
    ("date__ge", ("2024-05-10",), DT, "2024-05-09T23:59:59"),
    ("date__lt", ("2024-05-10",), date(2024, 5, 9), DT),
    ("date__le", ("2024-05-10",), DT, "2024-05-11"),
    # uuid
    ("uuid__eq", (str(U2),), U2, U3),
    ("uuid__gt", (str(U2),), U3, U2),
    ("uuid__ge", (str(U2),), U2, U1),
    ("uuid__lt", (str(U2),), U1, U2),
    ("uuid__le", (str(U2),), U2, U3),
]


@pytest.mark.parametrize(("rule", "args", "match", "no_match"), CASES)
def test_rule(rule: str, args: tuple[Any, ...], match: Any, no_match: Any) -> None:
    assert matches(rule, match, *args) is True
    assert matches(rule, no_match, *args) is False


def test_every_rule_is_tested() -> None:
    tested = {case[0] for case in CASES}
    assert tested == set(rules.rules)


def test_missing_key_is_rejected() -> None:
    schema = {"name": "int__eq", "args": ["missing", 1], "kwargs": {}, "inverse": False}
    predicate = _get_compiler().compile(schema)
    with pytest.raises(Exception, match="missing"):
        predicate({"v": 1})


@pytest.mark.parametrize(("rule", "value"), [("date__eq", "yesterday"), ("int__eq", "five")])
def test_invalid_filter_value(rule: str, value: str) -> None:
    with pytest.raises(ProcessArgumentError):
        matches(rule, None, value)


class TestToDate:
    @pytest.mark.parametrize(
        "value",
        [date(2024, 5, 10), datetime(2024, 5, 10, 8), "2024-05-10", "2024-05-10T08:00:00"],
    )
    def test_converts(self, value: date | str) -> None:
        assert _to_date(value) == date(2024, 5, 10)

    @pytest.mark.parametrize("value", [None, 20240510])
    def test_unsupported_type(self, value: Any) -> None:
        with pytest.raises(TypeError, match="to a date"):
            _to_date(value)

    def test_invalid_string(self) -> None:
        with pytest.raises(ValueError, match="isoformat"):
            _to_date("10/05/2024")


class TestProcessDecimal:
    def test_str_and_int(self) -> None:
        assert _process_decimal("1.25") == D("1.25")
        assert _process_decimal(3) == D(3)

    def test_float_is_rounded_to_cents(self) -> None:
        assert _process_decimal(0.1) == D("0.10")

    def test_unsupported_type(self) -> None:
        with pytest.raises(TypeError):
            _process_decimal(None)  # type: ignore[arg-type]
