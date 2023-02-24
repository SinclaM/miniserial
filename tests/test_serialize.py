from __future__ import annotations
import unittest
from struct import pack
from dataclasses import dataclass

from miniserial import serializable

ref: Foo

@serializable(reference=lambda: ref)
@dataclass
class Foo():
    x: int
    y: float
    z: str
    b: bool

    def serialize(self): ...

    @classmethod
    def deserialize(cls, *_): ...

ref = Foo(4, 8.0, "ref", False)

class SerializaitonTests(unittest.TestCase):
    def test_serialize(self) -> None:
        f = Foo(1, 2.0, "hello", True)

        serialized = pack("<i", f.x) + pack("<f", f.y) + f.z.encode() + b"\x00" + pack("<?", f.b)
        self.assertEqual(f.serialize(), serialized)
        self.assertEqual(Foo.deserialize(serialized), f)
