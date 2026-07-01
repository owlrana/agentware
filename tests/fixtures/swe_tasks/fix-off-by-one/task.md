# Task: Fix Off-By-One in Pagination Helper

The file `paginate.py` contains a `get_page` function that returns a slice of
items for a given page number (1-indexed) and page size. There is an off-by-one
bug: the last page is missing its final item when the total item count is an
exact multiple of the page size.

Fix the bug so that `get_page` returns the correct items for all valid pages,
including the last page.
