# Visibility modifiers in Python are a convention
# name: public
# _name: protected (visible to subclasses)
# __name: private (name-mangled to avoid conflicts with subclasses)
# __name__: special/dunder (reserved system name)

from math import gcd
from typing import Self

# If you decorate Frac as @final, you can use Self and the typecheckers know that
# Self is exactly Frac, because no subclasses can be defined.

class Frac:
    """A basic implementation of a fraction."""

    # Data:

    _num: int
    _den: int # always > 0

    # Constructor (enforces invariants):
    # Note: __new__ is the real constructor,
    #       __init__ is the initialiser (not used in this course)
    def __new__(cls, num: int, den: int) -> Self:
        #                                   ^^^^ the class cls itself.
        #       ^^^ could be Frac, or any subclass F of Frac.
        # 1. Validate arguments:
        if den == 0:
            raise ZeroDivisionError()
        # 2. Standardise arguments:
        if den < 0:
            num, den = -num, -den
        # 3. Create a blank instance:
        self = object.__new__(cls) # creates a blank object of class 'cls'
        # 4. Set values for instance attributes:
        self._num = num
        self._den = den
        # 5. Return the instance:
        return self

    # Properties:
    # Provide safe (read-only) access to internal data for an immutable fraction.

    @property
    def num(self) -> int:
        """The fraction's numerator."""
        return self._num
    
    @property
    def den(self) -> int:
        """The fraction's denominator."""
        return self._den

    # (Instance) methods:

    def reduced(self) -> Frac:
        """Returns a new fraction with coprime numerator and denominator."""
        num, den = self.num, self.den
        g = gcd(num, den)
        return Frac(num//g, den//g)
    
    # Special/dunder methods:

    def __add__(self, other: Frac) -> Frac:
        """
        Returns the sum of this fraction and another. (Result is not reduced.)
        
        Implements the + binary operator.
        """
        return Frac(self.num * other.den + self.den * other.num, self.den * other.den)
    
    def __float__(self) -> float:
        """
        Returns the fraction's value as a float.
        
        Implements the builtin float() conversion function.
        """
        return self.num / self.den

    def __str__(self) -> str:
        """
        Returns a string representation of the fraction.
        
        Implements the builtin str() conversion function.
        """
        if self.den == 1:
            return str(self.num)
        return f"{self.num}/{self.den}"
    