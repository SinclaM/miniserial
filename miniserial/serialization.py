from typing import cast
from dataclasses import fields
from typing import Any, Tuple, TypeVar
from struct import pack, unpack
from typing_inspect import get_args, get_origin

# TODO: why does `from __future__ import annotations` break things
# when used in the same file as a class definiton that uses the
# `Serializable` mixin?

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
    else:
        raise Exception(f"Unknown type: {type_}")

    return cast(T, result), remaining

class Serializable():
    def serialize(self) -> bytes:
        return b"".join([_serialize(v) for v in vars(self).values()])

    @classmethod
    def deserialize(cls, b: bytes):
        params: dict[str, Any] = {}

        remaining = b
        for field in fields(cls):
            v, remaining = _deserialize(field.type, remaining)
            params[field.name] = v
        return cls(**params) #type: ignore
