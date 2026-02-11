"""Data structure for bid stack."""

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Self
from .utils.stack import WithdrawableStack
if TYPE_CHECKING:
    from .user import Buyer
    # from .listing import ActiveListing

type Price = Decimal # TODO: This is just a dummy for future changes.

# A bid is a classic example of low-level data which should be modelled as immutable,
# because it is passed around between various parts of the library.
# The correct choice for immutable low-level structured data containers is...
# ... a frozen dataclass
@dataclass(frozen=True, slots=True)
class Bid:
    """A bid."""
    buyer: Buyer
    price: Price

class BidStack:
    """A stack of bits on listings."""

    __bids: WithdrawableStack[Bid]
    # An example of composition over inheritance.
    # A BidStack is ** not ** a WithdrawableStack[Bid], behaviourally.
    __buyer_bids: dict[Buyer, Bid]

    def __new__(cls) -> Self:
        self = object.__new__(cls)
        self.__bids = WithdrawableStack()
        self.__buyer_bids = {}
        return self
    
    @property
    def top(self) -> Bid | None:
        # Here, we can use None as a flag value because a Bid cannot be None.
        """Returns the top bid, or None if no bids are present."""
        return self.__bids.peek() if self else None
    
    def place(self, bid: Bid) -> bool:
        """
        Attempts to place a new bid on the bid stack, if price is strictly higher
        than price for top bid. Returns whether bid was placed successfully. 
        """
        top = self.top
        if top and bid.price <= top.price:
            return False
        self.withdraw(bid.buyer) # delegate withdrawal of any previous bid to withdraw
        self.__bids.push(bid)
        self.__buyer_bids[bid.buyer] = bid
        return True

    def withdraw(self, buyer: Buyer) -> bool:
        """
        Withdraws the bid by a buyer if present. Returns whether it was present. 
        """
        bid = self.__buyer_bids.get(buyer)
        if not bid:
            return False
        self.__bids.remove(bid)
        del self.__buyer_bids[buyer]
        return True


    def __bool__(self) -> bool:
        """Whether there are bids."""
        return bool(self.__bids)
