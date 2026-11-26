# Development

```text
git clone https://github.com/aaltatan/templify
cd templify
uv sync
uv run pytest
uvx ruff check src tests
uvx ruff format src tests
uv run mypy
```

Coverage (lines and branches) is printed after every test run.

## Project structure

```text
src/templify/
├── environment.py       # the sandboxed Jinja environment with jinja-types
├── writers.py           # Writer protocol, WriterRegistry, Docx/Text/Json writers,
│                        #   write_single / write_multiple, file naming
├── stores.py            # Store protocol, StoreRegistry, sqlite/xlsx/json/jsonl stores
└── cli/
    ├── cli.py           # the commands
    ├── help.py          # long --help texts
    └── dependencies/
        ├── data.py      # -d, --order, --filter, --group-by pipeline
        ├── store.py     # -s + store PATH, store error reporting
        ├── template.py  # -t (picks the writer) and -o
        └── console.py   # rich console
examples/                # data and templates used by every command in the docs
tests/
├── test_writers.py
├── test_stores.py
├── test_cli.py          # end-to-end user scenarios
└── test_docs.py         # runs every command in the docs
```

## Documentation

This site is built with [MkDocs](https://www.mkdocs.org) and
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). The pages are in
`docs/`, and the navigation in `mkdocs.yml`.

```text
uv run --group docs mkdocs serve          # live preview on http://127.0.0.1:8000
uv run --group docs mkdocs build --strict # what CI runs: broken links fail the build
```

Every push to `main` builds the site and publishes it to GitHub Pages
(`.github/workflows/docs.yml`).

### Commands in the docs are tested

`tests/test_docs.py` runs every `templify` command in the ` ```bash ` blocks of
`docs/**/*.md` against a fresh copy of `examples/`. The commands of one block run in
order in the same folder, so a block can build on its own earlier lines (a
`store init` before a `store list`). So:

- commands in ` ```bash ` blocks must work from inside `examples/`;
- commands that need a person (`-s` without `--id`), a server, or another shell go in
  ` ```text ` or ` ```powershell ` blocks, which are not run.

### Generated reference pages

`docs/reference/filter-rules.md` and `docs/reference/types.md` list every filter rule
and type filter of the installed pyrecords and jinja-types. After upgrading either,
check `templify filters` and `templify types` against those pages.

### Demo GIFs

The GIFs in `docs/demo/` are recorded with [VHS](https://github.com/charmbracelet/vhs)
(`scoop install vhs` or `brew install vhs`) and PowerShell (`pwsh`), from the repository
root:

```text
vhs docs/demo/each.tape && vhs docs/demo/schema.tape && vhs docs/demo/schema-list.tape
```

## Releasing

Push a `v*` tag. The release workflow builds the package, publishes it to PyPI with
trusted publishing, and creates a GitHub release.

## License

templify is free software, released under the
[GNU General Public License v3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html).
