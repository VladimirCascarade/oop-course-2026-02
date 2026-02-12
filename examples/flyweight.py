"""
Introduction to the Flyweight patter, where unique live instances exist for a given
instance key at runtime.
"""

from typing import Self, final
from weakref import WeakValueDictionary

@final
class Vec2:
    """
    A flyweight implementation of 2-dim integer vectors:
    for each given `(x, y)` pair, at most one unique instance of :class:`Vec2` exists. 
    """

    # To implement the flyweight pattern, you need a live instance "dictionary":
    # This should be global from the point of view of instances of Vec2,
    # but it should be local to the Vec2 class/context. Solution: a class attribute.

    # __instances: dict[tuple[int, int], Vec2] = {}
    # A dict is not right for this: it holds strong references to both keys and values,
    # and therefore once instances are stored here they cannot be garbage collected.
    # The key word is "live" instances: you don't want to keep zombie instances.
    __instances: WeakValueDictionary[tuple[int, int], Vec2] = WeakValueDictionary()
    #            ^^^^^^^^^ holds weak references to its values, gc disregards those

    x: int
    y: int

    __slots__ = ("__weakref__", "x", "y")
    #             ^^^^^^^^^^^ special slot name to enable support for weak references
    # The reason why weakref support is optional is that the pointers get a little
    # but fatter for this class (a weakref counter is added to the address and strong
    # reference counter that are always present in a garbage-collected language.)

    def __new__(cls, x: int, y: int) -> Self:
        # Flyweight pattern.
        # 1. Look up whether a live instance for (x, y) exists:
        self = Vec2.__instances.get((x, y))
        # 2. If no live instance exists, create one:
        if self is None:
            # 2.1. Create the new instance and set its attributes:
            self = object.__new__(cls)
            self.x = x
            self.y = y
            # 2.2. Store the new instance in the global instance dictionary:
            Vec2.__instances[(x, y)] = self
        # 3. Return the live instance:
        return self
        # If you use Self, mypy complains, because values in __instances are typed as
        # Vec2, not as its subclasses. This can be solved, but inheritance with the
        # flyweight pattern is really tricky, and common practice is to set any
        # flyweight class to be final (so Self is the same as Vec2).
        # If you want to see how the general case is handled,
        # you might wish to look up the hashcons library (disclosure: I am the author).
    
    def __repr__(self) -> str:
        return f"Vec2({self.x}, {self.y})"
    
u = Vec2(5, 3)
v = Vec2(5, 3)
print(f"{u is v = }") # True
print(f"{u == v = }") # True
# Equals means identical by default, but because of Flyweight instances which should
# be equal are always identical, so you don't need to implement __eq__ or __hash__.
