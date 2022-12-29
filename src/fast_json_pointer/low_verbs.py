from dataclasses import dataclass
from typing import *

from .exceptions import (CompilationException, EndOfArrayException,
                         ParseException, ResolutionException)
from .jsontypes import JsonType
from .resolver import Operation, resolve


def get(doc: JsonType, path: list[Operation]) -> JsonType:
    result = resolve(doc, path)
    return result.value


def _set_ref(doc: JsonType, part: str, value: JsonType) -> None:
    match doc:
        case dict():
            doc[part] = value

        case list() if part == "-":
            doc.append(value)

        case list():
            part_idx = int(part)
            if len(doc) == part_idx:
                doc.append(value)
            else:
                doc[part_idx] = value
        case _:
            raise RuntimeError(f"Unnavigable type {type(doc)}")


def add(doc: JsonType, path: list[Operation], value: JsonType) -> None:
    try:
        result = resolve(doc, path)
        if result.is_index_result:
            raise RuntimeError()
    except ResolutionException as e:
        if len(e.remaining) > 1:
            raise RuntimeError("Can't ")

        if len(e.remaining) == 0:
            raise RuntimeError()

        _set_ref(e.refs[-1].doc, e.remaining[0].step, value)
    else:

        _set_ref(result.refs[-2].doc, result.refs[-1].operation.step, value)


def remove(doc: JsonType, path: list[Operation]) -> JsonType:
    result = resolve(doc, path)
    parent, last = result.refs[-2:]

    part = last.operation.step

    match parent.doc:
        case dict():
            del parent.doc[part]
        case list():
            del parent.doc[int(part)]
        case _:
            raise RuntimeError()

    return result.value


def replace(doc: JsonType, path: list[Operation], value: JsonType) -> JsonType:
    result = resolve(doc, path)
    parent, last = result.refs[-2:]

    part = last.operation.step

    match parent.doc:
        case dict():
            parent.doc[part] = value
        case list():
            parent.doc[int(part)] = value
        case _:
            raise RuntimeError()

    return result.value


def move(doc: JsonType, path: list[Operation], from_: list[Operation]) -> None:
    obj = remove(doc, from_)
    add(doc, path, obj)


def copy(doc: JsonType, path: list[Operation], from_: list[Operation]) -> None:
    obj = get(doc, from_)
    add(doc, path, obj)


def test(doc: JsonType, path: list[Operation], value: JsonType) -> bool:
    obj = get(doc, path)
    return obj == value
