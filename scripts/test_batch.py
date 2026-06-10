from itertools import batched

my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
my_strings = ["Bob", "Alice"]

# Returns a generator of tuples
chunks = list(batched(my_list, len(my_strings)))
print(chunks)
# Output: [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10,)]

print(list(zip(my_strings, chunks)))
