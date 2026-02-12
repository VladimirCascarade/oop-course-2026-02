"""
A brief discussion of where things are stored in class object vs class instances.
"""

from typing import Self, final
from weakref import WeakValueDictionary

@final
class Vec2:
    __instances: WeakValueDictionary[tuple[int, int], Vec2] = WeakValueDictionary()

    x: int
    y: int

    # I omitted slots because I want to explicitly show you where the instance
    # attributes are stored in cases where instance __dict__ is used.
    # By default, custom classes enable __dict__ and __weakref__.

    def __new__(cls, x: int, y: int) -> Self:
        #       ^^^ This looks like a classmethod,
        #           but it is a static method with a class as first argument.
        self = Vec2.__instances.get((x, y))
        if self is None:
            self = object.__new__(cls)
            self.x = x
            self.y = y
            Vec2.__instances[(x, y)] = self
        return self
    
    def __str__(self) -> str:
        return f"Vec2({self.x}, {self.y})"
    

u = Vec2(5, 3)

# Vec2 class object and its members:
print(f"{Vec2 = }")
# Vec2 = <class '__main__.Vec2'>
print(f"{id(Vec2) = :#X}")
# id(Vec2) = 0X1F67356C7B0
print(f"{Vec2.__dict__ = }")
# Vec2.__dict__ = mappingproxy({
#   '__module__': '__main__',
#   '__firstlineno__': 8,
#   '_Vec2__instances': <WeakValueDictionary at 0x1f6743d9940>,
#   '__new__': <staticmethod(<function Vec2.__new__ at 0x000001F6744EE770>)>,
#   '__str__': <function Vec2.__str__ at 0x000001F674509010>,
#   '__annotate_func__': <function Vec2.__annotate__ at 0x000001F6745090C0>,
#   '__static_attributes__': ('x', 'y'),
#   '__dict__': <attribute '__dict__' of 'Vec2' objects>,
#   '__weakref__': <attribute '__weakref__' of 'Vec2' objects>,
#   '__doc__': None,
#   '__final__': True
# })

# u instance object and its members: 
print(f"{u = }")
# u = <__main__.Vec2 object at 0x000001F6744BD6A0>
print(f"{id(u) = :#X}")
# id(u) = 0X1F6744BD6A0
print(f"{u.__dict__ = }")
# u.__dict__ = {'x': 5, 'y': 3}

# If you use __slots__ (__dict__ is disable by default in that case),
# then the instance attribute getters, setters and deleters are handled by
# some class-level descriptors (akin to property getters, setters and deleters).
