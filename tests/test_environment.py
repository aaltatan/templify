# ruff: noqa: DTZ001 - data readers (Excel) return naive datetimes
"""The sandboxed jinja-types environment: real templates, hints and the `types` command."""

import json
from datetime import datetime
from pathlib import Path

import openpyxl
import pytest
from jinja2 import TemplateError
from jinja2.sandbox import ImmutableSandboxedEnvironment

from templify.cli.cli import _namespaces
from templify.environment import describe, environment

from .conftest import MakeFile, read_docx
from .test_cli import invoke

LETTER = (
    "Dear {{ name | str.title }},\n"
    "Your salary from {{ hired | date.strftime('%d/%m/%Y') }} is "
    "{{ salary | to_decimal | decimal.quantize(decimal.Decimal('0.01'), "
    "rounding=decimal.ROUND_HALF_UP) | fmt(',.2f') }}.\n"
    "Ref: {{ id | to_str | str.zfill(5) }}"
)


@pytest.fixture
def staff_xlsx(tmp_path: Path) -> Path:
    wb = openpyxl.Workbook()
    sheet = wb.active

    assert sheet is not None

    sheet.append(["id", "name", "salary", "hired"])
    sheet.append([7, "rama ali", 1500.005, datetime(2024, 3, 1)])
    sheet.append([42, "omar haddad", 2250, datetime(2021, 11, 15)])

    path = tmp_path / "staff.xlsx"
    wb.save(path)

    return path


def test_environment_is_sandboxed_with_jinja_types() -> None:
    env = environment()

    assert isinstance(env, ImmutableSandboxedEnvironment)
    assert env.from_string("{{ '7' | str.zfill(3) }}").render() == "007"


def test_salary_letters_docx(make_docx: MakeFile, staff_xlsx: Path, output_dir: Path) -> None:
    template = make_docx("letter.docx", LETTER)

    code, output = invoke(
        "render", "--each", "-t", template, "-d", staff_xlsx, "-o", output_dir, "-n", "name"
    )

    assert code == 0, output
    assert read_docx(output_dir / "rama ali.docx") == (
        "Dear Rama Ali,\nYour salary from 01/03/2024 is 1,500.01.\nRef: 00007"
    )
    assert "2,250.00" in read_docx(output_dir / "omar haddad.docx")


def test_fee_table_markdown(make_text_file: MakeFile, tmp_path: Path, output_dir: Path) -> None:
    fees = tmp_path / "fees.json"
    fees.write_text(
        json.dumps([{"item": "Tuition", "amount": 1200}, {"item": "Lab", "amount": 85.5}]),
        encoding="utf-8",
    )
    template = make_text_file(
        "fees.md",
        "| Item | Amount |\n|---|---:|\n"
        "{% for fee in objects %}"
        "| {{ fee.item | str.ljust(8) }} | {{ fee.amount | to_decimal | decimal.quantize("
        "decimal.Decimal('0.01')) }} |\n"
        "{% endfor %}"
        "Total in words: {{ objects | sum(attribute='amount') | int | ar.to_words }}",
    )

    code, output = invoke("render", "-t", template, "-d", fees, "-o", output_dir)

    assert code == 0, output
    assert (output_dir / "fees.md").read_text(encoding="utf-8") == (
        "| Item | Amount |\n|---|---:|\n"
        "| Tuition  | 1200.00 |\n"
        "| Lab      | 85.50 |\n"
        "Total in words: ألف ومئتان وخمسة وثمانون"
    )


def test_sandbox_blocks_mutation(
    make_text_file: MakeFile, json_file: Path, output_dir: Path
) -> None:
    template = make_text_file("t.txt", "{{ objects.append(1) }}")

    code, output = invoke("render", "-t", template, "-d", json_file, "-o", output_dir)

    assert code == 1
    assert "Template Error" in output
    assert "unsafe" in output


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("{{ x | str.zfil(3) }}", "No filter named 'str.zfil'. Did you mean: str.zfill"),
        ("{{ x is str.isdigt }}", "No test named 'str.isdigt'. Did you mean: str.isdigit"),
        ("{{ x | qqqq }}", "No filter named 'qqqq'. See `templify types` for every filter."),
        ("{{ x.y.z }}", "'x' is undefined"),
    ],
)
def test_describe_hints(source: str, expected: str) -> None:
    with pytest.raises(TemplateError) as raised:
        environment().from_string(source).render()

    assert describe(raised.value).startswith(expected)


def test_hint_in_cli(make_text_file: MakeFile, json_file: Path, output_dir: Path) -> None:
    template = make_text_file("t.txt", "{{ name | str.uper }}")

    code, output = invoke("render", "--each", "-t", template, "-d", json_file, "-o", output_dir)

    assert code == 2
    assert "Did you mean: str.upper" in output


def test_types_command() -> None:
    code, output = invoke("types", "-n", "str", "-k", "test")

    assert code == 0, output
    assert "str.isdigit" in output
    assert "str.zfill" not in output

    code, output = invoke("types", "-n", "nope")

    assert code == 1
    assert "namespaces: ar, date" in output


def test_namespace_completion() -> None:
    assert _namespaces("da") == ["date", "datetime"]
