"""
An implementation of a bag data structure.
"""

from collections.abc import Hashable, Iterable, Iterator
from typing import Self
#    ^^^^^^^^^^^^^^^ stdlib module containing the collection abstract base classes

from collections_abc import IndexOfMixin


class Bag[ItemT: Hashable](IndexOfMixin[ItemT]):
    #                      ^^^^^^^^^^^^^^^^^^^ automatically acquire index_of method
    #            ^^^^^^^^ generic type bound (T must be a sub-type of Hashable)
    #     ^^^^^ generic type parameter for the items in the bag
    """
    A bag is a unordered collection (like a set) with repetition (like a list).
    """

    __counts: dict[ItemT, int]
    """
    Counts for the items in the bag.

    Invariant: The count for an item is always strictly positive.
    """

    __len: int
    """
    The number of items in the bag.

    Invariant: self.__len == sum(self.__counts.values())
    """

    # By default, custom classes define a "__dict__" instance attribute,
    # which can be used to defined custom instance attributes dynamically.
    # The instance __dict__ is 272B of unnecessary baggage if you don't use it.

    # This is often not what you want when you define a class,
    # and __slots__ give you a way to explicitly specify the settable attributes.

    # The only attribute supported are __counts and __len:
    __slots__ = ("__counts", "__len")

    def __new__(cls, items: Iterable[ItemT]) -> Self:
        """
        I want to construct bags from any iterable of items.
        """
        # 1. Create a blank object of class 'cls':
        self = object.__new__(cls)
        # 2. Initialise internal data structures for an empty bag
        self.__counts = {}
        self.__len = 0
        # 3. Delegate the adding logic to the 'extend' method:
        self.extend(items)
        # 4. Return the populated bag:
        return self

    # Desired operations on the bag:

    def add(self, item: ItemT) -> None:
        """I want to be able to add elements to my bag."""
        # Delegate the counting logic to the 'count' method:
        self.__counts[item] = self.count(item) + 1
        self.__len += 1

    def remove(self, item: ItemT) -> None:
        """I want to be able to remove elements from my bag."""
        # Delegate the counting logic to the 'count' method:
        count = self.count(item)
        if count == 0:
            raise KeyError(f"Item not present in bag: {item!r}")
            #                      !r sets format to debug ^^
        if count == 1:
            del self.__counts[item]
            # The above is implemented by __delitem__, removes item from dict.
            # Not the same as del self.__counts, which deletes the __counts attribute
            # from the self object and is implemented by the __delattr__ method.
        else:
            self.__counts[item] = count - 1
        self.__len -= 1

    def clear(self, item: ItemT) -> None:
        """I want to be able to remove all copies of an element from my bag."""
        if item in self.__counts:
            del self.__counts[item]

    def extend(self, items: Iterable[ItemT]) -> None:
        """For convenience, I want to be able to add many elements to my bag."""
        for item in items:
            # Delegate the adding logic to the 'add' method:
            self.add(item)

    def count(self, item: ItemT) -> int:
        """
        I want to count how many copies of an item are in the bag.
        """
        # Return positive count if present, 0 if not present:
        return self.__counts.get(item, 0)
        # count = 0
        # for item_ in self:
        #     if item_ == item:
        #         count += 1
        # return count

    # Dunder methods, implementing pre-defined runtime functionality.

    # Note: a side effect of using a dict internally is that iteration
    #       respects insertion order, but this is not something I promised.
    def __iter__(self) -> Iterator[ItemT]:
        """
        I want to go through the elements of a bag => Bag[T] is Iterable[T]

        __iter__ specifies the behaviour of the iter() builtin function.
        """
        # A common OO pattern I didn't discuss yesterday is the generator pattern:
        # it is used to implement "interruptible" functions, which "yield" control.
        #
        # Using 'yield' in a function turns it into a generator function,
        # which in the simplest case effectively returns an iterator automatically.
        # Calling __next__ executes the function until the next yield statement,
        # raises StopIteration once the function finally exits.
        #
        # Go through all unique elements:
        for item, count in self.__counts.items():
            #           key-value pairs ^^^^^^^^
            # Yield each unique element with repetition:
            for _ in range(count):
                yield item  # returns item to the caller

    def __len__(self) -> int:
        """
        I want to know how many elements are in a bag => Bag[T] is Sized

        __len__ specifies the behaviour of the len() builtin function.
        """
        # The contract you make with your users is that this matches
        # the number of elements yielded by __iter__.
        return self.__len  # faster than explicit counting every time
        # return sum(self.__counts.values())
        # #                values ^^^^^^^^^

    def __contains__(self, item: ItemT) -> bool:
        """
        I wan to know whether a given item is in the bag.

        __contains__ specifies the behaviour of the 'in' operator
        """
        # I don't have items with count 0 in my __counts dictionary.
        return item in self.__counts
        # for item_ in self:
        #     if item_ == item:
        #         return True
        # return False
