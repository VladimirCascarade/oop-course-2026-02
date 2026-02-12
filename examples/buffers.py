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

from abc import ABCMeta, abstractmethod
from collections import deque
from collections.abc import Iterable
from typing import Protocol, Self, overload, override

from numpy import byte

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

    @overload
    def __setitem__(self, idx: int, value: Byte) -> None: ... 
    @overload
    def __setitem__(self, idx: ContiguousSlice, value: bytes) -> None: ... 
    def __setitem__(self, idx: int | ContiguousSlice, value: Byte|bytes) -> None:
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
    
    def __len__(self) -> int:
        """The size of the underlying data."""
        return len(self._data)


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

    # This is only for the sake of static typechecking, to ensure that a method
    # by the same name exists in the superclasses. It is intended to prevent the
    # class of bugs where one accidentally renames/refactors the parent method,
    # and forgets about the subclass overrides.
    # It is not necessary for overriding to actually work.
    @override
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
    
    def invalidate_buffer(self) -> None:
        """Clears the buffer and correctly rewinds position on underlying data."""
        self._pos -= len(self.__buffer)
        self.__buffer.clear()
        
    def __read_chunk(self) -> None:
        """Read a chunk of bytes from the underlying data and push them in buffer."""
        # I delegate reading self.__chunk_size bytes to Reader.read.
        # I cannot use self.read, because I have overridden the method.
        # self.read(num_bytes) is the same as type(self).read(self, num_bytes)
        self.__buffer.extend(Reader.read(self, self.__chunk_size))
        #              class ^^^^^^      ^^^^ instance

class Seekable(metaclass=ABCMeta):
    """
    An abstract (base?) class defining the seekable behaviour.
    It is kind of a mixin.
    """
    # abstract attribute (note: no initialiser)
    _pos: int 

    @abstractmethod
    def __len__(self) -> int:
        ...

    def seek(self, pos: int) -> None:
        """Sets the current data position."""
        if not 0 <= pos < len(self):
            raise IndexError(f"Invalid seek position {pos}")
        self._pos = pos



class RandomReader(Reader, Seekable):
    """A :class:`Reader` with seeking capabilities."""

    # By listing the base classes as Reader, Seekable (as opposed to Seekable, Reader),
    # the method resolution order (MRO) puts Reader before Seekable,
    # which means that when looking __len__ up on an instance of RandomReader,
    # e.g. in the first line of a call to seek(), the implementation Reader.__len__
    # is hit first, and is the one used, shadowing/overriding the
    # abstract method Seekable.__len__, hence implementing it without me having to
    # explicitly implement anything in the actual subclass RandomReader.


print(f"{RandomReader.__abstractmethods__ = }")
# RandomReader.__abstractmethods__ = frozenset() ✔

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
        self._data[self._pos:self._pos+len(data)] = data
        self._pos += len(data)
    
    def __len__(self) -> int:
        """The size of the underlying data."""
        return len(self._data)


class BufferedWriter(Writer):
    """A :class:`Writer` with buffering capabilities."""

    __buffer: bytearray
    __pos: int
    # This is _BufferedWriter__pos, no conflict with _pos (it's also not the same name!)
    # I am making an explicit point of being slightly confusing,
    # to highlight that the point of private attributes is that we don't have to
    # worry too much about naming conflicts.

    def __init__(self, data: ByteData, buffer_size: int) -> None:
        if buffer_size <= 0:
            raise ValueError("Buffer size must be strictly positive.")
        Writer.__init__(self, data)
        self.__buffer = bytearray(buffer_size)
        self.__pos = 0

    @override
    def write(self, data: bytes) -> None:
        """Writes data to the buffer, automatically flushing when overfull."""
        buffer = self.__buffer
        buf_size = len(buffer)
        num_bytes = len(data)
        buf_avail = buf_size - self.__pos
        if buf_avail >= num_bytes:
            buffer[self.__pos:self.__pos + num_bytes] = data
            self.__pos += len(data)
            return
        buffer[self.__pos:self.__pos + num_bytes] = data[:buf_avail]
        written = buf_avail
        while written < num_bytes:
            # TODO: flush
            data_chunk = data[:buf_size]
            buffer[:len(data_chunk)] = data_chunk
            written += len(data_chunk)
            self.__pos = len(data_chunk)

    def flush(self) -> None:
        """Writes the bytes currently into the buffer to the underlying bytes data."""
        Writer.write(self, self.__buffer[:self.__pos])
        self.__pos = 0
    

