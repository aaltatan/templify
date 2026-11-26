"""Run every `templify` command in the docs' bash blocks against a copy of `examples/`."""

import re
import shlex
import shutil
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from templify.cli.cli import app

ROOT = Path(__file__).parent.parent

PAGES = sorted((ROOT / "docs").rglob("*.md"))

# docs indent code blocks inside tabs and admonitions, so the fence may be indented
FENCE = re.compile(r"^([ \t]*)```bash\n(.*?)^\1```", re.DOTALL | re.MULTILINE)


def commands(block: str) -> list[list[str]]:
    """Split a bash block into commands, joining backslash continuations and open quotes."""
    found: list[list[str]] = []

    buffer = ""

    for line in block.splitlines():
        buffer += line.removesuffix("\\") + "\n"

        if line.endswith("\\"):
            continue

        try:
            words = shlex.split(buffer, comments=True)

        except ValueError:  # a quote is still open
            continue

        buffer = ""

        if words and words[0] == "templify":
            found.append(words)

    assert not buffer.strip(), f"unfinished command: {buffer}"

    return found


BLOCKS = [
    (f"{page.relative_to(ROOT / 'docs').as_posix()}:{number}", found)
    for page in PAGES
    for number, (_, block) in enumerate(FENCE.findall(page.read_text(encoding="utf-8")), 1)
    if (found := commands(textwrap.dedent(block)))
]


def test_the_docs_have_commands() -> None:
    assert sum(len(found) for _, found in BLOCKS) > 60


@pytest.mark.parametrize("block", [found for _, found in BLOCKS], ids=[i for i, _ in BLOCKS])
def test_docs_block(
    block: list[list[str]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The commands of one block run in order, in one folder, like a user would type them."""
    shutil.copytree(ROOT / "examples", tmp_path, dirs_exist_ok=True)

    monkeypatch.chdir(tmp_path)

    for words in block:
        result = CliRunner().invoke(app, words[1:])

        assert result.exit_code == 0, f"{shlex.join(words)}\n{result.output}"
