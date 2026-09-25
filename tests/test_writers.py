import json
from pathlib import Path

import pytest
from jinja2 import TemplateSyntaxError, UndefinedError
from templify.models import Data
from templify.writers import (
    Context,
    DocxWriter,
    InvalidOutputError,
    JsonWriter,
    TemplateExtensionNotSupportedError,
    TextWriter,
    Writer,
    WriterRegistry,
    _get_filename,
    write_multiple,
    write_single,
    writers,
)

from .conftest import MakeFile, read_docx

# -----------------------
# registry
# -----------------------


class TestRegistry:
    @pytest.mark.parametrize(
        ("extension", "writer_cls"),
        [
            ("docx", DocxWriter),
            ("txt", TextWriter),
            ("md", TextWriter),
            ("html", TextWriter),
            ("htm", TextWriter),
            ("json", JsonWriter),
        ],
    )
    def test_picks_writer_by_extension(self, extension: str, writer_cls: type) -> None:
        assert writers[extension] is writer_cls

    def test_extension_is_case_insensitive(self) -> None:
        assert "TXT" in writers
        assert writers["Docx"] is DocxWriter

    @pytest.mark.parametrize("extension", ["pdf", "xlsx", "", "doc", "xml", "csv", "yaml"])
    def test_unsupported_extension_raises(self, extension: str) -> None:
        assert extension not in writers
        with pytest.raises(TemplateExtensionNotSupportedError):
            writers[extension]

    def test_create_uses_template_suffix(self, make_text_file: MakeFile) -> None:
        template = make_text_file("letter.TXT", "hi")
        assert isinstance(writers.create(template), TextWriter)

    def test_register_custom_writer(self, tmp_path: Path) -> None:
        registry = WriterRegistry()

        @registry.writer("upper", "up")
        class UpperWriter:
            def __init__(self, template_path: Path) -> None:
                self.text = template_path.read_text()

            def write(self, context: Context, filepath: Path) -> None:
                filepath.write_text(self.text.format(**context).upper())

        template = tmp_path / "t.upper"
        template.write_text("hello {name}")

        writer = registry.create(template)
        writer.write({"name": "rama"}, tmp_path / "out.upper")

        assert registry.extensions == ["up", "upper"]
        assert (tmp_path / "out.upper").read_text() == "HELLO RAMA"

    def test_concrete_writers_satisfy_protocol(self, make_text_file: MakeFile) -> None:
        writer: Writer = TextWriter(make_text_file("t.txt", ""))
        assert callable(writer.write)


# -----------------------
# concrete writers
# -----------------------


class TestTextWriter:
    def test_renders_variables(self, make_text_file: MakeFile, tmp_path: Path) -> None:
        writer = TextWriter(make_text_file("t.txt", "Hello {{ name }}, age {{ age }}"))
        out = tmp_path / "out.txt"
        writer.write({"name": "Rama", "age": 25}, out)
        assert out.read_text(encoding="utf-8") == "Hello Rama, age 25"

    def test_keeps_trailing_newline(self, make_text_file: MakeFile, tmp_path: Path) -> None:
        writer = TextWriter(make_text_file("t.txt", "line\n"))
        out = tmp_path / "out.txt"
        writer.write({}, out)
        assert out.read_bytes() == b"line\n"

    def test_unicode(self, make_text_file: MakeFile, tmp_path: Path) -> None:
        writer = TextWriter(make_text_file("t.md", "# مرحبا {{ name }}"))
        out = tmp_path / "out.md"
        writer.write({"name": "رهف"}, out)
        assert out.read_text(encoding="utf-8") == "# مرحبا رهف"

    def test_missing_variable_renders_empty(self, make_text_file: MakeFile) -> None:
        writer = TextWriter(make_text_file("t.txt", "[{{ missing }}]"))
        assert writer.render({}) == "[]"

    def test_supports_include(self, make_text_file: MakeFile) -> None:
        make_text_file("header.txt", "HEADER")
        writer = TextWriter(make_text_file("t.txt", "{% include 'header.txt' %}|{{ x }}"))
        assert writer.render({"x": 1}) == "HEADER|1"

    def test_syntax_error_raised_at_load(self, make_text_file: MakeFile) -> None:
        with pytest.raises(TemplateSyntaxError):
            TextWriter(make_text_file("t.txt", "{% for x in %}"))

    def test_runtime_error_raised_at_write(self, make_text_file: MakeFile, tmp_path: Path) -> None:
        writer = TextWriter(make_text_file("t.txt", "{{ person.name.first }}"))
        with pytest.raises(UndefinedError):
            writer.write({}, tmp_path / "out.txt")

    def test_html_is_not_escaped(self, make_text_file: MakeFile) -> None:
        writer = TextWriter(make_text_file("t.html", "<p>{{ body }}</p>"))
        assert writer.render({"body": "<b>hi</b>"}) == "<p><b>hi</b></p>"


