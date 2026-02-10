from bag import Bag
import collections_abc

# Make a bag of fruit:
bag = Bag(["mango", "apple", "orange", "apple", "orange", "apple"])

# Iterate over the bag:
print("Items in the bag:")
for item in bag:
    print(f"  {item}")

# Show the size of the bag:
print(f"The bag has {len(bag)} items in it.")

print(f"Is an apple in the bag? {'apple' in bag}")

# You typically don't manually extract iterators,
# the runtime does it under the hood for you.

# Same as above, but done explicitly with the iterator:
it = iter(bag)  # infers that it: Iterator[str]
print("Items in the bag:")
while True:
    try:
        # Iterator[str] defines __next__(self) -> str
        # which returns the next item if available:
        item = it.__next__()
        print(f"  {item}")
    except StopIteration:
        # __next__ raises StopIteration if no more items are available
        break

# Make comprehensions using the bag:
item_strs = [item.upper() for item in bag]

# Checking that Bag structurally typechecks the various containers it should:
my_iterable: collections_abc.Iterable[str] = bag  # OK
my_iterator: collections_abc.Iterator[str] = iter(bag)  # OK
my_sized: collections_abc.Sized = bag  # OK
my_container: collections_abc.Container[str] = bag  # OK
my_mutable_container: collections_abc.MutableContainer[str] = bag
# Note: the above works without every having mentioned collections_abc in bag.py.

for item_upper in collections_abc.iter_map(bag, lambda item: item.upper()):
    #    anonymous function (lambda) definition ^^^^^^^^^^^^^^^^^^^^^^^^^
    # Lambdas are functions defined by a single return expression.
    print(item_upper)

# Effect of Mixin implementation:
print(f"Index of 'orange': {bag.index('orange')}")  # Index of 'orange': 2
