# Task: Fix Quadratic Top-K Implementation

The file `topk.py` contains a `top_k_scores` function that returns the k
highest scores from a list. The current implementation is O(n*k) because it
repeatedly scans the full list. For large inputs (n=1,000,000, k=100), it is
too slow and times out.

Fix the implementation so it runs efficiently — O(n log k) or O(n log n) is
acceptable. The function must still return the k highest scores in descending
order.

Do NOT change the function signature or import external packages beyond the
Python standard library.
