"""
The RAII (Resource Acquisition Is Initialisation) Pattern is a common resource
acquisition pattern used to avoid inconsistent usage of resources and/or deadlocks.

It is embodied in the standard library construct of "context managers".

Examples of RAII:

- file opening -> builtin open function
- locks, e.g. re-entrancy locks for methods
- instance creation for flyweight pattern

Essentially, any piece of code with the following lifecycle:

1. We enter a context, acquiring a resource (implicitly or explicitly).
2. We do some stuff within the context, using the resource (implicitly or explicitly).
3. We exit the context, and some cleanup/finalisation logic is performed automatically,
   releasing the resource.

"""

from collections.abc import Buffer, Callable, Iterator
from contextlib import contextmanager
from typing import Protocol, Self, SupportsIndex, SupportsInt, overload
from weakref import WeakValueDictionary

# (1) File opening

filename = "classobj.py"

# 1. Enter the context, the file is opened and the 'file' handle is given to use.
#                           ^^^^ resource          ^^^^^^^^^^^^^ access to the resource
with open(filename, "r") as file:
    # 2. Within this block/context, the file is open and we can safely use it.
    lines = list(file)
# 3. As we exit the context, the file is automatically closed.
print(f"Number of lines in {filename!r}: {len(lines)}")

class uint(int):

    def __new__(cls, value: str | Buffer | SupportsInt | SupportsIndex) -> Self:
        value = int.__new__(cls, value)
        if value < 0:
            raise ValueError("Unsigned integer values cannot be negative.")
        return value

    @overload
    def __add__(self, other: uint) -> uint: ...

    @overload
    def __add__(self, other: int) -> int: ...
    
    def __add__(self, other: int) -> int:
        if isinstance(other, uint):
            return uint(int.__add__(self, other))
        return int.__add__(self, other)

# (2) Re-entrancy lock

type Address = str

class InsufficientFundsError(ValueError):
    
    def __new__(cls, wallet: Address, balance: uint, required: uint) -> Self:
        message = f"Insufficient balance for {wallet = }: {required = }, {balance = }."
        return ValueError.__new__(cls, message)
    
class ReEntrancyError(RuntimeError):
    ...

class Token:
    """A mock version of a fungible token smart contract."""

    _accounts: dict[Address, uint]
    __is_reentrancy_locked: bool

    def __new__(cls) -> Self:
        self = object.__new__(cls)
        self._accounts = {}
        self.__is_reentrancy_locked = False
        return self

    @contextmanager
    def _reentrancy_lock(self) -> Iterator[None]:
        # 1. Setup: Try to acquire the lock.
        # 1(a) Raise error if locked: 
        if self.__is_reentrancy_locked:
            raise ReEntrancyError("Attempted to re-enter a method call.")
        # 1(b) Acquire the lock:
        self.__is_reentrancy_locked = True
        try:
            # 2. Context: yield control to caller.
            yield None
        finally:
            # 3. Cleanup: Release the lock.
            self.__is_reentrancy_locked = False

    # With some additional work you can turn the lock into a decorator
    # that can be applied to a whole method (it's what smart contracts libs do).

    # def reentrancy_locked(meth: Callable[[Token, P], R]) -> Callable[[Token, P], R]:
    #     def inner(self: Token, args, kwargs):
    #         with self._reentrancy_lock():
    #             return meth(self, *args, **kwargs)
    #     return inner 

    def _mint(self, wallet: Address, amount: uint) -> None:
        self._accounts[wallet] = self._accounts.get(wallet, uint(0)) + amount
    
    def transfer(
            self,
            source: Address,
            target: Address,
            amount: uint,
            source_callback: Callable[[Address, uint], None] | None = None,
            target_callback: Callable[[Address, uint], None] | None = None
        ) -> None:
        with self._reentrancy_lock():
            # Protected section: the acquired lock prevents re-entrancy.
            balance = self._accounts.get(source, uint(0))
            try:
                # Delegates validation of available balance checking to uint constructor:
                self._accounts[source] = uint(balance - amount) # raises ValueError if neg
                if source_callback is not None:
                    # This turns out to be a ** very bad ** idea:
                    # source_callback can call into transfer again,
                    # potentially breaking the integrity of your computation.
                    # This is known as a re-entrancy bug, and it lost dozens of millions.
                    # Solution 1: structure your code as validation -> execution -> notification
                    # Solution 2: introduce a re-entrancy lock
                    source_callback(source, amount)
            except ValueError:
                # The ValueError from uint doesn't have any info about the error context,
                # so we re-raise it as a different error, containing the info we want.
                raise InsufficientFundsError(source, balance, amount) from None
                #                         disregard originating error ^^^^^^^^^
            self._accounts[target] = self._accounts.get(target, uint(0)) + amount
            if target_callback is not None:
                target_callback(source, amount)

# (3) Factory pattern with loose coupling.

type ItemUID = int
class Item(Protocol):

    @property
    def uid(self) -> ItemUID: ...

class Factory[ItemT: Item]:

    _next_uid: ItemUID
    _items: WeakValueDictionary[ItemUID, ItemT]
    _expecting_registration: ItemUID | None

    def __new__(cls) -> Self:
        self = object.__new__(cls)
        self._next_uid = 1
        self._items = WeakValueDictionary()
        self._expecting_registration = None
        return self
    
    # The implementation of the factory pattern we've seen takes the form of:
    # 1. Factory knows the class to construct
    # 2. Factory receives the unmanaged constructor arguments
    # 3. Factory produces the additional managed constructor arguments (e.g. uid)
    # 4. Factory construct and returns the instance.
    # This becomes problematic when the constructor is not statically known.

    # Alternative implementation: the factory provides the resource to a caller,
    # but enforces that the caller registers themselves with the factory as 
    # part of their constructor. Except, the factory doesn't know the constructor... 


    @contextmanager
    def fresh_uid(self) -> Iterator[ItemUID]:
        # 1. Disallow nested item creation (for simplicity):
        if self._expecting_registration:
            raise ValueError("Nested item creation is not allowed.")
        # 2. Generate a fresh UID:
        uid = self._next_uid
        # 3. Set flag stating that registration is expected:
        self._expecting_registration = uid
        try:
            # 4. Pass the fresh UID to the caller:
            yield uid
        finally:
            # 5. Enforce that exactly one item has registered themselves with that UID.
            if self._expecting_registration is not None:
                raise ValueError("Item did not register themselves.")
            # 6. Increase the UID (because it has been spent):
            self._next_uid += 1

    def register(self, item: ItemT) -> None:
        # 1. Check that we're within the creation process:
        if self._expecting_registration is None:
            raise ValueError("This method must be called as part of item creation.")
        # 2. Check that the item being registered has the expected UID:
        if self._expecting_registration != item.uid:
            raise ValueError("Unexpected UID in item registration.")
        # 2. Register the item:
        self._items[item.uid] = item
        # 3. Clear the expectation flag:
        self._expecting_registration = None

class Shoe:

    _uid: ItemUID


    def __new__(cls, factory: Factory[Shoe]) -> Self:
        with factory.fresh_uid() as uid:
            self = object.__new__(cls)
            self._uid = uid
            factory.register(self)
            return self
        # Here, we exit the context, i.e. we move to the finally section of 'fresh_uid'
        # => if the object has not registered themselves, error is raised and the
        #    constructor fails to return a new instance of the shoe.

    @property
    def uid(self) -> ItemUID:
        return self._uid
