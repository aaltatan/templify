from typing import Any

import pytest
from templify.cli.dependencies.data import _get_compiler
from templify.models import Data
from templify.transformers import OrderByKey, filter_data, group_by_data, order_by_data


def predicate(name: str, *args: Any, inverse: bool = False) -> dict[str, Any]:
    return {"name": name, "args": list(args), "kwargs": {}, "inverse": inverse}


def names(data: Data) -> list[str]:
    return [item["name"] for item in data]


class TestOrderByKey:
    def test_asc(self) -> None:
        key = OrderByKey("age")
        assert (key.name, key.order) == ("age", "asc")

    def test_desc(self) -> None:
        key = OrderByKey("-age")
        assert (key.name, key.order) == ("age", "desc")


class TestOrder:
    def test_single_key(self, people: Data) -> None:
        assert names(order_by_data(people, [OrderByKey("age")])) == ["Rama", "Abdullah", "Rawaa"]

    def test_multiple_keys(self) -> None:
        data = [{"name": "b", "g": 1}, {"name": "a", "g": 2}, {"name": "c", "g": 1}]
        ordered = order_by_data(data, [OrderByKey("g"), OrderByKey("-name")])
        assert names(ordered) == ["c", "b", "a"]

    def test_unknown_key_raises(self, people: Data) -> None:
        with pytest.raises(KeyError, match="salary"):
            order_by_data(people, [OrderByKey("salary")])

    def test_does_not_mutate_input(self, people: Data) -> None:
        original = list(people)
        order_by_data(people, [OrderByKey("-age")])
        assert people == original


class TestFilter:
    def test_single_predicate(self, people: Data) -> None:
        result = filter_data(people, _get_compiler(), predicate("string__eq", "name", "Rama"))
        assert names(result) == ["Rama"]

    def test_inverse(self, people: Data) -> None:
        schema = predicate("string__eq", "name", "Rama", inverse=True)
        assert names(filter_data(people, _get_compiler(), schema)) == ["Abdullah", "Rawaa"]

    def test_regex(self, people: Data) -> None:
        schema = predicate("string__regex", "name", "^Ra")
        assert names(filter_data(people, _get_compiler(), schema)) == ["Rawaa", "Rama"]

    def test_all(self, people: Data) -> None:
        schema = {
            "operator": "all",
            "expressions": [
                predicate("string__startswith", "name", "Ra"),
                predicate("int__lt", "age", 30),
            ],
        }
        assert names(filter_data(people, _get_compiler(), schema)) == ["Rama"]

    def test_any(self, people: Data) -> None:
        schema = {
            "operator": "any",
            "expressions": [
                predicate("string__eq", "name", "Rama"),
                predicate("int__gt", "age", 32),
            ],
        }
        assert names(filter_data(people, _get_compiler(), schema)) == ["Rawaa", "Rama"]


class TestGroupBy:
    @pytest.fixture
    def employees(self) -> Data:
        return [
            {"name": "Abdullah", "city": "Homs", "team": "a"},
            {"name": "Rawaa", "city": "Damascus", "team": "a"},
            {"name": "Rama", "city": "Homs", "team": "b"},
            {"name": "Omar", "city": "Homs", "team": "a"},
        ]

    def test_single_key(self, employees: Data) -> None:
        groups = group_by_data(employees, ["city"])
        assert [g["city"] for g in groups] == ["Homs", "Damascus"]
        assert names(groups[0]["items"]) == ["Abdullah", "Rama", "Omar"]
        assert set(groups[0]) == {"city", "items"}

    def test_multiple_keys(self, employees: Data) -> None:
        groups = group_by_data(employees, ["city", "team"])
        assert [(g["city"], g["team"], names(g["items"])) for g in groups] == [
            ("Homs", "a", ["Abdullah", "Omar"]),
            ("Damascus", "a", ["Rawaa"]),
            ("Homs", "b", ["Rama"]),
        ]

    def test_keeps_rows_complete_and_in_order(self, employees: Data) -> None:
        [homs, _] = group_by_data(employees, ["city"])
        assert homs["items"][0] == employees[0]

    def test_custom_items_key(self, employees: Data) -> None:
        [group, *_] = group_by_data(employees, ["city"], items_key="people")
        assert names(group["people"]) == ["Abdullah", "Rama", "Omar"]

    def test_no_keys_makes_one_group(self, employees: Data) -> None:
        assert group_by_data(employees, []) == [{"items": employees}]

    def test_empty_data(self) -> None:
        assert group_by_data([], ["city"]) == []

    def test_none_is_a_group_value(self) -> None:
        data = [{"name": "a", "city": None}, {"name": "b", "city": None}]
        assert group_by_data(data, ["city"]) == [{"city": None, "items": data}]

    def test_distinguishes_types(self) -> None:
        data = [{"name": "a", "code": 1}, {"name": "b", "code": "1"}]
        assert len(group_by_data(data, ["code"])) == 2

    def test_unknown_key_raises(self, employees: Data) -> None:
        with pytest.raises(KeyError, match="country"):
            group_by_data(employees, ["country"])

    def test_items_key_clash_raises(self, employees: Data) -> None:
        with pytest.raises(ValueError, match="items"):
            group_by_data(employees, ["items"])

    def test_unhashable_value_raises(self) -> None:
        with pytest.raises(TypeError):
            group_by_data([{"name": "a", "tags": ["x"]}], ["tags"])
