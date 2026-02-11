"""Implementation of a withdrawable stack data structure."""

from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass, field
from typing import Concatenate, ParamSpec, Self, TypeVar

class StackError(Exception):
    """Base class for all stack errors"""

class EmptyStackError(StackError):
    """Error raised when peeking into or popping from an empty stack."""

class ItemAlreadyPresentError(StackError):
    """Error raised pushing an item onto the stack which  already in the stack."""

P = ParamSpec("P")
R = TypeVar("R")
T_ = TypeVar("T_", bound=Hashable)

# A dataclass is the right data structure to use for objects that just store data,
# with no interesting logic associated (aka low-level structured data containers).
@dataclass(slots=True)
class _Deletable[T]:
    """A low-level structured data container for internal use."""
    inner: T
    deleted: bool = field(default=False)

class WithdrawableStack[T: Hashable]:
    #                   ^^^^^^^^^^^ fast element lookup required by remove
    """A stack data structure that allows for withdrawing elements."""

    @staticmethod
    def not_empty(
        meth: Callable[Concatenate[WithdrawableStack[T_], P], R]
    ) -> Callable[Concatenate[WithdrawableStack[T_], P], R]:
        """
        Decorator to ensure that a withdrawable stack method is called
        on an non-empty stack.
        """
        def inner(
            self: WithdrawableStack[T_], /,
            *args: P.args,
            **kwargs: P.kwargs
        ) -> R:
            if not self:
                # For sized objects, 'not self' is a Python idiom for 'len(self) == 0'
                # The dunder method __bool__ is automatically implemented if __len__
                # is implemented, to mean zero length. It can be overridden.
                raise EmptyStackError()
            return meth(self, *args, **kwargs)
        return inner
    
    # __stack: list[T] # this is not the right approach, because I need to invalidate
    # Option 1: __stack: list[T | None]
    # Option 2: __stack: list[T | _UniqueSingletonClass]
    # Option 3: __stack: list[_Deletable[T]]
    __stack: list[_Deletable[T]]
    __idxs: dict[T, int]
    # Invariant: items in the stack are exactly those present in __idxs

    __slots__ = ("__stack", "__idxs")

    def __new__(cls, items: Iterable[T] = ()) -> Self:
        """
        Constructs a new withdrawable stack, pushing the items into the stack in order.
        """
        # 1. Create a blank object of class cls
        self = object.__new__(cls)
        # 2. Set attributes for empty stack:
        self.__stack = []
        self.__idxs = {}
        # 3. Push items into the stack (if any):
        for item in items:
            self.push(item)
        # 4. Return the stack:
        return self
    
    @not_empty
    def peek(self) -> T:
        return self.__stack[-1].inner
    
    def push(self, item: T) -> None:
        if item in self.__idxs:
            raise ItemAlreadyPresentError()
        self.__idxs[item] = len(self.__stack)
        self.__stack.append(_Deletable(item))

    @not_empty
    def pop(self) -> T:
        # Amortised O(1) over all inserted elements.
        item_ = self.__stack.pop()
        while item_.deleted:
            # @not_empty guarantees that at some point an item won't be deleted
            item_ = self.__stack.pop()
        item = item_.inner
        del self.__idxs[item]
        return item
    
    def remove(self, item: T) -> bool:
        """Removes the item from the stack if present, returns whether present."""
        idx = self.__idxs.get(item)
        if idx is None:
            return False
        # self.__stack.pop(idx) # O(N), which defeats the purpose of idxs...
        self.__stack[idx].deleted = True
        del self.__idxs[self.__stack[idx].inner]
        return True
    
    def __contains__(self, item: T) -> bool:
        return item in self.__idxs # amortised O(1) lookup
        #      ^^^^^^^^^^^^^^^^^^^ containment/iteration for mappings is over keys

    def __len__(self) -> int:
        # return len(self.__stack) # This is wrong with _Deletable[T]
        return len(self.__idxs) # This is the right way to count items
