"""Types shared by readers, transformers and writers."""

from typing import Any

type DataItem = dict[str, Any]
"""One record (a row), mapping column names to values."""

type Data = list[dict[str, Any]]
"""A list of records, as returned by a data reader."""
