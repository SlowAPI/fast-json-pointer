from dataclasses import dataclass
from typing import *

from .exceptions import (
    CompilationException,
    EndOfArrayException,
    ParseException,
    ResolutionException,
)
from .jsontypes import JsonType
from .pointer import JsonPointer, RelativeJsonPointer


@dataclass
class Start:
    pass


@dataclass
class DoUp:
    n: int


@dataclass
class DoIndex:
    pass


@dataclass
class DoStep:
    step: str


Operation = Start | DoUp | DoIndex | DoStep


@dataclass
class JsonRef:
    doc: JsonType
    operation: Operation


@dataclass
class ResolveResult:
    refs: list[JsonRef]
    value: JsonType
    is_index_result: bool = False


def resolve(doc: JsonType, operations: list[Operation]) -> ResolveResult:
    '''

    >>> resolve({'foo': 1}, [Start(), DoStep('foo'), DoIndex(), DoIndex()])
    Traceback (most recent call last):
    fast_json_pointer.exceptions.ResolutionException: ...
    """
    '''
    cur_doc = doc
    refs: list[JsonRef] = [JsonRef(doc, Start())]

    if len(operations) == 0:
        return ResolveResult(refs, doc)

    last_op = operations[-1]

    for idx, op in enumerate(operations):
        match op:
            case DoUp(n):
                if n > 0:
                    refs = refs[:-n]
                    cur_doc = refs[-1].doc

            case DoStep(step):
                match cur_doc:
                    case dict():
                        if step not in cur_doc:
                            raise ResolutionException(
                                f"Key '{step}' not in JSON object",
                                refs=refs,
                                remaining=operations[idx:],
                            )

                        cur_doc = cur_doc[step]
                        refs.append(JsonRef(cur_doc, op))

                    case list():
                        if step == "-":
                            raise EndOfArrayException(
                                "Hit '-' (end of array) token",
                                refs=refs,
                                remaining=operations[idx:],
                            )

                        part_idx = int(step)
                        if part_idx >= len(cur_doc):
                            raise ResolutionException(
                                f"Index '{part_idx}' not in JSON array",
                                refs=refs,
                                remaining=operations[idx:],
                            )

                        cur_doc = cur_doc[part_idx]
                        refs.append(JsonRef(cur_doc, op))

                    case _:
                        raise ResolutionException(
                            f"Unnvaigable doc type '{type(step)}'",
                            refs=refs,
                            remaining=operations[idx:],
                        )

            case DoIndex():
                if op is not last_op:
                    raise ResolutionException(
                        f"Can't do 'index of' as anything other than the last operation",
                        refs=refs,
                        remaining=operations[idx:],
                    )

                return ResolveResult(
                    refs=refs, value=refs[-1].operation.step, is_index_result=True
                )

    return ResolveResult(refs, value=cur_doc)


@dataclass
class JsonResolver:
    operations: list[Operation]
    is_index_ref: bool

    @classmethod
    def compile(cls, *pointers: str | JsonPointer | RelativeJsonPointer) -> Self:
        ops = compile(*pointers)
        is_index_ref = isinstance(ops[-1], DoIndex) if ops else False

        return cls(ops, is_index_ref)

    def resolve(self, doc: JsonType) -> ResolveResult:
        return resolve(doc, self.operations)


def compile(*pointers: str | JsonPointer | RelativeJsonPointer) -> list[Operation]:
    """Builds a compilation plan for resolving a series of json pointers.

    Assumes regular json pointers should be resolved as a relative pointer w/ an offset
    of zero

    >>> compile('/foo', '0#', '0/bar')
    Traceback (most recent call last):
    fast_json_pointer.exceptions.CompilationException: ...
    """

    operations = []

    for idx, ptr in enumerate(pointers):
        match ptr:
            case str():
                try:
                    massaged = RelativeJsonPointer.parse(ptr)
                except ParseException:
                    massaged = JsonPointer.parse(ptr)

            case _:
                massaged = ptr

        match massaged:
            case JsonPointer(parts):
                operations.extend(DoStep(part) for part in parts)

            case RelativeJsonPointer(up, pointer):
                if up > 0:
                    operations.append(DoUp(up))

                if pointer is not None:
                    operations.extend(DoStep(part) for part in pointer.parts)

                if massaged.is_index_ref:
                    if (idx + 1) != len(pointers):
                        raise CompilationException(
                            "Can't follow an 'index of' json pointer with further "
                            "json pointers"
                        )

                    operations.append(DoIndex())

    return operations
