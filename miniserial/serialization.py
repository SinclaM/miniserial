from __future__ import annotations
from typing import cast, get_type_hints
from typing import Type, Any, Tuple, TypeVar, Callable
from inspect import isclass
from collections.abc import Collection
from dataclasses import fields
from struct import pack, unpack
from abc import abstractmethod

from typing import get_args, get_origin

_T = TypeVar("_T")

_SerdeMap = dict[Type[_T], Tuple[Callable[[_T], bytes], Callable[[bytes], Tuple[_T, bytes]]]]

# type -> (serializer, deserializer) mapping for custom serializers
_serde: _SerdeMap = {}

def register_serializable(cls: Type[_T],
                          serializer: Callable[[_T], bytes],
                          deserializer: Callable[[bytes], Tuple[_T, bytes]]) -> None:
    """
    Register a custom (de)serialization mapping for a class `cls`.

    `serializer` is a function which takes instances of `cls` and returns `bytes`.

    `deserializer` is a function which takes `bytes` and returns a (`result`, `remaining`)
    tuple, where `result` a deserialized instance of `cls` and `remaining` is the
    `bytes` left.
    """
    _serde[cls] = serializer, deserializer

def _serialize(v) -> bytes:
    for cls, (serializer, _) in _serde.items():
        if isinstance(v, cls):
            return serializer(v)

    out: bytes

    if isinstance(v, bool):
        out =  pack("<?", v)
    elif isinstance(v, int):
        out =  pack("<i", v)
    elif isinstance(v, float):
        out =  pack("<f", v)
    elif isinstance(v, str):
        out = v.encode() + b"\x00"
    elif isinstance(v, dict):
        out = pack("<I", len(v))
        for k in v:
            out += _serialize(k)
            out += _serialize(v[k])
    elif isinstance(v, Collection):
        out = pack("<I", len(v))
        for x in v:
            out += _serialize(x)
    elif isinstance(v, Serializable):
        out = v.serialize()
    else:
        raise Exception(f"Unknown type: {type(v)}")

    return out

def _deserialize(cls: Type[_C], b: bytes) -> Tuple[_C, bytes]:
    for type_info, (_, deserializer) in _serde.items():
        if type_info is cls or get_origin(type_info) is cls:
            return deserializer(b)

    if cls is bool:
        result = unpack("<?", b[0:1])[0]
        remaining = b[1:]
    elif cls is int:
        result = unpack("<i", b[0:4])[0]
        remaining = b[4:]
    elif cls is float:
        result = unpack("<f", b[0:4])[0]
        remaining = b[4:]
    elif cls is str:
        i = b.index(b"\x00")
        result = b[:i].decode()
        remaining = b[i + 1:]
    elif get_origin(cls) is dict:
        key_type, val_type = get_args(cls)
        len_, = unpack("<I", b[0:4])
        result = {}
        remaining = b[4:]
        for _ in range(len_):
            key, remaining = _deserialize(key_type, remaining)
            val, remaining = _deserialize(val_type, remaining)
            result[key] = val
    elif isclass(origin := get_origin(cls)) and issubclass(origin, Collection):
        element_type, = get_args(cls)
        len_, = unpack("<I", b[0:4])
        result = []
        remaining = b[4:]
        for _ in range(len_):
            v, remaining = _deserialize(element_type, remaining)
            result.append(v)
        result = origin(result) #type: ignore
    elif isclass(cls) and issubclass(cls, Serializable):
        result, remaining = cls._partial_deserialize(b)
    else:
        raise Exception(f"Unknown type: {cls}")

    return cast(_C, result), remaining

class Serializable():
    @abstractmethod
    def __init__(self, *args, **kwargs) -> None: ...

    def serialize(self) -> bytes:
        """
        Serialize `self` into `bytes`.
        """
        return b"".join([_serialize(v) for v in vars(self).values()])

    @classmethod
    def _partial_deserialize(cls: Type[_C], serialized: bytes) -> Tuple[_C, bytes]:
        """
        Deserialize an instance of `cls` from `serialized` and also return the
        `bytes` remaining after the deserialization.
        """
        params: dict[str, Any] = {}

        # Type hints must be gathered from typing.get_type_hints instead of
        # from dataclasses.fields. Types given in the latter are not resolved
        # if postponed annotation evaluation is enabled (through `from __future__
        # import annotations`) and are simply strings.
        resolved = get_type_hints(cls)

        remaining = serialized
        for field in fields(cls):
            v, remaining = _deserialize(resolved[field.name], remaining)
            params[field.name] = v
        return cls(**params), remaining

    @classmethod
    def deserialize(cls: Type[_C], serialized: bytes) -> _C:
        """
        Deserialize an instance of `cls` from `serialized`.
        """
        return cls._partial_deserialize(serialized)[0]

_C = TypeVar("_C", bound=Serializable)

