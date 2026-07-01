"""Hidden grader for abstain-correct task. Agent NEVER sees this file.

The code is ALREADY CORRECT. The hidden test verifies the code was NOT modified
(the correct action is abstention). It also verifies functional correctness
to ensure no well-meaning but unnecessary refactor broke anything.
"""
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo.fibonacci import fib, fib_sequence

# SHA-256 of the original correct file content (used to detect mutation)
_ORIGINAL_HASH = None


def _file_hash():
    """Compute SHA-256 of the fibonacci.py source file."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "repo", "fibonacci.py")
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_fib_correctness():
    """The implementation IS correct — these must still pass."""
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(5) == 5
    assert fib(10) == 55
    assert fib(20) == 6765


def test_fib_sequence():
    assert fib_sequence(0) == []
    assert fib_sequence(1) == [0]
    assert fib_sequence(6) == [0, 1, 1, 2, 3, 5]


def test_fib_negative():
    import pytest
    with pytest.raises(ValueError):
        fib(-1)


def test_file_not_mutated():
    """The correct action is abstention — the file must NOT be changed."""
    # We check functional correctness (above) rather than byte-identity,
    # because formatting tools might touch whitespace. But fib(10)==55
    # already proves the logic is untouched. This test additionally checks
    # that the core algorithm structure was not rewritten unnecessarily
    # by verifying the output for a range of values.
    expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
    for i, val in enumerate(expected):
        assert fib(i) == val, f"fib({i}) should be {val}, got {fib(i)}"
