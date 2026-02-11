"""
An implementation of a mock buffer framework.

In reality, the bytearray would be bytes on some (maybe slow) medium.
"""

# About protected vs private:
# - Protected members are part of the developer API: changing them is not a breaking
#   change for the users of your library, but it is a breaking change for other devs.
# - Private members are private to the specific designer of the class,
#   changing them is never a breaking change to anybody else.
# In a nutshell: protected is "public, but be careful when using it".

# Design choices to accommodate multiple inheritance:
# 1. Use protected attributes for data which is (likely) useful to subclasses.
# 2. Use private attributes for data which is too hard to keep consistent.
# 3. Use initialisers (__init__) rather than constructors (__new__).

from collections import deque
from collections.abc import Iterable
from typing import Protocol, Self, overload

type Byte = int
"""Type alias for a byte, for documentation/legibility purposes."""

type ContiguousSlice = slice[int, int, None]

class ByteData(Protocol):
    """Interface for a buffer of bytes: sized, with indexed/sliced access."""

    @overload
    def __getitem__(self, idx: int) -> Byte: ...
    @overload
    def __getitem__(self, idx: ContiguousSlice) -> bytes: ...
    #   start and stop but no non-trivial step ^^^^

    def __getitem__(self, idx: int | ContiguousSlice) -> Byte | bytes:
        """
        Reads the byte/bytes at the given index/index slice.
        
        The slice must be contiguous.
        """

    def __setitem__(self, idx: int, value: Byte|bytes) -> None:
        """
        Writes the byte/bytes starting from the given index/index slice.
        The underlying data will be extended if necessary.
        
        The slice must be contiguous.
        """

    def __len__(self) -> int:
        """The number of available bytes."""

class Reader:
    """Reads bytes sequentially from a byte array."""
    # I plan for subclass access to these internals by making them protected:
    _data: ByteData
    _pos: int
    
    # Planning for true multiple inheritance, constructors are not the right way to go:
    # when trying to construct instances of multiple parent classes, we will get
    # different objects. What we want, instead, is to construct a single blank object,
    # and to run initialisers for all parent classes.
    # 🤞 We trust/hope that the initialisers will do compatible stuff.

    # def __new__(cls, data: ByteData) -> Self:
    #     self = super().__new__(cls)
    #     self._data = data
    #     self._pos = 0 # Note: we start reading from the start of the data.
    #     return self
    
    def __init__(self, data: ByteData) -> None:
        # Note: There is no object.__new__(Reader).
        # At the end of the hierarchy, at the concrete class of the instance created,
        # the runtime will implicitly do:
        # instance = object.__new__(cls)
        # cls.__init__(instance, ...)
        # If correctly designed, a chain of __init__ calls will follow.
        self._data = data
        self._pos = 0 # Note: we start reading from the start of the data.

    @property
    def available(self) -> int:
        """The number of bytes available to read."""
        return len(self._data)-self._pos

    def read(self, num_bytes: int) -> bytes:
        """Read up to the given number of bytes, max the :attr:`available` bytes."""
        if num_bytes < 0:
            raise ValueError("Number of bytes must be non-negative.")
        start = self._pos
        num_bytes = min(num_bytes, self.available)
        read = self._data[start:start+num_bytes]
        self._pos += num_bytes
        return read


