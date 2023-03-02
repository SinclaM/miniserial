# Miniserial

Miniserial is a Python package for dead-simple, space-efficient serialization
and deserialization of simple dataclasses. There are many great packages for
general purpose serialization in the standard library and on PyPI (e.g. `json`,
`marshal`, `pickle`, `ujson`, `bson`, etc.), but most use serialization
formats that can come with significant byte overhead. Sometimes, project
constraints—like the 256-byte-max-packet radio devices that inspired this
package—encourage the use of a much more compact format, something akin to
protobuf or the layout of C structs. But libraries in this space typically come
with the overhead of implementing manual serializers, modifying class fields
with various wrappers, or using non python data specifications (e.g. `.proto`
files). `msgpack` comes close, but does not work out of the box with classes.
Miniserial makes compact serialization easy. Simply have your
dataclass inherit from the `Serialization` mixin, and `serialize` and
`deserialize` methods will be automatically generated for the class.
For example:

```python3
from dataclasses import dataclass
from miniserial import Serializable

@dataclass
class Person(Serializable):
    name   : str
    age    : int
    titles : list[str]
    balance: float
    
p = Person("Bob", 34, ["Mr.", "Dr.", "Professor"], 239847.25)
assert Person.deserialize(p.serialize()) == p
```

Classes that inherit the `Serializable` mixin must be dataclasses composed of
fields annotated with supported types, which include any other class which
inherits `Serializable`. This means that even recursive structures,
like trees, can be serialized and deserialized.

```python3
from __future__ import annotations
from dataclasses import dataclass
from miniserial import Serializable

@dataclass
class Node(Serializable):
    value   : int
    children: list[Node]

#                 1
#               /   \ 
#              2     3 
#             / \
#            4   5
tree = Node(1, [Node(2, [Node(4, []), Node(5, [])]), Node(3, [])])
assert Node.deserialize(tree.serialize()) == tree
```

Documentation of supported types and the serialization format is on the way. For
now, `bool`, `int`, `float`, `str`, and `list` are supported, along with any
other user-defined class that inherits `Serializable`. `int` and `float` are
taken to be 32 bit values. Support for more types, including `int64`, `float64`,
etc. from `numpy` are on the horizon.
