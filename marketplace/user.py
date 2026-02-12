
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, Self, final
from weakref import WeakValueDictionary
from marketplace.listing import ActiveListing, CancelledListing, DraftListing, ConcreteListing, ListingUID, SoldListing
if TYPE_CHECKING:
    from .marketplace import Marketplace

type Username = str
"""A type alias for documentation purposes."""

class ListingFolderView(Protocol):
        
    @property
    def draft(self) -> Mapping[ListingUID, DraftListing]: ...
    
    @property
    def active(self) -> Mapping[ListingUID, ActiveListing]: ...
    
    @property
    def sold(self) -> Mapping[ListingUID, SoldListing]: ...
    
    @property
    def cancelled(self) -> Mapping[ListingUID, CancelledListing]: ...

class ListingsFolder:
    _stored_uids: set[Username]
    _draft: dict[Username, DraftListing]
    _active: dict[Username, ActiveListing]
    _sold: dict[Username, SoldListing]
    _cancelled: dict[Username, CancelledListing]

    def __new__(cls) -> Self:
        self = object.__new__(cls)
        self._draft = {}
        self._active = {}
        self._sold = {}
        self._cancelled = {}
        self._stored_uids = set()
        return self
    
    @property
    def draft(self) -> Mapping[ListingUID, DraftListing]:
        return MappingProxyType(self._draft)
    
    @property
    def active(self) -> Mapping[ListingUID, ActiveListing]:
        return MappingProxyType(self._active)
    
    @property
    def sold(self) -> Mapping[ListingUID, SoldListing]:
        return MappingProxyType(self._sold)
    
    @property
    def cancelled(self) -> Mapping[ListingUID, CancelledListing]:
        return MappingProxyType(self._cancelled)

    def add_draft(self, listing: DraftListing) -> None:
        if listing.uid in self._stored_uids:
            raise ValueError("Cannot add listing twice.")
        # 1. Add the listing to draft listings:
        self._draft[listing.uid] = listing
        # 2. Register state change callbacks with the listing:
        listing.on_activate.register(self.__on_activate)
        listing.on_sell.register(self.__on_sell)
        listing.on_cancel.register(self.__on_cancel)

    # By means of callbacks, the listing folder automatically tracks state
    # changes in listings, without listings having any access to it.
    # The PubSub pattern is an example of loose coupling.
    
    def __on_activate(self, listing: ActiveListing) -> None:
        assert listing.uid in self._draft
        del self._draft[listing.uid]
        self._active[listing.uid] = listing
    
    def __on_sell(self, listing: SoldListing) -> None:
        assert listing.uid in self._active
        del self._active[listing.uid]
        self._sold[listing.uid] = listing

    def __on_cancel(self, listing: CancelledListing) -> None:
        if listing.uid in self._draft:
            del self._draft[listing.uid]
        else:
            assert listing.uid in self._active
            del self._active[listing.uid]
        self._cancelled[listing.uid] = listing

@final
class Seller:
    """A seller in a marketplace."""
    
    
    _marketplace: Marketplace
    _username: Username
    _listings: ListingsFolder

    # # Flyweight pattern implementation:
    # __instances: WeakValueDictionary[tuple[Marketplace, Username], Seller] = WeakValueDictionary()

    # def __new__(cls, marketplace: Marketplace, username: Username) -> Self:
    #     instance_key = (marketplace, username)
    #     self = Seller.__instances.get(instance_key)
    #     if self is None:
    #         self = object.__new__(cls)
    #         self._marketplace = marketplace
    #         self._username = username
    #         self._listings = ListingsFolder()
    #         Seller.__instances[instance_key] = self
    #     return self


    def __new__(cls, marketplace: Marketplace, username: Username) -> Self:
        # An example of the factory pattern at work:
        return marketplace.seller(username)

    @property
    def username(self) -> Username:
        return self._username

    @property
    def marketplace(self) -> Marketplace:
        return self._marketplace
    
    @property
    def listings(self) -> ListingFolderView:
        return self._listings

    # def draft_listing(self) -> DraftListing:
    #     """Create a new listing in the "draft" state."""
    #     uid = "dummy" # FIXME: this is just a dummy value
    #     listing = ConcreteListing.draft(self._marketplace, self, uid)
    #     self._listings.add_draft(listing)
    #     return listing

    def draft_listing(self) -> DraftListing:
        """Create a new listing in the "draft" state."""
        listing = self._marketplace.new_draft_listing(self)
        self._listings.add_draft(listing)
        return listing


@final
class Buyer:
    """A buyer in a marketplace."""
    _marketplace: Marketplace
    _username: Username

    @property
    def username(self) -> Username:
        return self._username

    @property
    def marketplace(self) -> Marketplace:
        return self._marketplace