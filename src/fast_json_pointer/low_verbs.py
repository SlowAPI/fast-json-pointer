from .exceptions import ActionError, ResolutionException
from .jsontypes import JsonType
from .resolver import JsonResolver


def get(doc: JsonType, path: JsonResolver) -> JsonType:
    result = path.resolve(doc)
    return result.value


def add(doc: JsonType, path: JsonResolver, value: JsonType) -> None:
    if path.is_index_ref:
        raise ActionError("Can't add to a relative json pointer")

    try:
        result = path.resolve(doc)
    except ResolutionException as e:
        if len(e.remaining) > 1:
            raise ActionError("Can't add object, path doesn't exist")

        parent = e.refs[-1].doc
        step = e.remaining[0].step
    else:
        parent = result.refs[-2].doc
        step = result.refs[-1].operation.step

    match parent:
        case dict():
            parent[step] = value

        case list() if step == "-":
            parent.append(value)

        case list():
            if step == "-":
                parent.append(value)
            else:
                part_idx = int(step)
                if len(parent) == part_idx:
                    parent.append(value)
                else:
                    parent[part_idx] = value

        case _:
            raise RuntimeError(f"Unnavigable type {type(parent)}")


def remove(doc: JsonType, path: JsonResolver) -> JsonType:
    result = path.resolve(doc)
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


def replace(doc: JsonType, path: JsonResolver, value: JsonType) -> JsonType:
    result = path.resolve(doc)
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


def move(doc: JsonType, path: JsonResolver, from_: JsonResolver) -> JsonType:
    obj = remove(doc, from_)
    add(doc, path, obj)
    return obj


def copy(doc: JsonType, path: JsonResolver, from_: JsonResolver) -> JsonType:
    obj = get(doc, from_)
    add(doc, path, obj)
    return obj


def test(doc: JsonType, path: JsonResolver, value: JsonType) -> bool:
    obj = get(doc, path)
    return obj == value
