from collections.abc import Callable
from typing import Protocol, Self


class Event[EventData](Protocol):
    
    def register(self, callback: Callable[[EventData], None]) -> None:
        """Registers a callback for the event."""

    def unregister(self, callback: Callable[[EventData], None]) -> None:
        """Unregisters a callback for the event."""


class EventManager[EventData]:

    __callbacks: dict[int, Callable[[EventData], None]]

    def __new__(cls) -> Self:
        self = object.__new__(cls)
        self.__callbacks = {}
        return self

    def register(self, callback: Callable[[EventData], None]) -> None:
        """Registers a callback for the event."""
        self.__callbacks[id(callback)] = callback

    def unregister(self, callback: Callable[[EventData], None]) -> None:
        """Unregisters a callback for the event."""
        if id(callback) in self.__callbacks:
            del self.__callbacks[id(callback)]

    def trigger(self, event_data: EventData) -> None:
        """Triggers the event."""
        for callback in self.__callbacks.values():
            callback(event_data)

    def clear(self) -> None:
        """Clears all callbacks."""
        self.__callbacks.clear()