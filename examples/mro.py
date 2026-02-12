"""
The MRO (Method Resolution Order) is the algorithm used by Python to determine
the order in which methods are looked up amongst superclasses of a class.

References:

- https://www.python.org/download/releases/2.3/mro/
- https://en.wikipedia.org/wiki/C3_linearization

"""

from __future__ import annotations

print("=== MRO EXAMPLES ===")

class ex_2:
    class O: # noqa: E742 # noqa: E742
        pass
    class X(O):
        pass
    class Y(O):
        pass
    class A(X,Y):
        pass
    class B(Y,X):
        pass
    print("\n== MRO Example 2 ==")
    print(f"     O.__mro__: {''.join(cls.__name__ for cls in O.__mro__[:-1])}")
    print(f"  X(O).__mro__: {''.join(cls.__name__ for cls in X.__mro__[:-1])}")
    print(f"  Y(O).__mro__: {''.join(cls.__name__ for cls in Y.__mro__[:-1])}")
    print(f"A(X,Y).__mro__: {''.join(cls.__name__ for cls in A.__mro__[:-1])}")
    print(f"B(Y,X).__mro__: {''.join(cls.__name__ for cls in B.__mro__[:-1])}")
    try:
        class Z(A,B): # type: ignore
            pass #creates Z(A,B) in Python 2.2
    except TypeError:
        pass # Z(A,B) cannot be created in Python 2.3
    print("No consistent MRO for Z(A,B).")

def _mro_str(cls: type) -> str:
    assert all(len(c.__name__) == 1 for c in cls.__mro__[:-1])
    return "".join(c.__name__ for c in cls.__mro__[:-1])

def _aligned_mro_str(cls: type, subcls: type) -> str:
    assert issubclass(subcls, cls), (cls, subcls)
    assert tuple(c for c in subcls.__mro__ if c in cls.__mro__) == cls.__mro__
    assert all(len(c.__name__) == 1 for c in subcls.__mro__[:-1])
    return "".join(
        c.__name__ if c in cls.__mro__ else " "
        for c in subcls.__mro__[:-1]
    )#+" = "+_mro_str(cls)

class ex_5:
    class O: # noqa: E742
        pass
    class F(O):
        pass
    class E(O):
        pass
    class D(O):
        pass
    class C(D,F):
        pass
    class B(D,E):
        pass
    class A(B,C):
        pass
    print("\n== MRO Example 5 ==")
    print(f"     O.__mro__: {_aligned_mro_str(O, A)}")
    print(f"  F(O).__mro__: {_aligned_mro_str(F, A)}")
    print(f"  E(O).__mro__: {_aligned_mro_str(E, A)}")
    print(f"  D(O).__mro__: {_aligned_mro_str(D, A)}")
    print(f"C(D,F).__mro__: {_aligned_mro_str(C, A)}")
    print(f"B(D,E).__mro__: {_aligned_mro_str(B, A)}")
    print(f"A(B,C).__mro__: {_mro_str(A)}")

class ex_6:
    class O: # noqa: E742
        pass
    class F(O):
        pass
    class E(O):
        pass
    class D(O):
        pass
    class C(D,F):
        pass
    class B(E,D):
        pass
    class A(B,C):
        pass
    print("\n== MRO Example 6 ==")
    print(f"     O.__mro__: {_aligned_mro_str(O, A)}")
    print(f"  F(O).__mro__: {_aligned_mro_str(F, A)}")
    print(f"  E(O).__mro__: {_aligned_mro_str(E, A)}")
    print(f"  D(O).__mro__: {_aligned_mro_str(D, A)}")
    print(f"C(D,F).__mro__: {_aligned_mro_str(C, A)}")
    print(f"B(E,D).__mro__: {_aligned_mro_str(B, A)}")
    print(f"A(B,C).__mro__: {_mro_str(A)}")

class ex_9:
    class O: # noqa: E742
        pass
    class A(O):
        pass
    class B(O):
        pass
    class C(O):
        pass
    class D(O):
        pass
    class E(O):
        pass
    class F(A,B,C):
        pass
    class G(D,B,E):
        pass
    class H(D,A):
        pass
    class Z(F,G,H):
        pass
    print("\n== MRO Example 9 ==")
    print(f"       O.__mro__: {_aligned_mro_str(O, Z)}")
    print(f"    C(O).__mro__: {_aligned_mro_str(C, Z)}")
    print(f"    B(O).__mro__: {_aligned_mro_str(B, Z)}")
    print(f"    A(O).__mro__: {_aligned_mro_str(A, Z)}")
    print(f"    D(O).__mro__: {_aligned_mro_str(D, Z)}")
    print(f"    E(O).__mro__: {_aligned_mro_str(E, Z)}")
    print(f"  H(D,A).__mro__: {_aligned_mro_str(H, Z)}")
    print(f"G(D,B,E).__mro__: {_aligned_mro_str(G, Z)}")
    print(f"F(A,B,C).__mro__: {_aligned_mro_str(F, Z)}")
    print(f"Z(F,G,H).__mro__: {_mro_str(Z)}")
