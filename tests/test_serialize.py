from __future__ import annotations
from typing import Tuple
from struct import pack, unpack
from unittest import TestCase
from struct import pack
from dataclasses import dataclass

from miniserial import Serializable, register_serializable

@dataclass
class Foo(Serializable):
    x: int
    y: float
    z: str
    b: bool

@dataclass
class Bar(Serializable):
    x: int
    y: set[float]

@dataclass
class Baz(Serializable):
    x: bool
    y: dict[str, float]
    z: list[Bar]

@dataclass
class Person(Serializable):
    name   : str
    age    : int
    titles : list[str]
    balance: float

@dataclass
class Node(Serializable):
    value   : int
    children: list[Node]

@dataclass
class Qaz(Serializable):
    value: complex

class SerdeTests(TestCase):
    def test_simple(self) -> None:
        f = Foo(1, 2.0, "hello", True)

        serialized = pack("<i", f.x) + pack("<f", f.y) + f.z.encode() + b"\x00" + pack("<?", f.b)
        self.assertEqual(f.serialize(), serialized)
        self.assertEqual(Foo.deserialize(f.serialize()), f)

        b = Bar(11, {0.0, -1.0, 13.432})
        deserialized = Bar.deserialize(b.serialize())
        self.assertEqual(deserialized.x, b.x)
        for u, v in zip(deserialized.y, b.y):
            self.assertAlmostEqual(u, v, places=6)

        baz = Baz(True, {"some_key": 12.5, "another_key": 0.0}, [Bar(-200, set())])
        self.assertEqual(Baz.deserialize(baz.serialize()), baz)

        p = Person("Bob", 34, ["Mr.", "Dr.", "Professor"], 239847.25)
        self.assertEqual(Person.deserialize(p.serialize()), p)

    def test_tree(self) -> None:

        #                 1
        #               /   \ 
        #              2     3 
        #             / \
        #            4   5
        tree = Node(1, [Node(2, [Node(4, []), Node(5, [])]), Node(3, [])])
        self.assertEqual(Node.deserialize(tree.serialize()), tree)

    def test_custom(self) -> None:
        def custom_serializer(v: complex) -> bytes:
            return pack("<f", v.real) + pack("<f", v.imag)

        def custom_deserializer(b: bytes) -> Tuple[complex, bytes]:
            result = complex(unpack("<f", b[0:4])[0], unpack("<f", b[4:8])[0])
            remaining = b[8:]
            return result, remaining

        register_serializable(complex, custom_serializer, custom_deserializer)

        q = Qaz(1 + 2j)
        self.assertEqual(Qaz.deserialize(q.serialize()), q)

