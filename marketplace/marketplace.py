
from collections.abc import Mapping
from types import MappingProxyType
import uuid

from marketplace.listing import ConcreteListing, DraftListing, Listing, ListingUID
from marketplace.user import ListingsFolder, Seller, Username


class Marketplace:    
    """The entry point for the marketplace library (Facade pattern)."""

    _sellers: dict[Username, Seller]
    _listings: dict[ListingUID, Listing]

    @property
    def listing(self) -> Mapping[ListingUID, Listing]:
        return MappingProxyType(self._listings)
        #      ^^^^^^^^^^^^^^^^ readonly view wrapper, very cheap to construct

    # Factory pattern implementation.
    # This is where one class holds responsibility for some data or logic
    # that is necessary to the creation of another class.
    # It is implemented by means of a "factory method", 
    # a method on the "factory" which acts as the constructor for the other class.
    
    # The factory pattern can overlap with the flyweight pattern in cases where
    # the responsibility associated with the factory is to produce unique items.

    def seller(self, username: Username) -> Seller:
        """
        Factory method returning the seller by the given username in this marketplace,
        creating a new seller if one didn't exist yet.
        """
        seller = self._sellers.get(username)
        if seller is None:
            seller = object.__new__(Seller)
            seller._marketplace = self
            seller._username = username
            seller._listings = ListingsFolder()
            self._sellers[username] = seller
        return seller
    
    @property
    def _fresh_listing_uid(self) -> ListingUID:
        uid = uuid.uuid4()
        # Protects against the essential impossibility of collisions.
        while uid in self._listings:
            uid = uuid.uuid4()
        return str(uid)

    def new_draft_listing(self, seller: Seller) -> DraftListing:
        """
        Factory method returning a draft listing for the given seller,
        with a fresh listing UID. 
        """
        if seller.marketplace != self:
            raise ValueError("Seller is not in this marketplace.")
        # Factory pattern example where the Marketplace owns responsibility for a
        # piece of data (the fresh listing UID) required to create a listing.  
        uid = self._fresh_listing_uid
        listing = ConcreteListing.draft(self, seller, uid)
        # In this factory pattern example, there again is a flyweight component.
        self._listings[uid] = listing
        return listing