class TestJsonWriter:
    def test_writes_valid_json(self, make_text_file: MakeFile, tmp_path: Path) -> None:
        writer = JsonWriter(make_text_file("t.json", '{"name": "{{ name }}", "age": {{ age }}}'))
        out = tmp_path / "out.json"
        writer.write({"name": "Rama", "age": 25}, out)
        assert json.loads(out.read_text()) == {"name": "Rama", "age": 25}

    def test_tojson_filter_escapes_values(self, make_text_file: MakeFile) -> None:
        writer = JsonWriter(make_text_file("t.json", '{"quote": {{ quote | tojson }}}'))
        content = writer.render({"quote": 'He said "hi"'})
        assert json.loads(content) == {"quote": 'He said "hi"'}

    def test_invalid_output_raises_and_writes_nothing(
        self, make_text_file: MakeFile, tmp_path: Path
    ) -> None:
        writer = JsonWriter(make_text_file("t.json", '{"name": "{{ name }}"}'))
        out = tmp_path / "out.json"
        with pytest.raises(InvalidOutputError, match="not valid JSON"):
            writer.write({"name": 'Ra"ma'}, out)
        assert not out.exists()


class TestDocxWriter:
    def test_renders_variables(self, make_docx: MakeFile, tmp_path: Path) -> None:
        writer = DocxWriter(make_docx("t.docx", "Hello {{ name }}"))
        out = tmp_path / "out.docx"
        writer.write({"name": "Rama"}, out)
        assert read_docx(out) == "Hello Rama"

    def test_can_render_many_times(self, make_docx: MakeFile, tmp_path: Path) -> None:
        writer = DocxWriter(make_docx("t.docx", "Hello {{ name }}"))
        for name in ("A", "B"):
            writer.write({"name": name}, tmp_path / f"{name}.docx")
        assert read_docx(tmp_path / "A.docx") == "Hello A"
        assert read_docx(tmp_path / "B.docx") == "Hello B"

    def test_syntax_error_raised_at_write(self, make_docx: MakeFile, tmp_path: Path) -> None:
        writer = DocxWriter(make_docx("t.docx", "{% for x in %}"))
        with pytest.raises(TemplateSyntaxError):
            writer.write({}, tmp_path / "out.docx")


# -----------------------
# filenames
# -----------------------


class TestGetFilename:
    def test_default_uses_index(self) -> None:
        assert _get_filename({"name": "Rama"}, 3) == "template-3"

    def test_uses_key(self) -> None:
        assert _get_filename({"name": "Rama"}, 3, "name") == "Rama"

    def test_uses_key_with_index(self) -> None:
        assert _get_filename({"name": "Rama"}, 3, "name", include_index=True) == "3 - Rama"

    def test_missing_key_falls_back(self) -> None:
        assert _get_filename({"name": "Rama"}, 3, "id") == "template-3"

    @pytest.mark.parametrize("value", [None, "", "   ", "..."])
    def test_empty_value_falls_back(self, value: str | None) -> None:
        assert _get_filename({"name": value}, 1, "name") == "template-1"

    def test_non_string_value(self) -> None:
        assert _get_filename({"id": 42}, 1, "id") == "42"

    def test_invalid_chars_are_replaced(self) -> None:
        assert _get_filename({"name": 'a/b\\c:d*e?"f<g>h|i'}, 1, "name") == "a_b_c_d_e__f_g_h_i"


# -----------------------
# write modes
# -----------------------


