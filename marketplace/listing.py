from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Concatenate, Literal, ParamSpec, Protocol, Self, TypeVar, TypedDict, Unpack, cast, final

from .events import EventManager, Event

if TYPE_CHECKING:
    from .user import Seller
    from .marketplace import Marketplace

type ListingState = Literal["draft", "active", "sold", "cancelled"]
"""Possible states for a listing."""

# State pattern implementation (state-dependent interfaces)

class BaseListing(Protocol):
    """A listing in any state."""

    @property
    def state(self) -> ListingState: ...

    @property
    def marketplace(self) -> Marketplace: ...

    @property
    def seller(self) -> Seller: ...

    @property
    def uid(self) -> str: ...

    def clone(self, seller: Seller) -> DraftListing: ...

    def snapshot(self) -> ListingData: ...

    @property
    def on_activate(self) -> Event[ActiveListing]: ...

    @property
    def on_sell(self) -> Event[SoldListing]: ...
    
    @property
    def on_cancel(self) -> Event[CancelledListing]: ...

class IncompleteListing(BaseListing, Protocol):
    """A listing in any state."""

    @property
    def title(self) -> str | None: ...

    @property
    def description(self) -> str | None: ...

    @property
    def start_price(self) -> Decimal | None: ...

    @property
    def min_bidding_time(self) -> timedelta | None: ...

    
