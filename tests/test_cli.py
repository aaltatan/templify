# ruff: noqa: DTZ001 - data readers (Excel) return naive datetimes
import json
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl
import pytest
import questionary
from typer.testing import CliRunner

from templify.cli.cli import app, main
from templify.filter_rules import rules

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
        code, output = invoke(
            "render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir, "-n", "name"
        )

        assert code == 0, output
        assert (output_dir / f"Rama.{extension}").read_text() == "Hello Rama, 25"
        assert len(list(output_dir.iterdir())) == 3

    def test_docx(self, make_docx: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_docx("letter.docx", "Hello {{ name }}")
        code, output = invoke(
            "render",
            "--each",
            "-t",
            template,
            "-d",
            xlsx_file,
            "-o",
            output_dir,
            "-n",
            "name",
            "--numbered",
        )

        assert code == 0, output
        assert read_docx(output_dir / "2 - Rawaa.docx") == "Hello Rawaa"

    def test_json_template_with_json_data(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.json", '{"who": {{ name | tojson }}, "age": {{ age }}}')
        code, output = invoke(
            "render", "--each", "-t", template, "-d", json_file, "-o", output_dir, "-n", "name"
        )

        assert code == 0, output
        assert json.loads((output_dir / "Abdullah.json").read_text()) == {
            "who": "Abdullah",
            "age": 32,
        }

    def test_uppercase_extension(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.TXT", "{{ name }}")
        code, output = invoke("render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert (output_dir / "template-1.txt").read_text() == "Abdullah"

    def test_order_and_index(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        code, output = invoke(
            "render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "-n", "name", "--numbered", "--order", "-age",
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
            "render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "-n", "name", "--filter", filter_eq("name", "Rama"),
        )  # fmt: skip

        assert code == 0, output
        assert [p.name for p in output_dir.iterdir()] == ["Rama.txt"]

    def test_filter_matching_nothing(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        code, output = invoke(
            "render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "--filter", filter_eq("name", "Nobody"),
        )  # fmt: skip

        assert code == 0, output
        assert "0 files generated" in output

    def test_runs_twice_without_overwriting(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{{ name }}")
        args = ("render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir, "-n", "name")

        assert invoke(*args)[0] == 0
        assert invoke(*args)[0] == 0
        assert len(list(output_dir.iterdir())) == 6

    def test_invalid_json_output(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.json", "{{ name }}")
        code, output = invoke("render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 1  # a render failure, not a usage error
        assert "not valid JSON" in output


# -----------------------
# single template
# -----------------------


class TestSingleTemplate:
    def test_txt_default_filename_is_template_name(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file(
            "report.txt", "{% for p in objects %}{{ p.name }}={{ p.age }}\n{% endfor %}"
        )
        code, output = invoke("render", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert (output_dir / "report.txt").read_text() == "Abdullah=32\nRawaa=33\nRama=25\n"

    def test_custom_filename_and_variable(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.md", "{% for p in people %}- {{ p.name }}\n{% endfor %}")
        code, output = invoke(
            "render", "-t", template, "-d", json_file, "-o", output_dir,
            "-f", "people", "-v", "people",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "people.md").read_text() == "- Abdullah\n- Rawaa\n- Rama\n"

    def test_json(self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_text_file("all.json", "{{ objects | tojson }}")
        code, output = invoke("render", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert json.loads((output_dir / "all.json").read_text())[2] == {"name": "Rama", "age": 25}

    def test_docx(self, make_docx: MakeFile, xlsx_file: Path, output_dir: Path) -> None:
        template = make_docx(
            "all.docx",
            "{%p for p in objects %}\n{{ p.name }}\n{%p endfor %}",
        )
        code, output = invoke("render", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 0, output
        assert read_docx(output_dir / "all.docx") == "Abdullah\nRawaa\nRama"

    def test_filtered_and_ordered(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "{% for p in objects %}{{ p.name }} {% endfor %}")
        filter_schema = json.dumps(
            {"name": "int__gt", "args": ["age", 30], "kwargs": {}, "inverse": False}
        )
        code, output = invoke(
            "render", "-t", template, "-d", xlsx_file, "-o", output_dir,
            "--order", "name", "--filter", filter_schema,
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "Abdullah Rawaa "

    @pytest.mark.parametrize("command", [["render"], ["render", "--each"]])
    def test_output_defaults_to_current_dir(
        self, command: list[str], make_text_file: MakeFile, xlsx_file: Path, output_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:  # fmt: skip
        template = make_text_file("r.txt", "x")
        output_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(output_dir)
        code, output = invoke(*command, "-t", template, "-d", xlsx_file)

        assert code == 0, output
        assert list(output_dir.glob("*.txt"))


# -----------------------
# errors
# -----------------------


class TestErrors:
    @pytest.mark.parametrize("command", [["render"], ["render", "--each"]])
    def test_unsupported_template_extension(
        self, command: list[str], make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.pdf", "x")
        code, output = invoke(*command, "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 2
        assert "not supported" in output

    def test_template_without_extension(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("Makefile", "x")
        code, output = invoke("render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir)

        assert code == 2
        assert "not supported" in output

    def test_template_not_found(self, xlsx_file: Path, tmp_path: Path, output_dir: Path) -> None:
        code, output = invoke(
            "render", "--each", "-t", tmp_path / "missing.txt", "-d", xlsx_file, "-o", output_dir
        )
        assert code == 2
        assert "does not exist" in output

    def test_template_is_directory(self, xlsx_file: Path, tmp_path: Path, output_dir: Path) -> None:
        folder = tmp_path / "folder.txt"
        folder.mkdir()
        code, _ = invoke("render", "--each", "-t", folder, "-d", xlsx_file, "-o", output_dir)
        assert code == 2

    def test_missing_required_template(self, xlsx_file: Path) -> None:
        code, output = invoke("render", "--each", "-d", xlsx_file)
        assert code == 2
        assert "--template" in output

    def test_text_template_syntax_error(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "{% if %}")
        code, output = invoke("render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir)
        assert code == 2
        assert "Template Error" in output

    def test_docx_template_syntax_error(
        self, make_docx: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_docx("t.docx", "{{ name ")
        code, output = invoke("render", "-t", template, "-d", xlsx_file, "-o", output_dir)
        assert code == 1  # a render failure, not a usage error
        assert "Template Error" in output

    def test_corrupted_docx_template(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.docx", "not a zip file")
        code, output = invoke("render", "--each", "-t", template, "-d", xlsx_file, "-o", output_dir)
        assert code == 2
        assert "Could not load template" in output

    def test_unsupported_data_extension(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("data.csv", "name\nRama")
        code, output = invoke("render", "--each", "-t", template, "-d", data, "-o", output_dir)
        assert code == 2
        assert "not supported" in output

    def test_malformed_data_file(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("data.json", '{"not": "a list"}')
        code, output = invoke("render", "--each", "-t", template, "-d", data, "-o", output_dir)
        assert code == 2
        assert "Could not read data file" in output

    def test_corrupted_xlsx(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "x")
        data = make_text_file("data.xlsx", "garbage")
        code, output = invoke("render", "--each", "-t", template, "-d", data, "-o", output_dir)
        assert code == 2
        assert "Could not read data file" in output

    def test_order_by_unknown_column(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render",
            "--each",
            "-t",
            template,
            "-d",
            xlsx_file,
            "--order",
            "salary",
            "-o",
            output_dir,
        )
        assert code == 2
        assert "salary" in output

    def test_invalid_filter_json(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, _ = invoke(
            "render",
            "--each",
            "-t",
            template,
            "-d",
            xlsx_file,
            "--filter",
            "{bad",
            "-o",
            output_dir,
        )
        assert code == 2

    def test_output_is_a_file(self, make_text_file: MakeFile, xlsx_file: Path) -> None:
        template = make_text_file("t.txt", "x")
        existing_file = make_text_file("out", "")
        code, _ = invoke("render", "--each", "-t", template, "-d", xlsx_file, "-o", existing_file)
        assert code == 2


# -----------------------
# schema templates
# -----------------------


@pytest.fixture
def answer(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Script the schemify questions: each `text` / `confirm` prompt pops the next answer."""

    def feed(*answers: Any) -> None:
        queue = list(answers)

        class Question:
            def unsafe_ask(self) -> Any:
                return queue.pop(0)

        for name in ("text", "confirm"):
            monkeypatch.setattr(questionary, name, lambda *_, **__: Question())

        monkeypatch.setattr(questionary, "print", lambda *_, **__: None)

    return feed


@pytest.fixture
def person_schema(make_text_file: MakeFile) -> Path:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }

    return make_text_file("person.schema.json", json.dumps(schema))


class TestJsonSchemaSource:
    def test_single_from_list(
        self, answer: Callable[..., None], person_schema: Path, make_text_file: MakeFile,
        output_dir: Path,
    ) -> None:  # fmt: skip
        answer("Rama", True, "Rawaa", False)  # noqa: FBT003 - name, add another?, name, add another?
        template = make_text_file("t.txt", "{% for p in people %}{{ p.name }};{% endfor %}")
        code, output = invoke(
            "render", "-s", person_schema, "-t", template, "-o", output_dir, "-v", "people",
            "-f", "out",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "out.txt").read_text() == "Rama;Rawaa;"

    def test_multiple_from_list(
        self, answer: Callable[..., None], person_schema: Path, make_text_file: MakeFile,
        output_dir: Path,
    ) -> None:  # fmt: skip
        answer("Rama", True, "Rawaa", False)  # noqa: FBT003
        template = make_text_file("t.txt", "Hello {{ name }}")
        code, output = invoke(
            "render", "--each", "-s", person_schema, "-t", template, "-o", output_dir, "-n", "name"
        )

        assert code == 0, output
        assert (output_dir / "Rama.txt").read_text() == "Hello Rama"
        assert (output_dir / "Rawaa.txt").read_text() == "Hello Rawaa"

    def test_object(
        self, answer: Callable[..., None], person_schema: Path, make_text_file: MakeFile,
        output_dir: Path,
    ) -> None:  # fmt: skip
        answer("Rama")
        template = make_text_file("t.txt", "Hello {{ object.name }}")
        code, output = invoke(
            "render", "--object", "-s", person_schema, "-t", template, "-o", output_dir
        )

        assert code == 0, output
        assert (output_dir / "t.txt").read_text() == "Hello Rama"

    def test_invalid_schema(self, make_text_file: MakeFile, output_dir: Path) -> None:
        schema = make_text_file("bad.json", "{not json")
        template = make_text_file("t.txt", "x")
        code, output = invoke("render", "--object", "-s", schema, "-t", template, "-o", output_dir)

        assert code == 2
        assert "Could not read schema file" in output


# -----------------------
# object template
# -----------------------


class TestObjectTemplate:
    def test_json_object(self, make_text_file: MakeFile, output_dir: Path) -> None:
        data = make_text_file("person.json", '{"name": "Rama", "age": 25}')
        template = make_text_file("t.txt", "{{ person.name }} is {{ person.age }}")
        code, output = invoke(
            "render",
            "--object",
            "-t",
            template,
            "-d",
            data,
            "-o",
            output_dir,
            "-v",
            "person",
            "-f",
            "out",
        )

        assert code == 0, output
        assert (output_dir / "out.txt").read_text() == "Rama is 25"

    def test_json_list_is_rejected(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render", "--object", "-t", template, "-d", json_file, "-o", output_dir
        )

        assert code == 2
        assert "must be an object" in output

    def test_xlsx_is_not_supported(
        self, make_text_file: MakeFile, xlsx_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render", "--object", "-t", template, "-d", xlsx_file, "-o", output_dir
        )

        assert code == 2
        assert "not supported" in output


@pytest.mark.parametrize("command", [["render"], ["render", "--each"], ["render", "--object"]])
def test_needs_exactly_one_data_source(
    command: list[str], make_text_file: MakeFile, person_schema: Path, output_dir: Path
) -> None:
    template = make_text_file("t.txt", "x")
    data = make_text_file("d.json", "[]")

    for sources in ((), ("-d", data, "-s", person_schema)):
        code, output = invoke(*command, "-t", template, "-o", output_dir, *sources)

        assert code == 2
        assert "exactly one data source" in output


# -----------------------
# render modes
# -----------------------


class TestRenderModes:
    def test_each_and_object_together(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render", "--each", "--object", "-t", template, "-d", json_file, "-o", output_dir
        )

        assert code == 2
        assert "can not be used together" in output

    @pytest.mark.parametrize(
        ("mode", "option", "message"),
        [
            ([], ["-n", "name"], "--name-by only works with --each"),
            (["--object"], ["--numbered"], "--numbered only works with --each"),
            (["--each"], ["-f", "out"], "--filename does not work with --each"),
            (["--each"], ["-v", "rows"], "--var does not work with --each"),
        ],
    )
    def test_option_in_wrong_mode(  # noqa: PLR0913, PLR0917
        self, mode: list[str], option: list[str], message: str, make_text_file: MakeFile,
        json_file: Path, output_dir: Path,
    ) -> None:  # fmt: skip
        if "--object" in mode:
            json_file = make_text_file("one.json", '{"name": "Rama"}')

        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render", *mode, *option, "-t", template, "-d", json_file, "-o", output_dir
        )

        assert code == 2
        assert message in output

    @pytest.mark.parametrize("option", [["--order", "name"], ["--group-by", "name"]])
    def test_data_options_rejected_with_object(
        self, option: list[str], make_text_file: MakeFile, output_dir: Path
    ) -> None:
        data = make_text_file("one.json", '{"name": "Rama"}')
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render", "--object", *option, "-t", template, "-d", data, "-o", output_dir
        )

        assert code == 2
        assert "do not work with --object" in output

    def test_default_vars(
        self, make_text_file: MakeFile, json_file: Path, output_dir: Path
    ) -> None:
        one = make_text_file("one.json", '{"name": "Rama"}')
        many = make_text_file("many.txt", "{{ objects | length }}")
        single = make_text_file("single.txt", "{{ object.name }}")

        assert invoke("render", "-t", many, "-d", json_file, "-o", output_dir)[0] == 0
        assert invoke("render", "--object", "-t", single, "-d", one, "-o", output_dir)[0] == 0
        assert (output_dir / "many.txt").read_text() == "3"
        assert (output_dir / "single.txt").read_text() == "Rama"

    def test_short_alias(self, make_text_file: MakeFile, json_file: Path, output_dir: Path) -> None:
        template = make_text_file("t.txt", "{{ objects | length }}")
        code, output = invoke("r", "-t", template, "-d", json_file, "-o", output_dir)

        assert code == 0, output
        assert (output_dir / "t.txt").read_text() == "3"


# -----------------------
# misc
# -----------------------


def test_help_lists_commands() -> None:
    code, output = invoke("--help")
    assert code == 0
    assert "render" in output
    assert "filters" in output

    for old_name in ("single-template", "multiple-templates", "object-template", "fjs"):
        assert old_name not in output


def test_filters_schema_lists_rules() -> None:
    code, output = invoke("filters")
    lines = {line.split()[0]: line for line in output.splitlines() if line.strip()}

    assert code == 0
    assert lines.keys() == {"Rule", *rules.rules}
    assert "key: string, value: list[string]" in lines["string__is_in"]
    assert "key: string, pattern: string" in lines["string__regex"]
    assert "key: string, value: date " in lines["date__ge"]
    assert "value: string | number" in " ".join(output.split())
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
            "render", "--each", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--group-by", "city", "-n", "city",
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
            "{% for g in objects %}{{ g.city }}:{% for p in g.people %} {{ p.name }}{% endfor %}\n"
            "{% endfor %}",
        )
        code, output = invoke(
            "render", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--order", "city", "--order", "-name",
            "--group-by", "city", "--items-var", "people",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == (
            "Aleppo: Omar\nDamascus: Rawaa\nHoms: Rama Abdullah\n"
        )

    def test_groups_after_filtering(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "{% for g in objects %}{{ g.city }};{% endfor %}")
        code, output = invoke(
            "render", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--filter", filter_eq("city", "Homs"), "--group-by", "city",
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "Homs;"

    def test_unknown_group_key(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render",
            "--each",
            "-t",
            template,
            "-d",
            employees_xlsx,
            "--group-by",
            "country",
            "-o",
            output_dir,
        )
        assert code == 2
        assert "country" in output

    def test_group_key_clashes_with_items(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("t.txt", "x")
        code, output = invoke(
            "render",
            "--each",
            "-t",
            template,
            "-d",
            employees_xlsx,
            "--group-by",
            "city",
            "--items-var",
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
            "render", "--each", "-t", template, "-d", data, "--group-by", "tags", "-o", output_dir
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
        template = make_text_file("r.txt", "{% for p in objects %}{{ p.name }};{% endfor %}")
        not_empty = json.dumps(
            {"name": "is_null", "args": ["joined"], "kwargs": {}, "inverse": True}
        )
        schema = f'{{"operator": "all", "expressions": [{not_empty}, {date_filter(rule, value)}]}}'
        code, output = invoke(
            "render", "-t", template, "-d", employees_xlsx, "-o", output_dir, "--filter", schema
        )

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "".join(f"{n};" for n in expected)

    def test_json_string_dates(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("r.txt", "{% for p in objects %}{{ p.name }}{% endfor %}")
        data = make_text_file(
            "d.json",
            '[{"name": "a", "joined": "2024-01-01"}, {"name": "b", "joined": "2025-01-01"}]',
        )
        code, output = invoke(
            "render", "-t", template, "-d", data, "-o", output_dir,
            "--filter", date_filter("date__gt", "2024-06-01"),
        )  # fmt: skip

        assert code == 0, output
        assert (output_dir / "r.txt").read_text() == "b"

    def test_empty_cell_gives_clear_error(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "x")
        code, output = invoke(
            "render", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--filter", date_filter("date__eq", "2024-01-01"),
        )  # fmt: skip
        assert code == 2
        assert "Filter failed on a data value" in output

    def test_invalid_filter_date(
        self, make_text_file: MakeFile, employees_xlsx: Path, output_dir: Path
    ) -> None:
        template = make_text_file("r.txt", "x")
        code, output = invoke(
            "render", "-t", template, "-d", employees_xlsx, "-o", output_dir,
            "--filter", date_filter("date__eq", "soon"),
        )  # fmt: skip
        assert code == 2
        assert "soon" in output
        assert "Filter failed on a data value" not in output


def test_main_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["templify", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
