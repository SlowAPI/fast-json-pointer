from dataclasses import dataclass, field
from typing import *

from .exceptions import EndOfArrayException, ResolutionException
from .pointer import JsonPointer, RelativeJsonPointer

JsonType = dict[str, "JsonType"] | list["JsonType"] | str | bool | int | float | None


@dataclass
class JsonRef:
    doc: JsonType
    pointer: JsonPointer


def _resolve_ref(doc: JsonType, part: str) -> JsonType:
    match doc:
        case dict():
            if part not in doc:
                raise ResolutionException(f"Key '{part}' not in JSON object")

            return doc[part]

        case list():
            if part == "-":
                raise EndOfArrayException("Hit '-' (end of array) token")

            part_idx = int(part)
            if part_idx >= len(doc):
                raise ResolutionException(f"Index '{part_idx}' not in JSON array")

            return doc[part_idx]

        case _:
            raise ResolutionException(f"Unnvaigable doc type '{type(part)}'")


def _resolve(doc: JsonType, pointer: JsonPointer, *, base_pointer: JsonPointer | None = None) -> list[JsonRef]:
    doc_pointer = JsonPointer([]) if base_pointer is None else base_pointer
    doc_refs = [JsonRef(doc, doc_pointer)]

    for idx, part in enumerate(pointer.parts):
        try:
            doc = _resolve_ref(doc, part)
        except Exception as e:
            raise ResolutionException(
                "Error resolving json pointer",
                doc_refs=doc_refs,
                remaining=pointer.parts[idx:],
            ) from e

        doc_pointer = JsonPointer([*doc_pointer.parts, part])
        doc_refs.append(JsonRef(doc, doc_pointer))

    return doc_refs



def resolve(
    doc: JsonType, pointer: JsonPointer, *, rel: RelativeJsonPointer | None = None
) -> list[JsonRef]:
    doc_refs = _resolve(doc, pointer)

    if rel:
        if rel.offset > 0:
            doc_refs = doc_refs[: -rel.offset]

        last_ref = doc_refs[-1]
        
        if rel.is_index_ref:
            return doc_refs + [JsonRef(last_ref.pointer.parts[-1], last_ref.pointer)]

        new_refs = _resolve(last_ref.doc, rel.pointer, base_pointer=last_ref.pointer)
        doc_refs.extend(new_refs)

    return doc_refs



def get(
    doc: JsonType,
    pointer: str | JsonPointer,
    *,
    rel: str | RelativeJsonPointer | None = None,
) -> JsonType:
    """

    >>> get({}, "")
    {}
    >>> get({'x': 5}, "/x")
    5
    >>> get({'x': {'': 3}}, "/x/")
    3
    >>> get({'x': {'': 3, 'z': 12}}, "/x/", rel="1/z")
    12
    >>> get({'x': {'': 3}, 'z': 12}, "/x/", rel="1#")
    'x'
    >>> get([{'x': {'': 3}}, 4], "/0/x", rel="1#")
    '0'

    Trying to get fields that don't exist is a bad idea...

    >>> get([{'x': {'': 3}}, 4], "/0/x", rel="0//does-not-exist")
    Traceback (most recent call last):
    fast_json_pointer.exceptions.ResolutionException: ...
    >>> get([{'x': {'': 3}}, 4], "/3")
    Traceback (most recent call last):
    fast_json_pointer.exceptions.ResolutionException: ...
    >>> get([{'x': {'': 3}}, 4], "/0/z")
    Traceback (most recent call last):
    fast_json_pointer.exceptions.ResolutionException: ...
    """
    match pointer:
        case str():
            pointer = JsonPointer.parse(pointer)

    match rel:
        case str():
            rel = RelativeJsonPointer.parse(rel)

    doc_refs = resolve(doc, pointer, rel=rel)

    return doc_refs[-1].doc


def _set_ref(doc: JsonType, part: str, value: JsonType) -> None:
    match doc:
        case dict():
            doc[part] = value
        case list():
            part_idx = int(part)
            if len(doc) == part_idx:
                doc.append(value)
            else:
                doc[part_idx] = value
        case _:
            raise RuntimeError(f"Unnavigable type {type(doc)}")


