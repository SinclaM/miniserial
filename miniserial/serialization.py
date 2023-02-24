from dataclasses import dataclass
from typing import NoReturn, Type, Any, Tuple
from functools import singledispatchmethod
from struct import pack, unpack

class _Serde():
    @singledispatchmethod
    def serialize(self, v) -> NoReturn:
        raise NotImplementedError(f"Cannot serialize value of type {type(v)}")

    @singledispatchmethod
    def deserialize(self, type_: Type, _: bytes) -> NoReturn:
        raise NotImplementedError(f"Cannot deserialize into type {type_}")

    @serialize.register
    def _(self, v: bool) -> bytes:
        return pack("<?", v)

    @deserialize.register
    def _(self, _: bool, b: bytes) -> Tuple[bool, bytes]:
        return unpack("<?", b[0:1])[0], b[1:]

    @serialize.register
    def _(self, v: int) -> bytes:
        return pack("<i", v)

    @deserialize.register
    def _(self, _: int, b: bytes) -> Tuple[int, bytes]:
        return unpack("<i", b[0:4])[0], b[4:]

    @serialize.register
    def _(self, v: float) -> bytes:
        return pack("<f", v)

    @deserialize.register
    def _(self, _: float, b: bytes) -> Tuple[float, bytes]:
        return unpack("<f", b[0:4])[0], b[4:]

    @serialize.register
    def _(self, v: str) -> bytes:
        return v.encode() + b"\x00"

    @deserialize.register
    def _(self, _: str, b: bytes) -> Tuple[str, bytes]:
        return b[:b.index(b"\x00")].decode(), b[b.index(b"\x00") + 1:]

_serde = _Serde()

def serializable(cls):
    @dataclass
    class wrapper:
        def __init__(self, *args):
            self.wrapped = cls(*args)
        def __getattr__(self, *args):
            return getattr(self.wrapped, *args)
        def serialize(self) -> bytes:
            return b"".join([_serde.serialize(v) for v in vars(self.wrapped).values()])

        @staticmethod
        def deserialize(b: bytes, reference: cls):
            fields: dict[str, Any] = vars(reference.wrapped)
            params: dict[str, Any] = {}

            remaining = b
            for field in fields.keys():
                v, remaining = _serde.deserialize(getattr(reference, field), remaining)
                params[field] = v
            return wrapper(*params)

    return wrapper