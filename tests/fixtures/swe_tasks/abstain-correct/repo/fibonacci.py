"""Fibonacci sequence computation."""


def fib(n):
    """Return the nth Fibonacci number (0-indexed).

    fib(0) = 0, fib(1) = 1, fib(2) = 1, fib(3) = 2, ...

    Args:
        n: Non-negative integer.

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fib_sequence(n):
    """Return the first n Fibonacci numbers as a list.

    Args:
        n: How many numbers to generate.

    Returns:
        A list of the first n Fibonacci numbers.
    """
    if n <= 0:
        return []
    return [fib(i) for i in range(n)]