class CompleteListing(BaseListing, Protocol):
    """A listing in any state."""

    @property
    def title(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def start_price(self) -> Decimal: ...

    @property
    def min_bidding_time(self) -> timedelta: ...

class DraftListing(IncompleteListing, Protocol):
    """A listing in the "draft" state."""

    @property
    def state(self) -> Literal["draft"]: ...

    def activate(self) -> ActiveListing: ...

    def cancel(self) -> CancelledListing: ...

    def restore(self, data: ListingData) -> None: ...
    
    def with_(self, **data: Unpack[ListingData]) -> Self: ...

    # TODO: add properties/methods specific to draft listings

class ActiveListing(CompleteListing, Protocol):
    """A listing in the "active" state."""

    @property
    def state(self) -> Literal["active"]: ...

    def sell(self) -> SoldListing: ...

    def cancel(self) -> CancelledListing: ...

    # TODO: add properties/methods specific to active listings

class SoldListing(CompleteListing, Protocol):
    """A listing in the "sold" state."""

    @property
    def state(self) -> Literal["sold"]: ...

    # TODO: add properties/methods specific to sold listings

class CancelledListing(IncompleteListing, Protocol):
    """A listing in the "cancelled" state."""

    @property
    def state(self) -> Literal["cancelled"]: ...

    # TODO: add properties/methods specific to cancelled listings

# Using the Listing union type instead of the concrete _Listing class
# will be an example of the dependency inversion principle in action. 

type Listing = DraftListing | ActiveListing | SoldListing | CancelledListing
"""A listing in any state."""

# Typed dictionaries are the other kind of structural type in Python,
# which can be used to define types for values in dictionaries with a predefined
# set of string keys.

class ListingData(TypedDict, total=False):
    """A container for listing data."""

    title: str
    start_price: Decimal
    description: str
    min_bidding_time: timedelta


class StateError(Exception):
    """Error raised when listing is in an unexpected state."""

    def __init__(self, state: ListingState, valid: tuple[ListingState, ...]) -> None:
        message = f"Invalid state: {state}. Valid states are: {', '.join(valid)}."
        super().__init__(message)
        # In init, typecheckers automatically infer type of attributes being set:
        self.state = state
        self.valid = valid

# A (moderately) sophisticated example of the decorator pattern.

P = ParamSpec("P")
# Parameter specification variables are a special kind of type variable
# which implements and advanced version of parametric polymorphism,
# where function argument signatures can be used parametrically.

R = TypeVar("R")
# Type variables are the vanilla ones for parametric polymorphism. 

# # First attempt at defining a decorator, for fixed state.
# def in_draft(
#         fun: Callable[Concatenate[ConcreteListing, P], R]
#     ) -> Callable[Concatenate[ConcreteListing, P], R]:
#     def inner(self: ConcreteListing, /, *args: P.args, **kwargs: P.kwargs) -> R:
#         #                            ^ self is passed positionally only
#         # If you omit it, the returned function allows self to be passed by name,
#         # which is not what the return type says.
#         if self.state != "draft":
#             raise StateError(self.state, ("draft",))
#         return fun(self, *args, **kwargs)
#     return inner

# # This is what the parametric decorator could look like, but the return type is ugly... 
# def in_state(*states: ListingState) -> Callable[
#     [Callable[Concatenate[ConcreteListing, P], R]],
#     Callable[Concatenate[ConcreteListing, P], R]
# ]:
#     if states == ("draft",):
#         return in_draft
#     raise NotImplementedError()

# To make things a bit more legible, we define a Protocol for the resulting decorators:

class ListingMethodDecorator(Protocol):
    """Interface for concrete listing method decorators"""
    def __call__(
        self,
        meth: Callable[Concatenate[ConcreteListing, P], R], /
    ) -> Callable[Concatenate[ConcreteListing, P], R]:
        """Wraps the given ConcreteListing method with a state check."""

def in_state(*states: ListingState) -> ListingMethodDecorator:
    """
    A parametric decorator which, given one or more acceptable states,
    returns a decorator which can be used to add a state check to 
    a method in :class:`ConcreteListing`.
    """
    def decorator(
        fun: Callable[Concatenate[ConcreteListing, P], R], /
    ) -> Callable[Concatenate[ConcreteListing, P], R]:
        def inner(self: ConcreteListing, /, *args: P.args, **kwargs: P.kwargs) -> R:
            if self.state not in states:
                raise StateError(self.state, states)
            return fun(self, *args, **kwargs)
        return inner
    return decorator


type ListingUID = str
"""Type alias for documentation purposes."""

@final # concrete implementation of Listing, for internal use
class ConcreteListing:
    """A listing in a marketplace."""

    _marketplace: Marketplace
    _seller: Seller
    _uid: ListingUID
    _state: ListingState
    _data: ListingData

    def __new__(cls, marketplace: Marketplace, seller: Seller, uid: sListingUIDtr) -> Self:
        # TODO: ensure that the listing is being constructed legally.
        #       Possible options:
        #       - Notify the marketplace via some callback method.
        #       - Guard this with a lock managed by the marketplace.
        #       - Ask the marketplace for a new UID (I like this the best)
        self = object.__new__(cls)
        self._state = "draft"
        self._marketplace = marketplace
        self._seller = seller
        self._uid = uid
        self._data = {}
        self._on_activate = EventManager()
        self._on_sell = EventManager()
        self._on_cancel = EventManager()
        return self

    @staticmethod
    def draft(marketplace: Marketplace, seller: Seller, uid: ListingUID) -> DraftListing:
        """Create a new listing in the "draft" state."""
        return cast(DraftListing, ConcreteListing(marketplace, seller, uid))
        #      ^^^^^^^^^^^^^^^^^ directs the static typechecker to accept the type
        # Aka: I know better than you, trust me.

    @property
    def as_listing(self) -> Listing:
        """A utility property to return a ConcreteListing as a Listing."""
        return cast(Listing, self)

    # Read-only properties:

    @property
    def marketplace(self) -> Marketplace:
        """The marketplace this listing belongs to."""
        return self._marketplace

    @property
    def seller(self) -> Seller:
        """The seller who created this listing."""
        return self._seller

    @property
    def uid(self) -> ListingUID:
        """The unique identifier for this listing."""
        return self._uid

    @property
    def state(self) -> ListingState:
        """The current state of this listing."""
        return self._state

    # Read-write properties:

    @property
    def title(self) -> str | None:
        """The title of this listing."""
        # TODO: instead of returning None,
        #       we can raise an error if we are in the "draft" state and the title is not set.
        return self._title

    @title.setter
    @in_state("draft")
    def title(self, title: str) -> None:
        # Validate title length:
        if len(title) > 50:
            raise ValueError("Title must be at most 50 characters long.")
        self._title = title

    @property
    def start_price(self) -> Decimal:
        """The starting price of this listing."""
        return self._start_price

    @start_price.setter
    @in_state("draft")
    def start_price(self, price: Decimal) -> None:
        # TODO: Validate that listing is in draft.
        # Validate that price is non-negative:
        if price < 0:
            raise ValueError("Starting price must be non-negative.")
        self._start_price = price

    @property
    def description(self) -> str | None:
        """The description of this listing."""
        return self._description

    @description.setter
    @in_state("draft")
    def description(self, description: str) -> None:
        # TODO: Validate that listing is in draft.
        # Validate description length:
        if len(description) > 500:
            raise ValueError("Description must be at most 500 characters long.")
        self._description = description

    @property
    def min_bidding_time(self) -> timedelta | None:
        """The minimum bidding time for this listing."""
        return self._min_bidding_time

    @min_bidding_time.setter
    @in_state("draft")
    def min_bidding_time(self, time: timedelta) -> None:
        # TODO: Validate that listing is in draft.
        # Validate that minimum bidding time is at least 1 minute:
        if time < timedelta(minutes=1):
            raise ValueError("Minimum bidding time must be at least 1 minute.")
        self._min_bidding_time = time

    # Builder + Fluent API pattern implementation:
    @in_state("draft")
    def with_(self, **data: Unpack[ListingData]) -> Self:
        """A fluent interface for setting listing attributes."""
        # Setting of individual data attributes is delegated to property setters:
        if "title" in data:
            self.title = data["title"]
        if "start_price" in data:
            self.start_price = data["start_price"]
        if "description" in data:
            self.description = data["description"]
        if "min_bidding_time" in data:
            self.min_bidding_time = data["min_bidding_time"]
        return self

    # Prototype pattern implementation:

    def clone(self, seller: Seller) -> DraftListing:
        # Responsibility for handling the validity of the listing construction
        # is delegated to the constructor Listing.__new__:
        marketplace = seller._marketplace
        uid = "dummy" # FIXME: we'll request this to 
        clone = ConcreteListing.draft(marketplace, seller, uid)
        # Note: the listing clone is created in the "draft" state.
        clone.restore(self.snapshot())
        return clone

    # Memento pattern implementation:

    def snapshot(self) -> ListingData:
        """Create a snapshot of the current data of a listing."""
        return self._data.copy()
    
    @in_state("draft")
    def restore(self, data: ListingData) -> None:
        """Restore a listing's data from a snapshot."""
        # TODO: check that the listing is in the "draft" state before restoring data.
        # Data setting is delegated to the 'with_' method:
        self.with_(**data)

    # State pattern implementation:

    @in_state("draft")
    def activate(self) -> ActiveListing:
        """Activate this listing."""
        self._state = "active"
        listing = cast(ActiveListing, self)
        self._on_activate.trigger(listing) # pubsub pattern in action!
        self._on_activate.clear() # activate can never be triggered again
        return listing
    
    @in_state("draft", "active")
    def cancel(self) -> CancelledListing:
        """Cancel this listing."""
        self._state = "cancelled"
        listing = cast(CancelledListing, self)
        self._on_cancel.trigger(listing) # pubsub pattern in action!
        self._on_activate.clear() # activate can never be triggered again
        self._on_sell.clear() # sell can never be triggered again
        self._on_cancel.clear() # cancel can never be triggered again
        return listing

    @in_state("active")
    def sell(self) -> SoldListing:
        """Sell this listing."""
        self._state = "sold"
        listing = cast(SoldListing, self)
        self._on_sell.trigger(listing) # pubsub pattern in action!
        self._on_activate.clear() # activate can never be triggered again
        self._on_sell.clear() # sell can never be triggered again
        self._on_cancel.clear() # cancel can never be triggered again
        return listing

    # PubSub pattern implementation:

    _on_activate: EventManager[ActiveListing]

    @property
    def on_activate(self) -> Event[ActiveListing]:
        return self._on_activate

    _on_sell: EventManager[SoldListing]

    @property
    def on_sell(self) -> Event[SoldListing]:
        return self._on_sell
    
    _on_cancel: EventManager[CancelledListing]

    @property
    def on_cancel(self) -> Event[CancelledListing]:
        return self._on_cancel