class TestWriteSingle:
    def test_writes_one_file_with_all_data(
        self, make_text_file: MakeFile, output_dir: Path, people: Data
    ) -> None:
        template = make_text_file("t.txt", "{% for p in data %}{{ p.name }};{% endfor %}")
        path = write_single(
            TextWriter(template), people, output_dir=output_dir, filename="report", extension="txt"
        )
        assert path == output_dir / "report.txt"
        assert path.read_text() == "Abdullah;Rawaa;Rama;"

    def test_custom_data_variable(
        self, make_text_file: MakeFile, output_dir: Path, people: Data
    ) -> None:
        template = make_text_file("t.txt", "{{ rows | length }}")
        path = write_single(
            TextWriter(template),
            people,
            output_dir=output_dir,
            filename="r",
            extension="txt",
            data_variable="rows",
        )
        assert path.read_text() == "3"

    def test_additional_context(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "a{{ new_line }}b{{ tab }}c{{ page_break }}")
        path = write_single(
            TextWriter(template), [], output_dir=output_dir, filename="r", extension="txt"
        )
        assert path.read_text() == "a\nb\tc\f"

    def test_empty_data(self, make_text_file: MakeFile, output_dir: Path) -> None:
        template = make_text_file("t.txt", "{% for p in data %}x{% else %}empty{% endfor %}")
        path = write_single(
            TextWriter(template), [], output_dir=output_dir, filename="r", extension="txt"
        )
        assert path.read_text() == "empty"

    def test_creates_nested_output_dir(self, make_text_file: MakeFile, output_dir: Path) -> None:
        nested = output_dir / "a" / "b"
        path = write_single(
            TextWriter(make_text_file("t.txt", "x")),
            [],
            output_dir=nested,
            filename="r",
            extension="txt",
        )
        assert path.parent == nested

    def test_never_overwrites_existing_file(
        self, make_text_file: MakeFile, output_dir: Path
    ) -> None:
        output_dir.mkdir()
        (output_dir / "r.txt").write_text("old")
        path = write_single(
            TextWriter(make_text_file("t.txt", "new")),
            [],
            output_dir=output_dir,
            filename="r",
            extension="txt",
        )
        assert path != output_dir / "r.txt"
        assert path.name.startswith("r-")
        assert (output_dir / "r.txt").read_text() == "old"
        assert path.read_text() == "new"


class TestWriteMultiple:
    def test_writes_one_file_per_item(
        self, make_text_file: MakeFile, output_dir: Path, people: Data
    ) -> None:
        writer = TextWriter(make_text_file("t.txt", "{{ name }} is {{ age }}"))
        paths = list(
            write_multiple(
                writer, people, output_dir=output_dir, extension="txt", filename_key="name"
            )
        )
        assert [p.name for p in paths] == ["Abdullah.txt", "Rawaa.txt", "Rama.txt"]
        assert paths[2].read_text() == "Rama is 25"

    def test_is_lazy(self, make_text_file: MakeFile, output_dir: Path, people: Data) -> None:
        writer = TextWriter(make_text_file("t.txt", "x"))
        files = write_multiple(writer, people, output_dir=output_dir, extension="txt")
        assert not output_dir.exists()
        next(files)
        assert len(list(output_dir.iterdir())) == 1

    def test_default_names_and_index(
        self, make_text_file: MakeFile, output_dir: Path, people: Data
    ) -> None:
        writer = TextWriter(make_text_file("t.txt", "x"))
        names = [
            p.name for p in write_multiple(writer, people, output_dir=output_dir, extension="txt")
        ]
        assert names == ["template-1.txt", "template-2.txt", "template-3.txt"]

    def test_duplicate_keys_do_not_overwrite(
        self, make_text_file: MakeFile, output_dir: Path
    ) -> None:
        writer = TextWriter(make_text_file("t.txt", "{{ age }}"))
        data = [{"name": "Rama", "age": 1}, {"name": "Rama", "age": 2}]
        paths = list(
            write_multiple(
                writer, data, output_dir=output_dir, extension="txt", filename_key="name"
            )
        )
        assert len(set(paths)) == 2
        assert sorted(p.read_text() for p in paths) == ["1", "2"]

    def test_empty_data_writes_nothing(self, make_text_file: MakeFile, output_dir: Path) -> None:
        writer = TextWriter(make_text_file("t.txt", "x"))
        assert list(write_multiple(writer, [], output_dir=output_dir, extension="txt")) == []

    def test_builtin_context_wins_over_item_keys(
        self, make_text_file: MakeFile, output_dir: Path
    ) -> None:
        writer = TextWriter(make_text_file("t.txt", "[{{ tab }}]"))
        [path] = write_multiple(writer, [{"tab": "mine"}], output_dir=output_dir, extension="txt")
        assert path.read_text() == "[\t]"

    def test_docx(self, make_docx: MakeFile, output_dir: Path, people: Data) -> None:
        writer = DocxWriter(make_docx("t.docx", "Hello {{ name }}"))
        paths = list(
            write_multiple(
                writer,
                people,
                output_dir=output_dir,
                extension="docx",
                filename_key="name",
                include_index=True,
            )
        )
        assert paths[0].name == "1 - Abdullah.docx"
        assert read_docx(paths[1]) == "Hello Rawaa"
