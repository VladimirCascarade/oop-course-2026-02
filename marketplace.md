# OOP Exercises

This week's exercises will guide you through a mock implementation of a basic backend for online marketplaces.
In tackling the exercises, you might wish to follow the specifications given in the [Sample Assignment](./sample-oop-assignment.pd).

# Specification

There are two kinds of users in a marketplace, identified by a unique username:

- sellers, who list items for sale
- buyers, who bid on items

A buyer and a seller can have the same username, and they need not be related as far as this specification is concerned.
Below is the typical lifecycle of a listing in a marketplace:

1. A seller creates the listing (in draft state).
   At creation, the listing is assigned a Unique ID within a marketplace.
   The following data needs to be specified for a listing:

   - title, a string of max length 50
   - start price, a [`Decimal`](https://docs.python.org/3/library/decimal.html#decimal-objects)
   - description, a string of max length 500
   - min bidding time, a [`timedelta`](https://docs.python.org/3/library/datetime.html#timedelta-objects)

   Some or all of this data can be specified and modified after creation.

2. The seller can change the listing state from draft to active at any time, as long as all data from point 1 above has been specified. Alternatively, the seller can change the lifting state from draft to cancelled.

3. When the listing is active, buyers can submit bids. Only the current highest bid is visible to buyers. Each buyer can have at most one bid on the listing at any time and can withdraw their bid at any time. A new bid can be submitted only if it is higher than the highest current bid.

4. After the minimum bidding time has elapsed from the moment the listing has become active, the seller can change the listing state from active to sold, as long as at least one bid is present: when this happens, the buyer with the highest bid has bought the item. At any time when no bids are present, the seller can change the listing state from active to cancelled.

A `Marketplace` class should act as the entry point to your library, such that all data and actions for a single marketplace should ultimately be accessible starting from a corresponding `Marketplace` instance.
This is an example of the **Façade Pattern**, where a library or application has a single entry point which provides access to all of its functionality.

The library should offer the following core functionality:

- Creation of listings, either brand new or from existing listings.
- Access to marketplace listings by ID.
- Editing of listing data, with undo functionality.
- Changes to listing state.
- Submission and management of bids on a listing.
- Access to the draft, active, sold and cancelled listings of a seller.
- Access the current bids on active listings of a buyer, and the listings that a buyer has bought.
- Event subscription functionality, where can request to be notified of the following events:
  - changes in state for a listing
  - changes in bids for a listing
- Keeping track of the total amount of money that a seller has made from sold listing.
- Keeping track of the total amount of money that a buyer has spent on bought listings, and the total amount of money that a buyer currently has on highest bids for active listings.

Data management and actions for distinct clusters of marketplace functionality should be delegated to distinct classes.
This is according to the **Single Responsibility Principle**: every component &mdash; module, class, method, function &mdash; should have a single well-defined responsibility (at the corresponding level of abstraction).

# Implementation

Tree of public modules, classes and types for this mini-project:

```
marketplace
├── __init__.py
├── listings.py
│   └── Listing
├── bids.py
│   ├── Bid
│   └── BidStack
├── users.py
│   ├── Buyer
│   └── Seller
├── marketplaces.py
│   └── Marketplace
└── utils
    ├── __init__.py
    ├── stacks.py
    │   └── WithdrawableStack
    └── time_server.py
        └── TimeServer
```

## Part 1 - Listings

Implement a `Listing` class responsible for all listing-related functionality.

You will need to reference the `Seller` and `Buyer` classes from `marketplace.users` in some of your type hints: to avoid circular imports in your modules, you should import these classes solely for static type-checking purposes, as shown below.

```py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .users import Buyer, Seller
```

### Listing creation

Implement the constructor `__new__` for listings, taking a marketplace, a seller and a string UID as inputs.
The responsibility for UID management will lie with the `Marketplace` class: this is an example of the Factory Pattern, where one class is responsible for creating instances of another class by supplying additional information which it manages internally.

Implement an instance method `clone` for listings, returning a draft copy of the current listing with the same listing data but a new seller (and a new UID).
This is an example of the Prototype Pattern, where an existing instance of a class is used as a blueprint to create another instance, instead of invoking the constructor.
Because the `Marketplace` class is responsible for listing creation, your implementation of the `clone` method should rely on the `Marketpalce.draft_listing` method for draft listing creation, followed by setting of the cloned data.
You might want to use the `restore` method from the Memento Pattern below to set properties on the draft listing.

### Listing data

Implement properties exposing the title, price, description and minimum bidding time.
Remember that these might not be set: you might signal this by returning `None`, or by raising an error.

Implement methods which allow each one of the above pieces of data to be set and modified, but only when the listing is in the draft state.
Remember to validate input to these methods when the constraints cannot be captured by the static type hints.

In order to support undo functionality in the editing of draft listings, implement the Memento Pattern:

- a `snapshot` property returns a snapshot of the current listing data (known as a "memento");
- a `restore` method sets listing data to the values stored in the given snapshow.

Depending on how you implement the snapshot data and/or the restore method, you may or may not need to perform validation of the input data.


### Listing states

Implement a property `state` which exposes the listing state, as well as methods `activate`, `cancel` and `sell` which performs legal state transitions.

Implement properties exposing all state dependent data:

- listing time (a [`datetime`](https://docs.python.org/3/library/datetime.html#datetime-objects)), for active and sold listings
- bids (a `BidStack`), for active listings
- selling price (a `Decimal`), selling time (a `datetime`) and buyer (a `Buyer`), for sold listings
- cancelling time (a `datetime`), for cancelled listings

Your properties should raise errors if the listing is not in the relevant state.
Similarly, state transition methods should raise error if their preconditions are not met.
This is an example of the State Pattern, where an object changes its behaviour depending on its internal state.

The listing time and the validation logic for minimum bidding time should be based on the current time as returned by the `TimeServer` (see [Part 6 - Time Server](#part-6---time-server)).


## Part 2 - Bid Management

### Reusable generic data structure

Implement a generic reusable data structure `WithdrawableStack`, supporting the following operations:

- `peek`ing at the top item of the stack
- `push`ing an item on the top of the stack
- `pop`ping an item from the top of the stack
- counting the number of items in the stack (use `__len__`)
- checking if an item is in the stack (use `__contains__`)
- `remove`ing an item from the stack, if it is in the stack

Elements in the stack must be hashable and unique (when compared by equality).
Pushing raises error if the element being pushed on top of the stack is already present in the stack.
The `remove` method takes the item to be removed as its argument, not the item's position (which is not exposed to the outside).

```py
from collections.abc import Hashable
from typing import Generic
ItemT = TypeVar("ItemT", bound=Hashable)

class WithdrawableStack(Generic[ItemT]):
    ...
```

### Bids stack

Define a type alias `Bid` for bid data, as a pair of a buyer and a price.
This is an example of a low-level data container, with no logic associated, so you shouldn't use a class for this.

Implement a `BidStack` class responsible for bid management functionality on an active listing:

- `place`ing a new bid, subject to conditions and invalidating any previous bid by the same buyer
- `withdraw`ing a bid
- accessing the current `top` bid
- checking whether there are bids (use `__bool__` and/or `__len__`)

The `BidStack` class should use a `WithdrawableStack[Bid]` internally, but it should not inherit from it: this is an example of **composition over inheritance**.
A stack of bids is behaviourally different from a withdrawable stack &mdash; the pushing logic for the stack is replaced by the placing logic for a new bid, which behaves differently &mdash; so `BidStack` shouldn't be a subclass of `WithdrawableStack[Bid]`, at least according to a strict interpretation of the **Liskov Substitution Principle**.


## Part 3 - Users

### Buyers

Implement a `Buyer` class responsible for buyer logic, its constructor `__new__` taking the marketplace and a string username.
The responsibility for username management will lie with the `Marketplace` class: this is another example of the Factory Pattern.

Implement properties/methods exposing:

- marketplace
- username
- current bids on active listings
- bought listings
- total amount of money on highest bids for active listings
- total amount of money spent on bought listings

Implement `place_bid` and `withdraw_bid` methods to place or withdraw a bid on a listing, which must be active.

### Sellers

Implement a `Seller` class responsible for seller logic, its constructor  `__new__` taking the marketplace and a string username.
The responsibility for username management will lie with the `Marketplace` class: this is another example of the Factory Pattern.

Implement properties exposing:

- marketplace
- username
- listings, grouped by state
- total amount of money earned from sold listings

Since listings management for a seller is somewhat complex, you might wish to write a custom container class for them.

Implement a `draft_listing` method to create a new draft listing for the seller.
Because `Marketplace` ultimately holds the responsibility of listing creation, as part of the Factory Pattern, the `Seller.draft_listing` method should be implemented as an overlay of the `Marketplace.draft_listing` method.

Implement a `clone_listing` method, as an overlay of the `Listing.clone` method.

## Part 4 - The Marketplace Façade

Implement a `Marketplace` class acting as entry point for all marketplace functionality.
This is an example of the Façade Pattern.
The constructor of `Marketplace` should take a string UID as its argument.

Implement a `buyer` method which, given a username, returns the `Buyer` object responsible for that buyer's data and actions, creating a new object if necessary.
Implement a `seller` method which, given a username, returns the `Seller` object responsible for that user's data and actions, creating a new object if necessary.

Implement a `draft_listing` method which, given a seller, returns a new listing for that seller in draft state.
The method is internally responsible for selecting a fresh Unique ID for the listing (this can be done by keeping and incrementing a private attribute `__next_listing_uid` in the `Marketplace` instance).

Implement a property which exposes a readonly mapping of marketplace listings, indexed by UID.


## Part 5 - Event Management

### Implementing the PubSub Pattern

Implement event management functionality, an instance of the Publish-Subscribe pattern.
Typically, implementation of an event consists of the following three parts:

- A method taking a callback as its argument and adding it to a private collection of callbacks;
- A method taking a callback as its argument and removing it from the private collection of callbacks;
- Whenever the event is triggered as part of some instance method, logic which calls all registered callbacks, passing relevant data to them.

The events of interest to us are as follows:

- transition of a listing from draft to active;
- transition of a listing from draft to cancelled;
- transition of a listing from active to sold;
- transition of a listing from active to cancelled;
- placement of a new bid on an active listing;
- withdrawal of a bid from an active listing.

The 4 state transition events can alternatively be grouped into a single event, with additional parameters specifying the listing states before and after the event.

As an example, the "bid placed" event could be implemented with the following skeleton:

```py
BidPlacedCallback = Callable[[BidStack, Bid], None]

class BidStack:

    _on_bid_placed_callbacks: set[BidPlacedCallback]
    # protected attribute storing registered callbacks

    def on_bid_placed(self, callback: BidPlacedCallback):
        # registers a callback from the event
        ...

    def unregister_on_bid_placed(self, callback: BidPlacedCallback):
        # unregisters a callback from the event
        ...

    def place(self, bid: Bid) -> None:
        ...
        # when new bid has been placed,
        # call all callbacks passing self and bid

```

### Notify other classes of changes

The Publish-Subscribe Pattern provides a mechanism for classes to interact in a loosely coupled way, by registering callbacks which can be used to keep state synchronous without the need to expose their internals, i.e. while respecting Encapsulation and the Single Responsibility Principle.

Use the events on `Listing` and `BidStack` to perform the following updates on the internal state of the `Buyer`, `Seller` and `Marketplace` classes:

- updating highest bids on active listings for a buyer;
- updating bought listings for a buyer;
- updating money spent on bought listings for a buyer;
- updating listing groups for a seller;
- updating money earned by a seller.

The standard way for an object to be notified of an event is to define a protected/private method which is registered as a callback for the event and which handles its consequences for the object.
For example, the following methods could be used to notify `Buyer` objects of changes in bids for listings on which they have an active bid:

```py
class Buyer:

    def _notify_bid_placed(self, bids: BidStack, bid: Bid) -> None:
        ...

    def _notify_bid_withdrawn(self, bids: BidStack, bid: Bid) -> None:
        ...
```

In order for the mechanism to work, these methods must be registered as callbacks for the corresponding events at the time when a buyer places their first bet on an active listing, and they should be unregistered if and when the buyer withdraws their bet from that listing.

## Part 6 - Time Server

Implement a `TimeServer` class, with a `__new__` constructor always returning the same global instance.
This is an example of the Singleton Pattern: in a production implementation, the global instance would manage a program-wide connection to a live time server.

You should implement a public method `now`, returning a `datetime` object for the current date and time.
The listing time value and minimum bidding time logic should use the this method to obtain the current time, instead of using the [`datetime.now` class method](https://docs.python.org/3/library/datetime.html#datetime.datetime.now).

You should implement a protected method in `TimeServer` which allows an arbitrary current time to be set, for testing purposes.
Time can be manually moved forward in a test script, allowing listings with realistic minimum bidding times to be sold.

## Additional goals

If you're up for a challenge, you might wish to implement the following additional mechanics.

- Use a [context manager](https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager) to implement protected locks which prevents users from directly instantiating instances of `Buyer`, `Seller`, `Listing` or `BidStack`. This is an example of the [Resource Acquisition Is Initialisation (RAII) pattern](https://en.wikipedia.org/wiki/Resource_acquisition_is_initialization).
- Use the [`json`](https://docs.python.org/3/library/json.html) library to serialise and deserialise data. You might wish to implement the special `__del__` method: this is a finaliser, called before just before an object is about to be garbage collected, allowing you to serialise any outstanding data before it is cleared form memory.
