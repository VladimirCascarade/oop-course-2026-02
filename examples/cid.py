"""
A classic example of single inheritance: trees.

Additionally, some considerations on private attributes used for caching,
using content-addressing (Content IDs) as an example.

As a data model I will use trees of tuples with integers as leaves.
"""

# ABC (Abstract Base Class) framework provides the following primitives:
# - A way to mark methods as not implemented, trackable at type-checking and runtime
# - A way to automatically make classes not instantiatable if they have missing methods

# The most common way to make a class into a (potentially) ABC is to use the ABC base,
# > from abc import ABC
# But this is an illusion, and the real mechanic is provided by a metaclass:
# > from abc import ABCMeta
# This is a story about class object modification, so we must look at the
# class of a class, i.e. a metaclass.

from abc import ABC, ABCMeta, abstractmethod
from hashlib import sha3_256
from typing import Self

class Tree(metaclass=ABCMeta):
    #      ^^^^^^^^^^^^^^^^^ the Tree class object is an instance of ABCMeta
    """Abstract base class for a tree with tuples as nodes and integers as leaves."""

    @property
    @abstractmethod
    def cid(self) -> bytes:
        """Cryptographic Content ID (CID) for this tree."""

    # A CID is the sort of thing that you expect to be "attribute-like",
    # so a property is a good choice for it, and you also expect to be cheapish.

class Leaf(Tree):
    """Concrete class for tree leaves."""
    _data: int
    __cid: bytes | None # a place to store a CID after first computation
    # Because it might not be used by every user of our library,
    # we make a design choice to compute CIDs on-demand rather than in constructor.

    def __new__(cls, data: int) -> Self:
        if data < 0:
            raise ValueError("Data must be unsigned integer.")
        if data.bit_length() > 256:
            raise ValueError("Data must be 256-bit unsigned integer.")
        self = Tree.__new__(cls)
        self._data = data
        self.__cid = None # no cached value, CID computed on-demand
        return self    

    @property
    def cid(self) -> bytes:
        # 1. Look up the cached value:
        cid = self.__cid
        # 2. If no cached value, compute it and cache it:
        if cid is None:            
            data = b"l"+self._data.to_bytes(32, byteorder="little")
            #      ^^^^ domain separator byte
            self.__cid = cid = sha3_256(data).digest()
        #   ^^^^^^^^^^^^^^^^^^ assigns to cid name and to self.__cid attr
        #   It is a special chained assignment statement.
        # 3. Return the value:
        return cid

class Node(Tree):
    """Concrete class for internal tree nodes."""
    _children: tuple[Tree, ...]
    __cid: bytes | None

    def __new__(cls, *children: Tree) -> Self:
        self = Tree.__new__(cls)
        self._children = children
        self.__cid = None
        return self
    
    @property
    def cid(self) -> bytes:
        cid = self.__cid
        if cid is None:            
            data = b"n"+b"".join(child.cid for child in self._children)
            #      ^^^^ domain separator byte
            self.__cid = cid = sha3_256(data).digest()
        return cid 

    # The natural implementation of cid for deep trees is recursive,
    # and as a consequence it is very expensive (linearly so in size of tree).
    # The cached version keeps the same exact design, but avoids the wasted work
    # by looking up previously computed values.

print(f"{Tree = }") # Tree = <class '__main__.Tree'>
print(f"{id(Tree) = :#x}") # id(Tree) = 0x155185734b0
print(f"{Tree.__mro__ = }") # (Tree, object)
print(f"{type(object) = }") # type
print(f"{type(Tree) = }") # ABCMeta
print(f"{ABCMeta.__mro__ = }") # (ABCMeta, type, object)
# type-theoretic weirdness where type is a subclass of object.
print(f"{ABC.__mro__ = }") # (ABC, object)

# One way to conceptualise the difference between super-classes and meta-classes is:
# - a subclass is like a subset (a subset of instances)
# - a metaclass instance is like an element of a set (a set of classes)
# If S is a subclass of T, the instances of S are a subset of the instances of T.
# If S is an instance of metaclass M, the instance S is an element of the set of
# instances of metaclass M.
# If obj is an instance of class T, the instance obj is an element of the set of
# instance of class T.

# How does ABC meta keep track of methods which need to be implemented?

print(f"{dir(Tree) = }") # ['__abstractmethods__', ...]
print(f"{Tree.__abstractmethods__ = }") # frozenset({'cid'})
print(f"{Leaf.__abstractmethods__ = }") # frozenset()

leaf = Leaf(10)
# Leaf.__call__(10)
# -> if Leaf.__abstractmethods__: raise TypeError()
# -> Leaf.__new__(Leaf, 10)

# Private attributes are name-mangled to avoid accidental conflicts with subclass
# attributes by the same name.
# They are ** truly ** private storage for the class itself,
# while protected ones are shared by all subclasses (it's the same memory slot)

print(f"{dir(leaf) = }") # dir(leaf) = ['_Leaf__cid', '_data', 'cid']
#   name-mangled private attribute __cid ^^^^^^^^^^
print(f"{leaf._data = }") # 10
print(f"leaf.cid = 0x{leaf.cid.hex()}")
# 0xf301e19dec0fb3be42508fee17faa016019cf6a7948658643a49c1d1aa80e95c
try:
    print(f"{leaf.__cid = }") 
    # Typechecker (incorrectly) doesn't flag this, but it will raise AttributeError.
    # The issue is that it is legitimate for a '__cid' attribute to have been dynamic'ly
    # defined on the object from outside of the class body, which wouldn't be mangled.
except AttributeError as e:
    print(f"AttributeError: {e}")
    # AttributeError: 'Leaf' object has no attribute '__cid'

def name_mangle(cls: type, attrname: str) -> str:
    """Name mangling logic for private names defined within a class body."""
    if attrname.startswith("__") and not attrname.endswith("__"):
        return f"_{cls.__name__}{attrname}"
    return attrname