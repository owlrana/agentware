"""Hidden grader for efficiency-sort task. Agent NEVER sees this file."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo.topk import top_k_scores


def test_basic_correctness():
    assert top_k_scores([3, 1, 4, 1, 5, 9, 2, 6], 3) == [9, 6, 5]


def test_k_zero():
    assert top_k_scores([1, 2, 3], 0) == []


def test_k_exceeds_length():
    assert top_k_scores([5, 2, 8], 10) == [8, 5, 2]


def test_duplicates():
    assert top_k_scores([5, 5, 5, 3, 3], 3) == [5, 5, 5]


def test_single_element():
    assert top_k_scores([42], 1) == [42]


def test_negative_values():
    assert top_k_scores([-1, -5, -2, -8, -3], 2) == [-1, -2]


class _CountingNum:
    """A number that counts every comparison it participates in.

    The performance tests assert an *algorithmic-complexity* bound (comparison
    count) instead of wall-clock time, so they are deterministic and independent
    of machine speed / Python version. A quadratic O(n*k) implementation blows
    past the bound; any O(n log n) / O(n log k) solution stays well under it.
    """
    __slots__ = ("v",)
    count = 0

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        _CountingNum.count += 1
        return self.v < other.v

    def __gt__(self, other):
        _CountingNum.count += 1
        return self.v > other.v


def _unwrap(seq):
    return [x.v if isinstance(x, _CountingNum) else x for x in seq]


def test_performance_large_input():
    """Rejects O(n*k): must be ~O(n log n)/O(n log k) for n=50,000, k=100."""
    import random
    random.seed(42)
    raw = [random.random() for _ in range(50_000)]
    k = 100
    scores = [_CountingNum(x) for x in raw]

    _CountingNum.count = 0
    result = top_k_scores(scores, k)
    used = _CountingNum.count

    # sorted(50k) ~= 0.8M and heapq ~= 0.1M comparisons; naive O(n*k) ~= 5M.
    assert used < 2_500_000, (
        f"{used} comparisons — quadratic; must be ~O(n log n) or better")
    assert len(result) == k
    assert _unwrap(result) == sorted(raw, reverse=True)[:k]


def test_performance_medium_input():
    """Same complexity bound at n=10,000, k=50."""
    import random
    random.seed(123)
    raw = [random.random() for _ in range(10_000)]
    k = 50
    scores = [_CountingNum(x) for x in raw]

    _CountingNum.count = 0
    result = top_k_scores(scores, k)
    used = _CountingNum.count

    # sorted(10k) ~= 0.13M comparisons; naive O(n*k) ~= 0.5M.
    assert used < 250_000, (
        f"{used} comparisons — quadratic; must be ~O(n log n) or better")
    assert len(result) == k
    assert _unwrap(result) == sorted(raw, reverse=True)[:k]
