from typing import cast, get_type_hints, Type
from dataclasses import fields
from typing import Any, Tuple, TypeVar
from struct import pack, unpack
from typing_inspect import get_args, get_origin

T = TypeVar("T")

def _serialize(v) -> bytes:
    out: bytes

    if isinstance(v, bool):
        out =  pack("<?", v)
    elif isinstance(v, int):
        out =  pack("<i", v)
    elif isinstance(v, float):
        out =  pack("<f", v)
    elif isinstance(v, str):
        out = v.encode() + b"\x00"
    elif isinstance(v, list):
        out = pack("<I", len(v))
        for x in v:
            out += _serialize(x)
    elif hasattr(v, "serialize"):
        out = v.serialize()
    else:
        raise Exception(f"Unknown type: {type(v)}")

    return out

def _deserialize(type_: T, b: bytes) -> Tuple[T, bytes]:
    if type_ is bool:
        result = unpack("<?", b[0:1])[0]
        remaining = b[1:]
    elif type_ is int:
        result = unpack("<i", b[0:4])[0]
        remaining = b[4:]
    elif type_ is float:
        result = unpack("<f", b[0:4])[0]
        remaining = b[4:]
    elif type_ is str:
        i = b.index(b"\x00")
        result = b[:i].decode()
        remaining = b[i + 1:]
    elif get_origin(type_) is list:
        args = get_args(type_)
        len_ = unpack("<I", b[0:4])[0]
        result = []
        remaining = b[4:]
        for _ in range(len_):
            v, remaining = _deserialize(args[0], remaining)
            result.append(v)
    elif hasattr(type_, "_partial_deserialize"):
        result, remaining = type_._partial_deserialize(b) #type: ignore
    else:
        raise Exception(f"Unknown type: {type_}")

    return cast(T, result), remaining

class Serializable():
    def serialize(self) -> bytes:
        return b"".join([_serialize(v) for v in vars(self).values()])

    @classmethod
    def _partial_deserialize(cls: Type[T], b: bytes) -> Tuple[T, bytes]:
        params: dict[str, Any] = {}

        # Type hints must be gathered from typing.get_type_hints instead of
        # from dataclasses.fields. Types given in the latter are not resolved
        # if postponed annotation evaluation is enabled (through `from __future__
        # import annotations`) and are simply strings.
        resolved = get_type_hints(cls)

        remaining = b
        for field in fields(cls):
            v, remaining = _deserialize(resolved[field.name], remaining)
            params[field.name] = v
        return cls(**params), remaining #type: ignore

    @classmethod
    def deserialize(cls: Type[T], b: bytes) -> T:
        return cls._partial_deserialize(b)[0] # type: ignore