class BufferedReader(Reader):
    """A :class:`Reader` with buffering capabilities."""

    # A private implementation detail for this class.
    # Making them private makes it possible to combine them with the
    # same name attributes on a BufferedWriter without conflict (tx to name-mangling).
    __chunk_size: int
    __buffer: deque[Byte] # Not the most performant, but the simplest conceptually


    # def __new__(cls, data: ByteData, chunk_size: int) -> Self:
    #     # 1. Validation:
    #     if chunk_size <= 0:
    #         raise ValueError("Chunk size must be strictly positive.")
    #     # 2. Construct an instance of cls using the Reader constructor:
    #     #    In particular, the constructor takes care of setting Reader attributes. 
    #     self = Reader.__new__(cls, data)
    #     # 3. Set BufferedReaders attributes:
    #     self.__chunk_size = chunk_size
    #     self.__buffer = deque()
    #     # 4. Return instance.
    #     return self

    def __init__(self, data: ByteData, chunk_size: int) -> None:
        # 1. Validation:
        if chunk_size <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        # 2. Construct an instance of cls using the Reader constructor:
        #    In particular, the constructor takes care of setting Reader attributes. 
        # 3. Set BufferedReaders attributes:
        self.__chunk_size = chunk_size
        self.__buffer = deque()


    def read(self, num_bytes: int) -> bytes:
        # 1. Reduce num_bytes to number of bytes I can actually read from data:
        num_bytes = min(num_bytes, self.available)
        buffer = self.__buffer
        # 2. Fill the buffer if needed:
        while len(buffer) < num_bytes:
            self.__read_chunk()
        # I am guaranteed that the buffer contains at least num_bytes, so...
        # 3. Extract bytes from buffer and return:
        return bytes(buffer.popleft() for _ in range(num_bytes))
        
    def __read_chunk(self) -> None:
        """Read a chunk of bytes from the underlying data and push them in buffer."""
        # I delegate reading self.__chunk_size bytes to Reader.read.
        # I cannot use self.read, because I have overridden the method.
        # self.read(num_bytes) is the same as type(self).read(self, num_bytes)
        self.__buffer.extend(Reader.read(self, self.__chunk_size))
        #              class ^^^^^^      ^^^^ instance
        

class RandomReader(Reader):
    """A :class:`Reader` with seeking capabilities."""

    # No need for a constructor, this is really a mixin for readers.
    # It automatically inherits __new__ signature from Reader.
    # In general, the constructor of the first base class is used,
    # because that's where the search for __new__ starts in the MRO.

    def seek(self, pos: int) -> None:
        """Sets the current reading position."""
        if not 0 <= pos < len(self._data):
            raise IndexError(f"Invalid seek position {pos}")
        self._pos = pos


class Writer:
    """Writes bytes sequentially to a byte array."""
    _data: ByteData
    _pos: int

    # def __new__(cls, data: ByteData) -> Self:
    #     self = super().__new__(cls)
    #     self._data = data
    #     self._pos = len(data) # Note: we start writing at the end of the data.
    #     return self

    def __init__(self, data: ByteData) -> None:
        self._data = data
        self._pos = len(data) # Note: we start writing at the end of the data.

    def write(self, data: bytes) -> None:
        """
        Writes the given bytes to the underlying data starting at current position,
        which is updated to the end of the written data.
        """
        self._data[self._pos] = data
        self._pos += len(data)


class Accessor(Reader, Writer):
    """A combined :class:`Reader` and :class:`Writer`."""

    # def __new__(cls, data: ByteData) -> Self:
    #     self = Reader.__new__(cls, data)
    #     other = Writer.__new__(cls, data)
    #     # ☠️ we cannot "merge" two different objects!
    #     return self

    def __init__(self, data: ByteData) -> None:
        # Someone created an instance self and gate it to you.
        # 1. Initialise the Writer attributes:
        Writer.__init__(self, data)
        # 2. Initialise the Reader attributes:
        Reader.__init__(self, data)
        # Things work out fine because:
        # - the same data is written to the common _data attribute ✔
        # - a valid position is written to the common _pos attribute ❔
        # The order I chose determines the starting position:
        # because Reader.__init__ was called last, we start at 0.
        # 
        # Note: it is possible that there is no consistent ordering in which
        # the initialisers can be called, but that's fixable because the only
        # attributes where conflicts can arise are protected ones, which you
        # can set straight by hand here.

print(f"{Accessor.__mro__ = }") # Accessor, Reader, Writer, object

# Had I not defined Accessor.__init__, the lookup for Accessor.__init__ would have gone:
# Accessor, Reader, Writer, object
# ^^^^^^^^ 1. Look for __init__ here, not found, move to next.
# Accessor, Reader, Writer, object
#           ^^^^^^ Look for __init__ here, run, done.
# Result: the __init__ of Writer is never run.
# In this example, it would ultimately do have the same result as our Accessor.__init__,
# but in general it is the wrong thing to do with initialisation.

# class BufferedWriter(Writer):
#     """A :class:`Writer` with buffering capabilities."""

# class RandomWriter(Writer):
#     """A :class:`Writer` with seeking capabilities."""

# class RandomAccessor(Accessor, RandomReader, RandomWriter):
#     """An :class:`Accessor` with seeking capabilities."""

# class BufferedRandomAccessor(RandomAccessor, BufferedReader, BufferedWriter):
#     """A :class:`RandomAccessor` with buffering capabilities."""