def add(
    doc: JsonType,
    pointer: str | JsonPointer,
    value: JsonType,
    *,
    rel: str | RelativeJsonPointer | None = None,
) -> None:
    """
    >>> obj = {}
    >>> add(obj, "/x", 2)
    >>> obj
    {'x': 2}

    >>> obj = {'x': 2}
    >>> add(obj, "", 'foo', rel="0/y")
    >>> obj
    {'x': 2, 'y': 'foo'}

    >>> obj = {'x': 2}
    >>> add(obj, "/x", 'foo', rel="1/x")
    >>> obj
    {'x': 'foo'}

    >>> obj = {'x': [0]}
    >>> add(obj, "/x", 'foo', rel="0/1")
    >>> obj
    {'x': [0, 'foo']}
    
    >>> obj = {'x': [0]}
    >>> add(obj, "/x", 'foo', rel="0/-")
    >>> obj
    {'x': [0, 'foo']}
    """

    match pointer:
        case str():
            pointer = JsonPointer.parse(pointer)

    match rel:
        case str():
            rel = RelativeJsonPointer.parse(rel)

    if rel and rel.is_index_ref:
        raise RuntimeError()

    try:
        doc_refs = resolve(doc, pointer, rel=rel)
        parent = doc_refs[-2].doc
        part = rel.pointer.parts[-1] if rel is not None else pointer.parts[-1]
    except ResolutionException as e:
        if len(e.remaining) > 1:
            raise

        parent = e.doc_refs[-1].doc
        part = e.remaining[0]

    _set_ref(parent, part, value)


def remove(doc, pointer: str | JsonPointer,  *, rel: str | RelativeJsonPointer | None = None) -> None:
    '''
    >>> obj = {'x': 2}
    >>> remove(obj, "/x")
    >>> obj
    {}

    >>> obj = {'x': [0, 1, 2]}
    >>> remove(obj, "/x", rel="0/2")
    >>> obj
    {'x': [0, 1]}
    '''
    match pointer:
        case str():
            pointer = JsonPointer.parse(pointer)

    match rel:
        case str():
            rel = RelativeJsonPointer.parse(rel)

    doc_refs = resolve(doc, pointer, rel=rel)
    parent = doc_refs[-2]
    last_ref = doc_refs[-1]

    part = last_ref.pointer.parts[-1]

    match parent.doc:
        case dict():
            del parent.doc[part]
        case list():
            del parent.doc[int(part)]
        case _:
            raise RuntimeError()
    

def replace(doc, pointer: str | JsonPointer, value: JsonType, *, rel: str | RelativeJsonPointer | None = None) -> None:
    '''
    >>> obj = {'x': 2}
    >>> replace(obj, "/x", ['foo'])
    >>> obj
    {'x': ['foo']}

    >>> obj = {'x': 2}
    >>> replace(obj, "", ['foo'], rel="0/x")
    >>> obj
    {'x': ['foo']}
    
    >>> obj = [0, 1, 2]
    >>> replace(obj, "/2", 'foo')
    >>> obj
    [0, 1, 'foo']
    '''
    
    match pointer:
        case str():
            pointer = JsonPointer.parse(pointer)

    match rel:
        case str():
            rel = RelativeJsonPointer.parse(rel)

    doc_refs = resolve(doc, pointer, rel=rel)
    parent = doc_refs[-2]
    last_ref = doc_refs[-1]

    part = last_ref.pointer.parts[-1]

    match parent.doc:
        case dict():
            parent.doc[part] = value
        case list():
            parent.doc[int(part)] = value
        case _:
            raise RuntimeError()


def move(doc, from_: str | JsonPointer, pointer: str | JsonPointer, *, rel: str | RelativeJsonPointer | None = None, from_rel: str | RelativeJsonPointer | None = None) -> None:
    '''
    >>> obj = {'x': 2}
    >>> move(obj, "/x", "/y")
    >>> obj
    {'y': 2}
    '''
    
    obj = get(doc, from_, rel=from_rel)
    remove(doc, from_, rel=from_rel)
    add(doc, pointer, obj, rel=rel)


def copy(doc, from_: str | JsonPointer, pointer: str | JsonPointer, *, rel: str | RelativeJsonPointer | None = None, from_rel: str | RelativeJsonPointer | None = None) -> None:
    '''
    >>> obj = {'x': 2}
    >>> copy(obj, "/x", "/y")
    >>> obj
    {'x': 2, 'y': 2}
    '''
    obj = get(doc, from_, rel=from_rel)
    add(doc, pointer, obj, rel=rel)


def test(doc, pointer: str | JsonPointer, value: JsonType, *, rel: str | RelativeJsonPointer | None = None) -> bool:
    '''
    >>> obj = {'x': 2}
    >>> test(obj, "/x", 2)
    True
    '''
    obj = get(doc, pointer, rel=rel)
    return obj == value