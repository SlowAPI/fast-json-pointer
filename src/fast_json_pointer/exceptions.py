from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .resolver import JsonPointer, JsonRef


class JsonPointerException(Exception):
    """Generic json pointer failure."""


class ParseException(JsonPointerException):
    """Failure occurred while parsing a json pointer."""


class ResolutionException(JsonPointerException):
    """Failure occurred while resolving a json pointer."""

    def __init__(self, *args, doc_refs: list[JsonRef], remaining) -> None:
        self.doc_refs = doc_refs
        self.remaining = remaining


class EndOfArrayException(ResolutionException):
    """Reference pointed to the end of a array."""
