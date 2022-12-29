from . import low_verbs
from .jsontypes import JsonType
from .pointer import JsonPointer, RelativeJsonPointer
from .resolver import Operation, compile


def _compile(
    pointer: str | JsonPointer, rel: str | RelativeJsonPointer | None = None
) -> list[Operation]:
    if rel is not None:
        return compile(pointer, rel)
    else:
        return compile(pointer)


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
    >>> get([{'x': {'': 3}}, 4], JsonPointer.parse("/0/x"))
    {'': 3}

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
    path = _compile(pointer, rel)
    return low_verbs.get(doc, path)


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
    path = _compile(pointer, rel)
    return low_verbs.add(doc, path, value)


def remove(
    doc: JsonType,
    pointer: str | JsonPointer,
    *,
    rel: str | RelativeJsonPointer | None = None,
) -> JsonType:
    """
    >>> obj = {'x': 2}
    >>> remove(obj, "/x")
    2
    >>> obj
    {}

    >>> obj = {'x': [0, 1, 2]}
    >>> remove(obj, "/x", rel="0/2")
    2
    >>> obj
    {'x': [0, 1]}
    """
    path = _compile(pointer, rel)
    return low_verbs.remove(doc, path)


def replace(
    doc: JsonType,
    pointer: str | JsonPointer,
    value: JsonType,
    *,
    rel: str | RelativeJsonPointer | None = None,
) -> JsonType:
    """
    >>> obj = {'x': 2}
    >>> replace(obj, "/x", ['foo'])
    2
    >>> obj
    {'x': ['foo']}

    >>> obj = {'x': 2}
    >>> replace(obj, "", ['foo'], rel="0/x")
    2
    >>> obj
    {'x': ['foo']}

    >>> obj = [0, 1, 2]
    >>> replace(obj, "/2", 'foo')
    2
    >>> obj
    [0, 1, 'foo']
    """
    path = _compile(pointer, rel)
    return low_verbs.replace(doc, path, value)


def move(
    doc: JsonType,
    from_: str | JsonPointer,
    pointer: str | JsonPointer,
    *,
    rel: str | RelativeJsonPointer | None = None,
    from_rel: str | RelativeJsonPointer | None = None,
) -> None:
    """
    >>> obj = {'x': 2}
    >>> move(obj, "/x", "/y")
    >>> obj
    {'y': 2}
    """
    path = _compile(pointer, rel)
    from_path = _compile(from_, from_rel)
    return low_verbs.move(doc, path, from_path)


def copy(
    doc: JsonType,
    from_: str | JsonPointer,
    pointer: str | JsonPointer,
    *,
    rel: str | RelativeJsonPointer | None = None,
    from_rel: str | RelativeJsonPointer | None = None,
) -> None:
    """
    >>> obj = {'x': 2}
    >>> copy(obj, "/x", "/y")
    >>> obj
    {'x': 2, 'y': 2}
    """
    path = _compile(pointer, rel)
    from_path = _compile(from_, from_rel)
    return low_verbs.copy(doc, path, from_path)


def test(
    doc: JsonType,
    pointer: str | JsonPointer,
    value: JsonType,
    *,
    rel: str | RelativeJsonPointer | None = None,
) -> bool:
    """
    >>> obj = {'x': 2}
    >>> test(obj, "/x", 2)
    True
    """
    path = _compile(pointer, rel)
    return low_verbs.test(doc, path, value)
