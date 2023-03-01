import unittest
from struct import pack
from dataclasses import dataclass

from miniserial import Serializable

@dataclass
class Foo(Serializable):
    x: int
    y: float
    z: str
    b: bool

class SerializaitonTests(unittest.TestCase):
    def test_serialize(self) -> None:
        f = Foo(1, 2.0, "hello", True)

        serialized = pack("<i", f.x) + pack("<f", f.y) + f.z.encode() + b"\x00" + pack("<?", f.b)
        self.assertEqual(f.serialize(), serialized)
        self.assertEqual(Foo.deserialize(f.serialize()), f)
