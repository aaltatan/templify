# ruff: noqa: DTZ001 - data readers (Excel) return naive datetimes
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import pytest
from templify.cli.main import app, main
from templify.filter_rules import rules
from typer.testing import CliRunner

from .conftest import MakeFile, read_docx

runner = CliRunner(env={"COLUMNS": "1000"})

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def invoke(*args: str | Path) -> tuple[int, str]:
    result = runner.invoke(app, [str(arg) for arg in args])
    return result.exit_code, ANSI_ESCAPE.sub("", result.output)


def filter_eq(key: str, value: str) -> str:
    return json.dumps({"name": "string__eq", "args": [key, value], "kwargs": {}, "inverse": False})


# -----------------------
# multiple templates
# -----------------------


class TestMultipleTemplates:
    @pytest.mark.parametrize("extension", ["txt", "md", "html", "htm"])
    def test_text_formats(
        self, extension: str, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file(f"t.{extension}", "Hello {{ name }}, {{ age }}")
        code, output = invoke("m", "-t", template, "-d", xlsx_file, "-o", output_dir, "-k", "name")

        assert code == 0, output
        assert (output_dir / f"Rama.{extension}").read_text() == "Hello Rama, 25"
        assert len(list(output_dir.iterdir())) == 3

    def test_docx(self, make_docx: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_docx("letter.docx", "Hello {{ name }}")
        code, output = invoke(
            "multiple", "-t", template, "-d", xlsx_file, "-o", output_dir, "-k", "name", "--index"
        )

        assert code == 0, output
        assert read_docx(output_dir / "2 - Rawaa.docx") == "Hello Rawaa"

    def test_json_template_with_json_data(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.json", '{"who": {{ name | tojson }}, "age": {{ age }}}')
        code, output = invoke("m", "-t", template, "-d", json_file, "-o", output_dir, "-k", "name")

        assert code == 0, output
        assert json.loads((output_dir / "Abdullah.json").read_text()) == {
            "who": "Abdullah",
            "age": 32,
        }

    def test_uppercase_extension(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.TXT", "{{ name }}")
        code, output = invoke("m", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert (output_dir / "template-1.txt").read_text() == "Abdullah"

    def test_order_and_index(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        code, output = invoke(
            "m", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "-k", "name", "-i", "--order", "-age",
        )  # fmt: skip

        assert code == 0, output
        assert sorted(p.name for p in output_dir.iterdir()) == [
            "1 - Rawaa.txt",
            "2 - Abdullah.txt",
            "3 - Rama.txt",
        ]

    def test_filter(self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        code, output = invoke(
            "m", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "-k", "name", "--filter", filter_eq("name", "Rama"),
        )  # fmt: skip

        assert code == 0, output
        assert [p.name for p in output_dir.iterdir()] == ["Rama.txt"]

    def test_filter_matching_nothing(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        code, output = invoke(
            "m", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "--filter", filter_eq("name", "Nobody"),
        )  # fmt: skip

        assert code == 0, output
        assert "0 files generated" in output

    def test_runs_twice_without_overwriting(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        args = ("m", "-t", template, "-d", xlsx_file, "-o", output_dir, "-k", "name")

        assert invoke(*args)[0] == 0
        assert invoke(*args)[0] == 0
        assert len(list(output_dir.iterdir())) == 6

    def test_invalid_json_output(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.json", "{{ name }}")
        code, output = invoke("m", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code != 0
        assert "not valid JSON" in output


# -----------------------
# single template
# -----------------------


class TestSingleTemplate:
    def test_txt_default_filename_is_template_name(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file(
            "report.txt", "{% for p in data %}{{ p.name }}={{ p.age }}\n{% endfor %}"
        )
        code, output = invoke("s", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert (output_dir / "report.txt").read_text() == "Abdullah=32\nRawaa=33\nRama=25\n"

    def test_custom_filename_and_variable(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.md", "{% for p in people %}- {{ p.name }}\n{% endfor %}")
        code, output = invoke(
            "single", "-t", template, "-d", json_file, "-o", output_dir,
            "-f", "people", "-v", "people",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "people.md").read_text() == "- Abdullah\n- Rawaa\n- Rama\n"

    def test_json(self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_text_file("all.json", "{{ data | tojson }}")
        code, output = invoke("s", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert json.loads((output_dir / "all.json").read_text())[2] == {"name": "Rama", "age": 25}

    def test_docx(self, make_docx: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_docx(
            "all.docx",
            "{%p for p in data %}\n{{ p.name }}\n{%p endfor %}",
        )
        code, output = invoke("s", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert read_docx(output_dir / "all.docx") == "Abdullah\nRawaa\nRama"

    def test_filtered_and_ordered(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "{% for p in data %}{{ p.name }} {% endfor %}")
        filter_schema = json.dumps(
            {"name": "int__gt", "args": ["age", 30], "kwargs": {}, "inverse": False}
        )
        code, output = invoke(
            "s", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "--order", "name", "--filter", filter_schema,
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "Abdullah Rawaa "

    @pytest.mark.parametrize("command", ["s", "m"])
    def test_output_is_required(
        self, command: str, make_text_file: MakeFile, xlsx_file: Path
    ) -> None:
        template = make_text_file("r.txt", "x")
        code, output = invoke(command, "-t", template, "-d", xlsx_file)

        assert code == 2
        assert "Missing option '-o' / '--output'" in output


# -----------------------
# errors
# -----------------------


class TestErrors:
    @pytest.mark.parametrize("command", ["s", "m"])
    def test_unsupported_template_extension(
        self, command: str, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.pdf", "x")
        code, output = invoke(command, "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 2
        assert "not supported" in output

    def test_template_without_extension(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("Makefile", "x")
        code, output = invoke("m", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 2
        assert "not supported" in output

    def test_template_not_found(self, xlsx_file: Path, tmp_path: Path, output_dir: Path) -> None:
        code, output = invoke(
            "m", "-t", tmp_path / "missing.txt", "-d", xlsx_file, "-o", output_dir
        )
        assert code == 2
        assert "does not exist" in output

    def test_template_is_directory(self, xlsx_file: Path, tmp_path: Path, output_dir: Path) -> None:
        folder = tmp_path / "folder.txt"
        folder.mkdir()
        code, _ = invoke("m", "-t", folder, "-d", xlsx_file, "-o", output_dir)
        assert code == 2

    def test_missing_required_template(self, xlsx_file: Path) -> None:
        code, output = invoke("m", "-d", xlsx_file)
        assert code == 2
        assert "--template" in output

    def test_text_template_syntax_error(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{% if %}")
        code, output = invoke("m", "-t", template, "-d", xlsx_file, "-o", output_dir)
        assert code == 2
        assert "Template Error" in output

    def test_docx_template_syntax_error(
        self, make_docx: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_docx("t.docx", "{{ name ")
        code, output = invoke("s", "-t", template, "-d", xlsx_file, "-o", output_dir)
        assert code == 2
        assert "Template Error" in output

    def test_corrupted_docx_template(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.docx", "not a zip file")
        code, output = invoke("m", "-t", template, "-d", xlsx_file, "-o", output_dir)
        assert code == 2
        assert "Could not load template" in output

    def test_unsupported_data_extension(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("data.csv", "name\nRama")
        code, output = invoke("m", "-t", template, "-d", data, "-o", output_dir)
        assert code == 2
        assert "not supported" in output

    def test_malformed_data_file(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("data.json", '{"not": "a list"}')
        code, output = invoke("m", "-t", template, "-d", data, "-o", output_dir)
        assert code == 2
        assert "Could not read data file" in output

    def test_corrupted_xlsx(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("data.xlsx", "garbage")
        code, output = invoke("m", "-t", template, "-d", data, "-o", output_dir)
        assert code == 2
        assert "Could not read data file" in output

    def test_order_by_unknown_column(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "m", "-t", template, "-d", xlsx_file, "--order", "salary", "-o", output_dir
        )
        assert code == 2
        assert "salary" in output

    def test_invalid_filter_json(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, _ = invoke("m", "-t", template, "-d", xlsx_file, "--filter", "{bad", "-o", output_dir)
        assert code == 2

    def test_output_is_a_file(self, make_text_file: MakeFile, xlsx_file: Path) -> None:
        template = make_text_file("t.txt", "x")
        existing_file = make_text_file("out", "")
        code, _ = invoke("m", "-t", template, "-d", xlsx_file, "-o", existing_file)
        assert code == 2


# -----------------------
# misc
# -----------------------


def test_help_lists_commands() -> None:
    code, output = invoke("--help")
    assert code == 0
    assert "single-template" in output
    assert "multiple-templates" in output


def test_filters_schema_lists_rules() -> None:
    code, output = invoke("fjs")
    lines = {line.split()[0]: line for line in output.splitlines() if line.strip()}

    assert code == 0
    assert lines.keys() == {"Rule", *rules.rules}
    assert "key: string, value: list[string]" in lines["string__is_in"]
    assert "key: string, pattern: string" in lines["string__regex"]
    assert "key: string, value: date " in lines["date__ge"]
    assert "Keep records where `key` is `true`." in lines["is_true"]


# -----------------------
# group by & date filters
# -----------------------


@pytest.fixture
def employees_xlsx(tmp_path: Path) -> Path:
    wb = openpyxl.Workbook()
    sheet = wb.active
    assert sheet is not None
    sheet.append(["name", "city", "joined"])
    sheet.append(["Abdullah", "Homs", datetime(2023, 1, 15)])
    sheet.append(["Rawaa", "Damascus", datetime(2024, 3, 1)])
    sheet.append(["Rama", "Homs", datetime(2024, 6, 20)])
    sheet.append(["Omar", "Aleppo", None])
    path = tmp_path / "employees.xlsx"
    wb.save(path)
    return path


def date_filter(rule: str, value: str) -> str:
    return json.dumps({"name": rule, "args": ["joined", value], "kwargs": {}, "inverse": False})


class TestGroupBy:
    def test_multiple_one_file_per_group(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file(
            "city.md", "# {{ city }}\n{% for p in items %}- {{ p.name }}\n{% endfor %}"
        )
        code, output = invoke(
            "m", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--group-by", "city", "-k", "city",
        )  # fmt: skip

        assert code == 0, output
        assert sorted(p.name for p in output_dir.iterdir()) == [
            "Aleppo.md",
            "Damascus.md",
            "Homs.md",
        ]
        assert (output_dir / "Homs.md").read_text() == "# Homs\n- Abdullah\n- Rama\n"

    def test_single_nested_loop_with_order_and_custom_items(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file(
            "r.txt",
            "{% for g in data %}{{ g.city }}:{% for p in g.people %} {{ p.name }}{% endfor %}\n"
            "{% endfor %}",
        )
        code, output = invoke(
            "s", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--order", "city", "--order", "-name",
            "--group-by", "city", "--group-items", "people",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == (
            "Aleppo: Omar\nDamascus: Rawaa\nHoms: Rama Abdullah\n"
        )

    def test_groups_after_filtering(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "{% for g in data %}{{ g.city }};{% endfor %}")
        code, output = invoke(
            "s", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--filter", filter_eq("city", "Homs"), "--group-by", "city",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "Homs;"

    def test_unknown_group_key(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "m", "-t", template, "-d", employees_xlsx, "--group-by", "country", "-o", output_dir
        )
        assert code == 2
        assert "country" in output

    def test_group_key_clashes_with_items(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "m",
            "-t",
            template,
            "-d",
            employees_xlsx,
            "--group-by",
            "city",
            "--group-items",
            "city",
            "-o",
            output_dir,
        )
        assert code == 2
        assert "can not be one of the group by keys" in output

    def test_unhashable_group_value(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("d.json", '[{"tags": ["a"]}]')
        code, output = invoke(
            "m", "-t", template, "-d", data, "--group-by", "tags", "-o", output_dir
        )
        assert code == 2
        assert "unhashable" in output


class TestDateFilter:
    @pytest.mark.parametrize(
        ("rule", "value", "expected"),
        [
            ("date__eq", "2024-03-01", ["Rawaa"]),
            ("date__ge", "2024-03-01", ["Rawaa", "Rama"]),
            ("date__lt", "2024-01-01", ["Abdullah"]),
        ],
    )
    def test_excel_dates(  # noqa: PLR0913, PLR0917
        self,
        rule: str,
        value: str,
        expected: list[str],
        make_text_file: MakeFile,
        employees_xlsx: Path,
        output_dir: Path,
    ) -> None:
        template = make_text_file("r.txt", "{% for p in data %}{{ p.name }};{% endfor %}")
        not_empty = json.dumps(
            {"name": "is_null", "args": ["joined"], "kwargs": {}, "inverse": True}
        )
        schema = f'{{"operator": "all", "expressions": [{not_empty}, {date_filter(rule, value)}]}}'
        code, output = invoke(
            "s", "-t", template, "-d", employees_xlsx, "-o", output_dir, "--filter", schema
        )

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "".join(f"{n};" for n in expected)

    def test_json_string_dates(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("r.txt", "{% for p in data %}{{ p.name }}{% endfor %}")
        data = make_text_file(
            "d.json",
            '[{"name": "a", "joined": "2024-01-01"}, {"name": "b", "joined": "2025-01-01"}]',
        )
        code, output = invoke(
            "s", "-t", template, "-d", data, "-o", output_dir,
            "--filter", date_filter("date__gt", "2024-06-01"),
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "b"

    def test_empty_cell_gives_clear_error(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "x")
        code, output = invoke(
            "s", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--filter", date_filter("date__eq", "2024-01-01"),
        )  # fmt: skip
        assert code == 2
        assert "Filter failed on a data value" in output

    def test_invalid_filter_date(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "x")
        code, output = invoke(
            "s", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--filter", date_filter("date__eq", "soon"),
        )  # fmt: skip
        assert code == 2
        assert "soon" in output


def test_main_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["templify", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
