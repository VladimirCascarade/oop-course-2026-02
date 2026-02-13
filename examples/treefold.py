"""
An implementation of the Visitor pattern, using tree folds.

Visitor pattern: a safe way to expose complex data structure internals by
taking a "visitor" object and controlling its "visit" to the internals,
e.g. guaranteed certain non-trivial invariants/properties of the visit.

The logic of the visitor is entirely in the hands of the caller to the visit function,
in this case to the caller of the Tree.fold method. They can do whatever they want,
as long as the interface match. The entire point of the visitor pattern is to insulate
the data structure internals from whatever logic the visitor implementer has chosen.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import Protocol, Self

type frozenlist[T] = tuple[T, ...]
#         variadic tuple type ^^^
"""
A type alias for immutable lists which matches the set/frozenset duality.
It avoids having to write ... every time for variadic tuples (which confuses everyone).
"""

# # The simplified version of a list fold (aka reduce):
# def list_fold[StateT, ItemT](
#     items: list[ItemT],
#     init: StateT,
#     update: Callable[[StateT, ItemT], StateT],
# ) -> StateT:
#     state = init
#     for item in items:
#         state = update(state, item)
#     return state

# The version of list fold which matches the same pattern as tree fold:
def list_fold[StateT, ItemT](
    items: list[ItemT],
    init: Callable[[], StateT], # corresponds to init_leaf
    update: Callable[[StateT, ItemT], StateT], # corresponds to update_node
) -> StateT:
    state = init()
    for item in items:
        state = update(state, item)
    return state

class TreeFoldVisitor[StateT, ItemT](Protocol):
    """
    Interface for a visitor object which can be used to perform a tree fold.
    """
    # An example of dependency inversion and/or interface segregation:
    # Users of fold don't need to directly know about my interface,
    # as long as they implement methods with the correct identifiers/signatures.

    def init_leaf(self, value: ItemT) -> StateT: ...
    def update_node(self, *child_states: StateT) -> StateT: ...


class Tree[ItemT](metaclass=ABCMeta):

    __slots__ = ("__weakref__",)
    
    @abstractmethod
    def fold[StateT](self, visitor: TreeFoldVisitor[StateT, ItemT]) -> StateT: ...

class Node[ItemT](Tree[ItemT]):

    _children: frozenlist[Tree[ItemT]]

    __slots__ = ("_children",)

    def __new__(cls, *children: Tree[ItemT]) -> Self:
        self = object.__new__(cls)
        self._children = children
        return self

    def fold[StateT](self, visitor: TreeFoldVisitor[StateT, ItemT]) -> StateT:
        # child_states = tuple(child.fold(visitor) for child in self._children)
        # return visitor.update_node(*child_states)
        return visitor.update_node(*(child.fold(visitor) for child in self._children))
        #                          ^ spread the iterator onto the variable args
        #                  iterator ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
class Leaf[ItemT](Tree[ItemT]):

    _value: ItemT

    __slots__ = ("_value",)

    def __new__(cls, value: ItemT) -> Self:
        self = object.__new__(cls)
        self._value = value
        return self

    def fold[StateT](self, visitor: TreeFoldVisitor[StateT, ItemT]) -> StateT:
        return visitor.init_leaf(self._value)

# You can make it more complicated by adding indices, but it's not necessary,
# because the visitor can keep track of that themselves.

# To prove to you that the fold implementation above has access to all the tree info,
# I can implement a tree_clone visitor which returns a clone of the tree.

class TreeCloneVisitor[ItemT]:
    
    def init_leaf(self, value: ItemT) -> Leaf[ItemT]:
        return Leaf(value)

    def update_node(self, *child_states: Tree[ItemT]) -> Node[ItemT]:
        return Node(*child_states)

def clone_tree[ItemT](tree: Tree[ItemT]) -> Tree[ItemT]:
    visitor: TreeCloneVisitor[ItemT] = TreeCloneVisitor()
    return tree.fold(visitor)

class TreeSumVisitor:
    
    def init_leaf(self, value: int) -> int:
        return value

    def update_node(self, *child_states: int) -> int:
        return sum(child_states)

def tree_sum(tree: Tree[int]) -> int:
    visitor = TreeSumVisitor()
    return tree.fold(visitor)

