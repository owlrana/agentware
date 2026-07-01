"""Top-K scores — returns the k highest values from a list."""


def top_k_scores(scores, k):
    """Return the k highest scores in descending order.

    Args:
        scores: A list of numeric scores.
        k: How many top scores to return.

    Returns:
        A list of the top k scores, sorted descending.
        If k >= len(scores), return all scores sorted descending.
    """
    if k <= 0:
        return []
    if k >= len(scores):
        return sorted(scores, reverse=True)

    # BUG: O(n*k) quadratic approach — too slow for large inputs
    result = []
    remaining = list(scores)
    for _ in range(k):
        max_val = remaining[0]
        max_idx = 0
        for i in range(1, len(remaining)):
            if remaining[i] > max_val:
                max_val = remaining[i]
                max_idx = i
        result.append(max_val)
        remaining.pop(max_idx)
    return result
