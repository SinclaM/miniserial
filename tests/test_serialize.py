from __future__ import annotations
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

@dataclass
class Bar(Serializable):
    x: int
    y: list[float]

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

class SerializaitonTests(unittest.TestCase):
    def test_simple(self) -> None:
        f = Foo(1, 2.0, "hello", True)

        serialized = pack("<i", f.x) + pack("<f", f.y) + f.z.encode() + b"\x00" + pack("<?", f.b)
        self.assertEqual(f.serialize(), serialized)
        self.assertEqual(Foo.deserialize(f.serialize()), f)

        b = Bar(11, [0.0, -1.0, 13.432])
        deserialized = Bar.deserialize(b.serialize())
        self.assertEqual(deserialized.x, b.x)
        for u, v in zip(deserialized.y, b.y):
            self.assertAlmostEqual(u, v, places=6)

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

