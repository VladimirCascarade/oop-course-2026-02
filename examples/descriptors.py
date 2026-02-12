"""
Descriptors are one of the mechanism used by Python to expose attribute-like
names in classes. Notable examples include properties and slotted attributes.

Descriptors implement attribute-like access via three methods:

- __get__: read access, e.g. value = instance.attrname
- __set__: write access, e.g. instance.attrname = value
- __delete__: deletion, e.g. del instance.attrname

"""

from __future__ import annotations
from collections import Counter
from collections.abc import Callable, Iterable
from typing import Any, Hashable, Self, Type, cast, overload


_NOT_FOUND = object()
"""A unique object, used as a flag for cache misses in cache_property logic."""


class cached_property[Instance, Value]:
    """
    Example of a descriptor which can be read and deleted, but not written.
    Inspired from the cached_property descriptor from functools.

    .. warning::

        The implementation uses the instance __dict__ for value caching,
        so it cannot be used with slotted classes.

    """

    __func: Callable[[Instance], Value]
    """The wrapped function, providing the implementation of the cached property."""

    __doc__: str | None
    """The docstring of the wrapped function."""

    __module__: str
    """The module of the wrapped function."""

    __property_name: str | None
    """The property name, set once the class object is created."""

    __owner: Type[Instance] | None
    """The class owning this descriptor, set once the class object is created."""

    def __init__(self, func: Callable[[Instance], Value]):
        self.__func = func
        self.__property_name = None
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        print(f"Cached property object initialised, wrapping function {func.__name__}")

    @property
    def property_name(self) -> str:
        """Returns the name of the cached property, ensuring that it was set."""
        property_name = self.__property_name
        if property_name is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it."
            )
        return property_name

    @property
    def owner(self) -> Type[Instance]:
        """Returns the owner class of the cached property, ensuring that it was set."""
        owner = self.__owner
        if owner is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it."
            )
        return owner

    def __set_name__(self, owner: Type[Instance], name: str) -> None:
        """
        Sets the owner class and property name for the descriptor.
        This is called once the class object 'owner' is created,
        at which point the local name of the cached property is known.
        """
        if self.__property_name is None:
            self.__property_name = name
            self.__owner = owner
            print(f"Set name and owner for cached property {owner.__name__}.{name}")
        elif name != self.__property_name:
            raise TypeError(
                "Cannot assign the same cached_property to two different names: "
                f"{self.__property_name!r} and {name!r}."
            )

    def __get_cache(self, instance: Instance) -> dict[str, Any]:
        """Utility method to get the cache for an instance."""
        # The current implementation doesn't depend on self,
        # but the caching logic could be descriptor-dependent in principle.
        try:
            return instance.__dict__
        except AttributeError:
            raise TypeError("No __dict__ available for caching.") from None

    def is_cached_on(self, instance: Instance) -> bool:
        """Whether the property has a cached value on the given instance."""
        return self.property_name in self.__get_cache(instance)

    @overload
    def __get__(
        self, instance: Instance, owner: Type[Instance] | None = None
    ) -> Value: ...
    @overload
    def __get__(self, instance: None, owner: Type[Instance] | None = None) -> Self: ...
    def __get__(
        self, instance: Instance | None, owner: Type[Instance] | None = None
    ) -> Self | Value:
        """
        If 'instance' is None, returns the descriptor object itself.
        If 'instance' is not None, returns the property value:

        - If a cached value exists, it is returned.
        - Otherwise, the value is produced by invoking the wrapped function on the
          given instance, then the value is cached and returned.

        :raises AttributeError: if no __dict__ is available on the instance.
        """
        if instance is None:
            # Special case where the descriptor object itself is accessed:
            return self
        # The descriptor value is read on an instance:
        property_name = self.property_name
        cache = self.__get_cache(instance)
        val = cache.get(property_name, _NOT_FOUND)
        if val is _NOT_FOUND:
            print(f"Caching value for {self.owner.__name__}.{property_name}")
            val = self.__func(instance)
            cache[property_name] = val
        return val  # type: ignore[no-any-return]

    def __delete__(self, instance: Instance) -> None:
        """
        Deletes the cached value for the property.

        :raises AttributeError: if no __dict__ is available on the instance.
        :raises AttributeError: if no value for the property is cached on the instance.
        """
        property_name = self.property_name
        cache = self.__get_cache(instance)
        val = cache.get(property_name, _NOT_FOUND)
        if val is _NOT_FOUND:
            raise AttributeError("No property value cached.")
        del cache[property_name]
        print(f"Deleted cached value for {self.owner.__name__}.{property_name}")

    # Settable descriptors also define a __set__ method, to set values:
    # def __set__(self, instance: InstanceT, value: ValueT) -> None