class RandomWriter(Writer, Seekable):
    """A :class:`Writer` with seeking capabilities."""


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

    # I can read from the underlying data, write to the underlying data,
    # pos updates are a bit weird (no seek) but nonetheless consistent,
    # and __len__ returns the same result from Reader and Writer, so no inconsistency
    # (The version from Reader is used, because of the MRO).

# C3 linearisation (MRO) of the inheritance hierarchy above Accessor:
print(f"{Accessor.__mro__ = }") # Accessor, Reader, Writer, object

# Methods and properties are stored in the class objects (Attribute and superclasses):
print(f"{Accessor.__init__ = }")
# Accessor.__init__ = <function Accessor.__init__ at 0x0000011FAC42EA30>
print(f"{Accessor.read = }")
# Accessor.read = <function Reader.read at 0x0000011FAC42D4E0>
print(f"{Accessor.write = }")
# Accessor.write = <function Writer.write at 0x0000011FAC42E1F0>
print(f"{Accessor.__len__ = }")
# Accessor.__len__ = <function Reader.__len__ at 0x0000011FAC42D640>
# Note: The version from Reader is used because Reader comes first in the MRO

# Attributes are stored on instances of Accessor:
accessor = Accessor(bytearray(5))
print(f"{accessor.__dict__ = }")
# {'_data': bytearray(b'\x00\x00\x00\x00\x00'), '_pos': 0}

# Had I not defined Accessor.__init__, the lookup for Accessor.__init__ would have gone:
# Accessor, Reader, Writer, object
# ^^^^^^^^ 1. Look for __init__ here, not found, move to next.
# Accessor, Reader, Writer, object
#           ^^^^^^ Look for __init__ here, run, done.
# Result: the __init__ of Writer is never run.
# In this example, it would ultimately do have the same result as our Accessor.__init__,
# but in general it is the wrong thing to do with initialisation.


class RandomAccessor(RandomReader, RandomWriter, Accessor):
    """An :class:`Accessor` with seeking capabilities."""

print(f"{RandomAccessor.__len__ = }")
# RandomAccessor.__len__ = <function Reader.__len__ at 0x000001BC7FD2D640>
print(f"{RandomAccessor.__abstractmethods__ = }") # frozenset()
# Indeed, let's look at the MRO of RandomAccessor:
print(f"{RandomAccessor.__mro__}")
# C3 linearisation of the inheritance hierarchy for RandomAccessor:
#                                                                       Seekable:
#                                             Accessor: Reader, Writer,
#                               RandomWriter:                   Writer, Seekable,
#                 RandomReader:                         Reader,         Seekable,
# RandomAccessor: RandomReader, RandomWriter, Accessor,
# --------------------------------------------------------------------------------------
# RandomAccessor, RandomReader, RandomWriter, Accessor, Reader, Writer, Seekable, object
#            seek ^^^^^^^^^^^^
#                                    __init__ ^^^^^^^^
#                                                  read ^^^^^^
#                                               __len__ ^^^^^^
#                                             available ^^^^^^
#                                                         write ^^^^^^

class BufferedRandomAccessor(RandomAccessor, BufferedReader, BufferedWriter):
    """A :class:`RandomAccessor` with buffering capabilities."""

    @override
    def write(self, data: bytes) -> None:
        self.invalidate_buffer() # BufferedReader.invalidate_buffer(self)
        RandomAccessor.write(self, data) # Writer.write(self, data)

    @override
    def read(self, num_bytes: int) -> bytes:
        self.flush() # BufferedWriter.flush(self)
        return RandomAccessor.read(self, num_bytes) # Reader.read(self, num_bytes)

print(f"{BufferedRandomAccessor.__mro__ = }")
# C3 linearisation of the inheritance hierarchy for BufferedRandomAccessor,
# this time using the full MROs for the three base classes, for conciseness:
#                                                                                                       BufferedWriter                                                Writer            object
#                                                                               BufferedReader                                                        Reader                    object
#                         RandomAccessor, RandomReader, RandomWriter, Accessor, BufferedReader, Reader, BufferedWriter, Writer, Seekable, object
# ----------------------------------------------------------------------------------------------------------------------------------------------
# BufferedRandomAccessor, RandomAccessor, RandomReader, RandomWriter, Accessor, BufferedReader, Reader, BufferedWriter, Writer, Seekable, object
# ^^^^^^^^^^^^^^^^^^^^^^ read
# ^^^^^^^^^^^^^^^^^^^^^^ write
#                                                            __init__ ^^^^^^^^
#                                                                           seek ^^^^^^^^^^^^
#                                                                                       __len__ ^^^^^^
#                                                                                     available ^^^^^^
