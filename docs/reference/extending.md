# Extending templify

Each extension point is a registry filled with a decorator. Add your code, and the CLI picks it up automatically, including `--help` and the error messages. Data sources and filter rules live in [pyrecords](https://github.com/aaltatan/pyrecords), shared with other CLIs.

## A new data source

`pyrecords/readers.py`: a function that takes a path and returns a list of dicts, registered on `readers`. A reader for `render --object` returns one dict and is registered on `object_readers`.

```python
import csv


@readers.reader("csv")
def read_csv(filepath: Path) -> Data:
    with filepath.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
```

## A new template format

`src/templify/writers.py`: a class built from the template path that implements the `Writer` protocol, i.e. a `write(context, filepath)` method.

```python
class Writer(Protocol):
    def write(self, context: Context, filepath: Path) -> None: ...
```

Text-based formats can simply be added to `TextWriter`:

```python
@writers.writer("txt", "md", "html", "htm", "xml", "csv")
class TextWriter: ...
```

A format with its own engine gets its own class:

```python
@writers.writer("pptx")
class PptxWriter:
    def __init__(self, template_path: Path) -> None:
        self.template_path = template_path

    def write(
        self, context: Context, filepath: Path
    ) -> None: ...  # render context into the template and save to filepath
```

A format that needs validation can extend `TextWriter` and override `render`, the way `JsonWriter` does.

## A new store

`src/templify/stores.py`: a class built from `(path, table, columns)` that implements the `Store` protocol (`init`, `add`, `all`, `get`, `update`, `delete`, `migrate`), registered on `stores`. `columns` are `Column(name, type, format)` from the schema's top-level properties. File-based stores can extend `_FileStore` and only read and save the rows, the way `JsonStore` does:

```python
@stores.store("csv")
class CsvStore(_FileStore):
    native_json = False  # nested values as JSON text

    def _rows(self) -> list[dict[str, Any]]: ...  # read every row

    def _save(self, rows: list[dict[str, Any]]) -> None: ...  # write every row
```

## A new filter rule

`pyrecords/filter_rules.py`: the first two parameters are the row and the column. A `Process` marker on a parameter converts the value coming from the filter JSON.

```python
@rules.rule()
def float__between(d: dict[str, Any], key: str, low: FloatValue, high: FloatValue) -> bool:
    return low <= d[key] <= high
```

```bash
--filter '{"name": "float__between", "args": ["salary", 1200, 1600], "kwargs": {}, "inverse": false}'
```


## Where your code goes

Data sources and filter rules live in [pyrecords](https://github.com/aaltatan/pyrecords),
which templify shares with other CLIs such as [qrbar-cli](https://github.com/aaltatan/qrbar-cli).
A reader or rule added there works in all of them. Writers and stores live in templify itself.