print("In __main__, immediately before Bag declaration.")


class Bag[Item: Hashable]:
    """A super simple bag implementation showcasing a use case for cached properties."""

    __counts: dict[Item, int]

    def __new__(cls, items: Iterable[Item] | None = None) -> Self:
        self = object.__new__(cls)
        self.__counts = {}
        if items is not None:
            self.update(items)
        return self

    print("In Bag, immediately before unique_items declaration.")

    @cached_property
    def unique_items(self) -> frozenset[Item]:
        """
        Set of unique items:

        - Expensive to compute: compute on-demand, then store.
        - Expensive to store: allow cached value to be deleted.

        Cached is automatically invalidated when the set of unique items changes.
        """
        return frozenset(self.__counts.keys())

    print("In Bag, immediately after unique_items declaration.")

    def count(self, item: Item) -> int:
        return self.__counts.get(item, 0)

    def add(self, item: Item, count: int = 1) -> None:
        if count < 0:
            raise ValueError()
        current_count = self.count(item)
        if current_count == 0 and Bag.unique_items.is_cached_on(self):
            # new unique item => invalidate cached value for set of unique items
            del self.unique_items
        self.__counts[item] = current_count + count

    def update(self, items: Iterable[Item]) -> None:
        for item, count in Counter(items).items():
            self.add(item, count)


print("In __main__, immediately after Bag declaration.")

# In __main__, immediately before Bag declaration.
# In Bag, immediately before unique_items declaration.
# Cached property object initialised, wrapping function unique_items
# In Bag, immediately after unique_items declaration.
# Set name for cached property Bag.unique_items
# In __main__, immediately after Bag declaration.


bag = Bag(x % 8 for x in range(100))

print(bag.unique_items)
# Caching value for Bag.unique_items
# frozenset({0, 1, 2, 3, 4, 5, 6, 7})

bag.add(5)

print(bag.unique_items)
# frozenset({0, 1, 2, 3, 4, 5, 6, 7})

bag.add(8)
# Deleted cached value for Bag.unique_items

print(bag.unique_items)
# Caching value for Bag.unique_items
# frozenset({0, 1, 2, 3, 4, 5, 6, 7, 8})


# Interestingly, descriptors are also the mechanism used to implement class slots!


class Vec2:
    x: int
    y: int
    __slots__ = ("x", "y")


print(f"{Vec2.x = }")  # type: ignore[misc]
# Mypy complains that: "x" in __slots__ conflicts with class variable access...
# ... but actually Vec2.x exists: it is a descriptor, implementing the slot!
# Vec2.x = <member 'x' of 'Vec2' objects>

# The __get__, __set__ and __delete__ methods of the Vec2.x descriptor
# give read, write and delete access to the slot value, which is stored
# inside of a C struct (at least, in CPython).
# The logic for doing so is defined by the member_descriptor class:

print(f"{type(Vec2.x) = }")  # type: ignore[misc]
# type(Vec2.x) = <class 'member_descriptor'>

# Sadly, end of the line: member_descriptor is an opaque class, implemented in C.
# See https://github.com/python/cpython/blob/main/Objects/descrobject.c
# and https://github.com/python/cpython/blob/main/Include/descrobject.h
