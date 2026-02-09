from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Self

if TYPE_CHECKING:
    from .user import Seller
    from .marketplace import Marketplace

type ListingState = Literal["draft", "active", "sold", "cancelled"]
"""Possible states for a listing."""

class Listing:
    """A listing in a marketplace."""

    # Immutable attributes:
    _marketplace: Marketplace
    _seller: Seller
    _uid: str

    # Internally mutable attributes:
    _state: ListingState

    # Externally mutable attributes:
    # TODO: I will refactor these into a separate container (typed dictionary),
    #       when implementing the memento pattern tomorrow.
    _title: str | None # Optional[T] is implemented as T | None
    _start_price: Decimal | None
    _description: str | None
    _min_bidding_time: timedelta | None

    def __new__(cls, marketplace: Marketplace, seller: Seller, uid: str) -> Self:
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
        self._title = None
        self._start_price = None
        self._description = None
        self._min_bidding_time = None
        return self
    
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
    def uid(self) -> str:
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
    def title(self, title: str) -> None:
        # TODO: Validate that listing is in draft.
        # Validate title length:
        if len(title) > 50:
            raise ValueError("Title must be at most 50 characters long.")
        self._title = title

    @property
    def start_price(self) -> Decimal | None:
        """The starting price of this listing."""
        return self._start_price
    
    @start_price.setter
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
    def min_bidding_time(self, time: timedelta) -> None:
        # TODO: Validate that listing is in draft.
        # Validate that minimum bidding time is at least 1 minute:
        if time < timedelta(minutes=1):
            raise ValueError("Minimum bidding time must be at least 1 minute.")
        self._min_bidding_time = time

    # Prototype pattern implementation:

    def clone(self, seller: Seller, uid: str) -> Listing:
        # Responsibility for handling the validity of the listing construction
        # is delegated to the constructor Listing.__new__:
        clone = Listing(self.marketplace, seller, uid)
        # Note: the listing clone is created in the "draft" state.
        # TODO: set additional listing attributes.
        return clone