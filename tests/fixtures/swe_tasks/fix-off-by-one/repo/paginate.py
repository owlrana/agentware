"""Pagination helper — returns a page of items from a list."""


def get_page(items, page, page_size):
    """Return items for the given 1-indexed page.

    Args:
        items: The full list of items.
        page: 1-indexed page number.
        page_size: Number of items per page.

    Returns:
        A list of items for the requested page, or [] if page is out of range.
    """
    if page < 1 or page_size < 1:
        return []
    total_pages = len(items) // page_size  # BUG: should use ceil division
    if page > total_pages:
        return []
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def total_pages(items, page_size):
    """Return the total number of pages."""
    if page_size < 1:
        return 0
    count = len(items) // page_size  # BUG: same off-by-one
    return count
