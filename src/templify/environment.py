"""The Jinja environment every template renders in: sandboxed, with the jinja-types filters.

jinja-types adds Python's type methods as qualified filters and tests (`str.zfill`,
`decimal.quantize`, `date.strftime`, `ar.to_words`, ...); its catalog drives the `types`
command and the "did you mean" hints for misspelled names.
"""

import re
from difflib import get_close_matches
from functools import cache
from typing import Any

from jinja2 import TemplateError
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja_types import Catalog, Registry, TypesExtension

_UNKNOWN = re.compile(r"No (filter|test) named '([^']+)'")


def environment(**options: Any) -> ImmutableSandboxedEnvironment:
    """Return a sandboxed environment with jinja-types, `options` go to the environment."""
    return ImmutableSandboxedEnvironment(extensions=[TypesExtension], **options)


@cache
def catalog() -> Catalog:
    """Every jinja-types filter, test and global."""
    return Registry.default().catalog()


def describe(error: TemplateError) -> str:
    """Return the error message, with close matches when a filter or test name is unknown."""
    message = str(error)
    unknown = _UNKNOWN.search(message)

    if unknown is None:
        return message

    kind, name = unknown.groups()
    names = [entry.name for entry in catalog().select(kind=kind)]
    matches = get_close_matches(name, names, n=3)

    if matches:
        return f"{message} Did you mean: {', '.join(matches)}?"

    return f"{message} See `templify types` for every {kind}."
