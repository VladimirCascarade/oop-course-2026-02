"""
Reproduces a fragment of the stdlib collections.abc module,
but using modern structural typing machinery (Protocols).
"""

# It's not entirely straightforward to find collections.abc source,
# because it is manually plugged into the module mapping.
# This snippet is from the collections module source:
# import _collections_abc
# import sys as _sys
# _sys.modules['collections.abc'] = _collections_abc

# If you wanna look at the collections.abc source, use the import below:
import _collections_abc

# The implementation of collection "interfaces" in collections.abc
# follows an old pattern where we use ABCs and special hooks to check at runtime.
# class Iterable(metaclass=ABCMeta):
#     __slots__ = ()
#     @abstractmethod
#     def __iter__(self):
#         while False:
#             yield None
#     @classmethod
#     def __subclasshook__(cls, C):
#         if cls is Iterable:
#             return _check_methods(C, "__iter__")
#         return NotImplemented
#     __class_getitem__ = classmethod(GenericAlias)

# Protocols are Python's structurally typechecked types.
# It's the spiritual equivalent of an interface in TypeScript.
from collections.abc import Callable
from typing import Protocol, runtime_checkable

# @runtime_checkable decorator checks that the methods are defined at runtime,
# but does not perform any static type-check on their signature.


@runtime_checkable
class Iterator[T](Protocol):
    """Interface for iterators."""

    __slots__ = ()  # => no slots on this class. Subclasses can define their own!
    # Protocols are not really interface, they're a special piece of machinery
    # introduces much later in the language's history.
    # In particular, the slots mechanism works the same as with other classes:
    # if you omit a slots declaration, an instance dictionary is created automatically,
    # and this necessarily holds for all subclasses (because once it's there...)

    # Design rule you should follows:
    # If you design interfaces or mixins, you must include __slots__ = ()
    # because otherwise you're forcing your users to have an instance dictionary,
    # and interfaces/mixins shouldn't have attribute responsibilities.

    def __next__(self) -> T:
        """
        Returns the next item if available, raises :class:`StopIteration` otherwise.
        """
        # Because this is a protocols, methods don't have implementations.


@runtime_checkable
class Iterable[T](Protocol):
    """Interface for iterable objects."""

    __slots__ = ()

    def __iter__(self) -> Iterator[T]:
        """Returns an iterator over the items in the iterable."""


@runtime_checkable
class Sized(Protocol):
    """Interface for sized objects."""

    __slots__ = ()

    def __len__(self) -> int:
        """The size of the object."""


@runtime_checkable
class Container[T](Protocol):
    """Interface for container objects."""

    __slots__ = ()

    def __contains__(self, item: T) -> int:
        """Whether the item is in the container."""


# This is an example of:
# - interface segregation: I used the bare minimum interface required for 'iterable'
# - dependency inversion: I factored the mapping behaviour through an interface.
def iter_map[S, T](iterable: Iterable[S], f: Callable[[S], T]) -> Iterable[T]:
    #                           f: (S,) -> T ^^^^^^^^^^^^^^^^
    #        ^^^^ generic type parameters (parametric polymorphism)
    for item in iterable:
        yield f(item)


@runtime_checkable
class MutableContainer[T](Container[T], Protocol):
    # extends Container[T]^^^^^^^^^^^^  ^^^^^^^^ it is still an interface.
    #                                            (As opposed to being a class which
    #                                             implements the interface instead.)
    """Interface for mutable containers."""

    __slots__ = ()

    def add(self, item: T) -> None:
        """
        Adds an item to the container.

        Invariant: after I add an item to a container, it is contained in it:

        container.add(item)
        item in container # True here
        """

    def remove(self, item: T) -> None:
        """
        Removes an item from the container.

        This does not necessarily imply that the item is no longer in the container,
        because there may be containers with multiplicity (e.g. bags).
        """

    def clear(self, item: T) -> None:
        """
        Removes all copies of an item from the container.

        Invariant: after I clear an item from a container, it is not contained in it.

        container.clear(item)
        item in container # False here
        """


class IndexOfMixin[T](Iterable[T]):
    #                 ^^^^^^^^^^^ Extending this mixin forces classes to
    #                             implement the Iterable[T] interface.
    """A mixin implementing index_of functionality for iterables."""

    __slots__ = ()  # mixins shouldn't force instance __dict__

    def index(self, item: T, start: int = 0, stop: int | None = None) -> int:
        """
        Returns the index of the first occurrence of the item.

        :raises ValueError: if the item is not found.
        """
        index = 0
        for item_ in self:
            if stop is not None and index >= stop:
                break
            if index < start:
                index += 1
                continue
            if item_ == item:
                return index
            index += 1
        raise ValueError(f"Item not found: {item!r}")


# TODO: add Reversible, Collection, make a Sequence interface, talk about SequenceMixin
# Plan for afternoon.
# Interfaces:
# Collection = Sized + Iterable + Container
# Sequence = Reversible + Collection
# Mixins:
# SequenceMixin = implements __iter__, __contains__, __reversed__ from __getitem__ + __len__
# IndexOfMixin = implements index from __iter__
# CountMixin = implements count from __iter__
