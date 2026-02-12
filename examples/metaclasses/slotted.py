"""A metaclass automating the process of creating slots for annotated attributes."""

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from abc import ABCMeta
from collections import deque
from collections.abc import Iterable
from typing import Any


def all_ancestor_classes(classes: tuple[type, ...]) -> set[type]:
    """The set of all ancestors of the given sequence of classes (incl. themselves)."""
    ancestors = set(classes)
    q = deque(classes)
    while q:
        t = q.popleft()
        new_bases = tuple(s for s in t.__bases__ if s not in ancestors)
        ancestors.update(new_bases)
        q.extend(new_bases)
    return ancestors


def weakref_slot_present(bases: tuple[type, ...]) -> bool:
    """Whether a class with given bases has ``__weakref__`` in its slots."""
    return any(
        "__weakref__" in getattr(cls, "__slots__", {})
        for cls in all_ancestor_classes(bases)
    )


def namespace_union(classes: Iterable[type]) -> dict[str, Any]:
    """
    Union of namespaces from the given classes, with names from earlier classes in the
    iterable shadowing the same names from later classes (if any).
    """
    classes = reversed(tuple(classes))
    namespace: dict[str, Any] = {}
    for base in classes:
        namespace.update(base.__dict__)
    return namespace


def class_slots(cls: type) -> tuple[str, ...] | None:
    """
    Returns a tuple consisting of all slots for the given class and all
    non-private slots for all classes in its MRO.
    Returns :obj:`None` if slots are not defined for the class.
    """
    if not hasattr(cls, "__slots__"):
        return None
    slots: list[str] = list(cls.__slots__)
    for cls in cls.__mro__[1:-1]:
        for slot in getattr(cls, "__slots__", ()):
            assert isinstance(slot, str)
            if slot.startswith("__") and not slot.endswith("__"):
                continue
            slots.append(slot)
    return tuple(slots)


class SlottedMeta(ABCMeta):
    """A metaclass automating the process of creating slots for annotated attributes."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> Any:
        # The trick of this metaclass is to edit the namespace
        # - after the user has written the class body
        # - but before the type.__new__ constructor assembles the class object
        annotations: dict[str, Any] = namespace.setdefault("__annotations__", {})
        if "__slots__" in namespace:
            raise TypeError("Class __slots__ should not be explicitly declared.")
        slots: list[str] = []
        if not weakref_slot_present(bases):
            slots.append("__weakref__")
        extended_namespace = namespace_union(bases) | namespace
        slots.extend(
            attr_name
            for attr_name in annotations
            if attr_name not in extended_namespace
        )
        namespace["__slots__"] = tuple(slots)
        cls = type.__new__(mcs, name, bases, namespace)
        # the type.__new__ constructor does the heavy lifting
        return cls
