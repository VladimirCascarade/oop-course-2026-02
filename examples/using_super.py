"""
Discussion of the builtin super() function.

super() can be used to find the first occurrence of a method in the MRO of a class,
excluding the class itself. It is the foundation of true multiple inheritance.

It is a form of computed indirect reference, used to design "cooperative classes".
It is powerful, but also complicated to use: As they say, careful what you wish for...

See https://rhettinger.wordpress.com/2011/05/26/super-considered-super/
See mysuper.py for a mock implementation of the super() lookup logic.

"""

from __future__ import annotations
import json
from typing import Any, ClassVar, final

# == A simple example ==

class A:

    x: ClassVar[str] = "A"

    def greet(self) -> None:
        print("Greetings from A!")

class B(A):

    def greet(self) -> None:
        print("Greetings from B!")

class C(A):

    x: ClassVar[str] = "C"
    y: ClassVar[str] = "C"

    # Note: super() does not give you access to instance attributes,
    #       because those are stored at instance level.
    #       super() returns a class, and the x, y above are class attributes.

class D(B, C):

    def greet(self) -> None:
        print(f"In D.greet(): {super() = }")
        print(f"In D.greet(): {super().x = }")
        print(f"In D.greet(): {super().y = }")
        super().greet()
        print("... and greetings from D!")

class E(D): ...

E().greet()
# In D.greet(): super() = <super: <class 'D'>, <E object>>
# In D.greet(): super().x = 'C'
# In D.greet(): super().y = 'C'
# Greetings from B!
# ... and greetings from D!


# == Cooperative Class Design ==

type JSON = bool | int | float | str | list[JSON] | dict[str, JSON]

class JSONSerialisable:
    """Base class for JSON serialisable classes."""

    def to_dict(self) -> dict[str, JSON]:
        """Serialises this instance to a JSON dictionary."""
        return {}

    @final # cannot be overridden by subclasses.
    def to_json(self) -> str:
        """Serialises this instance to string, via the JSON dictionary."""
        return json.dumps(self.to_dict())

class Named(JSONSerialisable):
    """Mixin implementing serialisation for a 'name' str attribute."""

    def __init__(self, name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.name = name

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        return d

class Aged(JSONSerialisable):
    """Mixin implementing serialisation for an 'age' int attribute."""

    def __init__(self, age: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.age = age

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["age"] = self.age
        return d

class Person(Named, Aged):
    """A class serialisable with 'name' and 'age' attributes."""
    def __init__(self, name: str, age: int) -> None:
        super().__init__(name=name, age=age)

p = Person("Alice", 30)
print(f"{Person.__mro__ = }")
# (
#     <class '__main__.Person'>,
#     <class '__main__.Named'>,
#     <class '__main__.Aged'>,
#     <class '__main__.JSONSerialisable'>,
#     <class 'object'>
# )
print(p.to_json()) # '{"age": 30, "name": "Alice"}'
# Person.to_dict()          -> Named.to_dict()
#                              d = super().to_dict() -> Aged.to_dict()
#                                                       d = super().to_dict() -> JSONSerialisable.to_dict()
#                                                         = {}                <- return {}
#                                                       d["age"] = self.age
#                                = {"age": 30}       <- return d
#                              d["name"] = self.name
# {"age":30,"name":"Alice"} <- return d


# == MRO Injection [Advanced] ==
# MRO injection exists as a way to add functionality
# between inheritance hierarchies without breaking the open-closed principle.

class Sniffer(JSONSerialisable):
    """A sniffer class for JSON serialisation 🐶."""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        print(f"Sniffed dictionary: {d}")
        return d
    
# Easy mode: inject between bases of a subclass.

class SniffedPerson(Person, Sniffer, JSONSerialisable):
    """Subclass forcing Sniffer to come between Person and JSONSeriable in MRO."""

print(f"{SniffedPerson.__mro__ = }")
# (
#     <class '__main__.SniffedPerson'>,
#     <class '__main__.Person'>,
#     <class '__main__.Sniffer'>, 🐶
#     <class '__main__.Named'>,
#     <class '__main__.Aged'>,
#     <class '__main__.JSONSerialisable'>,
#     <class 'object'>
# )

sp = SniffedPerson("Alice", 30)
sp.to_dict()
# Sniffed dictionary: {'age': 30, 'name': 'Alice'}

# Hard mode: modify the bases of the Person class directly.
# (only works if none of the bases is C-native, e.g. object)
# The fact that we can do this is an incarnation of the Open-Closed principle:
# it means you don't have to go and modify the source code, replacing Person
# with SniffedPerson wherever you need the sniffing (e.g. debugging, logging).

Person.__bases__ = (Sniffer,) + Person.__bases__ # 😭

print(f"{Person.__mro__ = }")
# (
#     <class '__main__.Person'>,
#     <class '__main__.Sniffer'>, 🐶
#     <class '__main__.Named'>,
#     <class '__main__.Aged'>,
#     <class '__main__.JSONSerialisable'>,
#     <class 'object'>
# )

p.to_dict() # Note: p = Person("Alice", 30) was created BEFORE the injection!
# Sniffed dictionary: {'age': 30, 'name': 'Alice'}
