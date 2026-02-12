"""
A custom implementation of super, for teaching purposes.
https://rhettinger.wordpress.com/2011/05/26/super-considered-super/
"""

# The code below works in CPython, but it uses advanced reflection techniques
# and so it might not work on other runtimes (e.g. mypyc compiled code).

import inspect
from types import FunctionType, MethodType
from typing import Any, ClassVar, Self, final, override

@final
class mysuper:
    """A custom implementation of super, for teaching purposes."""

    __method_class: type
    """ The class owning the method within which has mysuper() been called. """

    __instance: Any
    """ The specific instance upon which the method has been called. """

    __instance_class: type
    """ The actual class of the instance, a subclass of __method_class. """

    def __new__(cls) -> Self:
        """ Constructs the mysuper object. """
        self = object.__new__(cls)
        # 1. Get the scope of the method call
        #    within which mysuper() is being constructed:
        scope = inspect.getouterframes(inspect.currentframe())[1].frame
        # 2. Load the 'self' of the method call
        #    within which mysuper() is being constructed:
        instance = scope.f_locals["self"]
        # 3. Get the name of the class owning the method
        #    within whose scope mysuper() is being constructed:
        method_class_name = ".".join(scope.f_code.co_qualname.split(".")[:-1])
        # 4. Get the class owning the method:
        method_class = next(
            cls for cls in type(instance).__mro__
            if cls.__qualname__ == method_class_name
        )
        # 5. Store the class, instance and concrete class of the instance:
        self.__method_class = method_class
        self.__instance = instance
        self.__instance_class = type(instance)
        return self

    def __getattr__(self, name: str) -> Any:
        """
        This method is called to resolve arbitrary attribute lookups,
        e.g. in mysuper().greet, we have name = "greet".        
        """
        # 1. Take the MRO of __instance_class:
        mro = self.__instance_class.__mro__
        # 2. Go to the index of __method_class in the MRO:
        idx = mro.index(self.__method_class)
        # 3. Start looking for the method from the next class in that MRO:
        print(
            f"Looking for {name} "
            f"in {self.__instance_class.__name__}.__mro__ "
            f"starting from {mro[idx+1].__name__}:\n"
            f"    {self.__instance_class.__name__}.__mro__ = "
            f"{', '.join(c.__name__ for c in self.__instance_class.__mro__)}"
        )
        # 4(a). If the method is found, return first occurrence, bound to instance:
        for cls in mro[idx+1:]:
            if hasattr(cls, name):
                print(f"    {cls.__name__}.{name} ✔️")
                attr = getattr(cls, name)
                if isinstance(attr, FunctionType):
                    return MethodType(attr, self.__instance) # bind the instance
                return attr
            print(f"    {cls.__name__}.{name} ❌")
        # 4(b). If the method is not found, raise AttributeError
        raise AttributeError() # method not found

    def __repr__(self) -> str:
        return (
            "<super: "
            f"<class {self.__method_class.__name__!r}>, "
            f"<{self.__instance_class.__name__} object>>"
        )

# == Demonstration of mysuper at work ==

class A:

    x: ClassVar[str] = "A"

    def greet(self) -> None:
        print("Greetings from A!")

class B(A):

    @override
    def greet(self) -> None:
        print("Greetings from B!")

class C(A):

    x: ClassVar[str] = "C"
    y: ClassVar[str] = "C"

class D(B, C):

    @override
    def greet(self) -> None:
        print(f"In D.greet(): {mysuper() = }")
        print(f"In D.greet(): {mysuper().x = }")
        print(f"In D.greet(): {mysuper().y = }")
        mysuper().greet()
        print("... and greetings from D!")

class E(D): ...

E().greet()
# In D.greet(): mysuper() = <super: <class 'D'>, <E object>>
# Looking for x in E.__mro__ starting from B:
#     E.__mro__ = E, D, B, C, A, object
#     B.x ✔️
# In D.greet(): mysuper().x = 'A'
# Looking for y in E.__mro__ starting from B:
#     E.__mro__ = E, D, B, C, A, object
#     B.y ❌
#     C.y ✔️
# In D.greet(): mysuper().y = 'C'
# Looking for greet in E.__mro__ starting from B:
#     E.__mro__ = E, D, B, C, A, object
#     B.greet ✔️
# Greetings from B!
# ... and greetings from D!
