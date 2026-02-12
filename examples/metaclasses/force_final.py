"""A metaclass forcing only final classes to be instantiated."""

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
from typing import Any, Type

class ForceFinalMeta(ABCMeta):
    """A metaclass forcing only final classes to be instantiated."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> Any:
        cls = super().__new__(mcs, name, bases, namespace)
        cls.__final__ = False
        return cls

    __final__: bool
    """Whether the class is marked final."""

    def __call__[_T](cls: Type[_T], *args: Any, **kwargs: Any) -> _T:
        assert isinstance(cls, ForceFinalMeta)
        if not cls.__final__:
            raise TypeError(
                f"Class {cls.__name__} is not final, so it cannot be instantiated."
            )
        return cls.__new__(cls, *args, **kwargs)
    