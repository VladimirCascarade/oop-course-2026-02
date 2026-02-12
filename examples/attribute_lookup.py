"""
The __getattr__, __setattr__ and __delattr__ special methods provide a general purpose
mechanism to expose attribute-like names in Python.

As an extreme example, we implement a mechanism where attributes are stored in a global
key-value store, keyed by object id and attribute name.
The key-value store could, for example, be an interface to a no-sql database (as long
as a stable UID mechanism is used for object identification, instead of Python's 'id'.)
"""

from typing import Any, ClassVar, Protocol, Self

class AttrStore(Protocol):
    """Interface for the key-value store used to store attribute values."""

    def __getitem__(self, key: tuple[int, str]) -> Any:
        ...

    def __setitem__(self, key: tuple[int, str], value: Any) -> None:
        ...

    def __delitem__(self, key: tuple[int, str]) -> Any:
        ...

class Object:
    """Base class for objects with attributes stored in the global key-value store."""
    
    attr_store: ClassVar[AttrStore] = {}
    """The global key-value store, saved as a class variable."""

    __slots__ = () # Note: no __dict__, no slots.

    def __getattr__(self, name: str) -> Any:
        """Reads attribute value from the global key-value store."""
        try:
            return Object.attr_store[(id(self), name)]
        except KeyError:
            raise AttributeError(
                f"AttributeError: {type(self).__name__!r} object "
                f"has no attribute {name!r}"
            ) from None

    def __setattr__(self, name: str, value: Any) -> None:
        """Writes attribute value to the global key-value store."""
        Object.attr_store[(id(self), name)] = value

    def __delattr__(self, name: str) -> None:
        """Deletes attribute value from the global key-value store."""
        try:
            del Object.attr_store[(id(self), name)]
        except KeyError:
            raise AttributeError(
                f"AttributeError: {type(self).__name__!r} object "
                f"has no attribute {name!r}"
            ) from None


class Vec2(Object):
    """A concrete class, using the global key-value store to store its attributes."""
    
    # We can annotate the attributes for the benefit of the typechecker.
    # This has no effect on the storage mechanism, it's just a static hint.

    x: int
    y: int

    __slots__ = () # Note: no __dict__, no slots.

    def __new__(cls, x: int, y: int) -> Self:
        # Note: the constructor is the same as usual.
        self = object.__new__(cls)
        self.x = x
        self.y = y
        return self
    
    def __repr__(self) -> str:
        return f"Vec2({self.x}, {self.y})"
    
u = Vec2(5, 3)

print(f"{u = }")
print(f"{Object.attr_store = }")
# u = Vec2(5, 3)
# Object.attr_store = {(2567706452592, 'x'): 5, (2567706452592, 'y'): 3}

# __getattr__
ux_plus_2 = u.x + 2
print(f"{ux_plus_2 = }")
# ux = 5

# __setattr__
u.x = 1
print(f"{u = }")
print(f"{Object.attr_store = }")
# u = Vec2(1, 3)
# Object.attr_store = {(2567706452592, 'x'): 1, (2567706452592, 'y'): 3}

# __delattr__
del u.y
print(f"{Object.attr_store = }")
# Object.attr_store = {(2567706452592, 'x'): 1}
