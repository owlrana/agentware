"""Hidden grader for fix-off-by-one task. Agent NEVER sees this file."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo.paginate import get_page, total_pages


def test_basic_pagination():
    items = [1, 2, 3, 4, 5, 6]
    assert get_page(items, 1, 3) == [1, 2, 3]
    assert get_page(items, 2, 3) == [4, 5, 6]


def test_last_page_exact_multiple():
    """The bug: last page missing when len(items) % page_size == 0."""
    items = list(range(1, 11))  # 10 items
    # page_size=5 -> 2 pages exactly
    assert get_page(items, 2, 5) == [6, 7, 8, 9, 10]


def test_last_page_partial():
    items = list(range(1, 8))  # 7 items
    # page_size=3 -> 3 pages (last has 1 item)
    assert get_page(items, 3, 3) == [7]


def test_total_pages_exact():
    items = list(range(10))
    assert total_pages(items, 5) == 2


def test_total_pages_remainder():
    items = list(range(7))
    assert total_pages(items, 3) == 3


def test_out_of_range():
    items = [1, 2, 3]
    assert get_page(items, 0, 2) == []
    assert get_page(items, 5, 2) == []


def test_invalid_page_size():
    assert get_page([1, 2], 1, 0) == []
    assert total_pages([1, 2], 0) == 0
