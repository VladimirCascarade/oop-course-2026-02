
from typing import TYPE_CHECKING
from marketplace.listing import DraftListing, ConcreteListing
if TYPE_CHECKING:
    from .marketplace import Marketplace

class Seller:
    """A seller in a marketplace."""
    _marketplace: Marketplace

    @property
    def marketplace(self) -> Marketplace:
        return self._marketplace

    def draft_listing(self) -> DraftListing:
        """Create a new listing in the "draft" state."""
        uid = "dummy" # FIXME: this is just a dummy value
        return ConcreteListing.draft(self._marketplace, self, uid)
