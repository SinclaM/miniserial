from __future__ import annotations
from dataclasses import dataclass, fields
from typing import Any, Tuple, TypeVar
from struct import pack, unpack

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
    else:
        raise Exception(f"Unknown type: {type(v)}")

    return out

def _deserialize(type_: T, b: bytes) -> Tuple[T, bytes]:
    result: T
    remaining: bytes

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
        result = b[:b.index(b"\x00")].decode() #type: ignore
        remaining = b[b.index(b"\x00") + 1:]
    else:
        raise Exception(f"Unknown type: {type_}")

    return result, remaining

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
