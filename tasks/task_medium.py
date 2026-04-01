"""
MEDIUM TASK GRADER: Multi-Label Categorization + Priority Assignment

Agent receives 30 emails and must:
1. Classify each into one of 6 categories
2. Assign a priority level (1-5)
3. Optionally FLAG or ARCHIVE emails

Scoring:
    Final = 0.6 × category_accuracy + 0.4 × priority_accuracy

    Category accuracy: exact match = 1.0, else 0.0
    Priority accuracy:
        - Exact match: 1.0
        - Off by 1: 0.5
        - Off by 2: 0.2
        - Off by 3+: 0.0

This grader is fully DETERMINISTIC.
"""


def grade(results: list[dict]) -> float:
    """
    Grade the medium task: multi-label categorization + priority.

    Args:
        results: List of dicts with 'action' and 'truth' keys.

    Returns:
        Score between 0.0 and 1.0
    """
    if not results:
        return 0.0

    cat_score = 0.0
    pri_score = 0.0
    n = len(results)

    for r in results:
        pred_cat = r["action"].get("category", "")
        true_cat = r["truth"].get("category", "")
        pred_pri = r["action"].get("priority", 3)
        true_pri = r["truth"].get("priority", 3)

        # Ensure priority values are ints
        if pred_pri is None:
            pred_pri = 3
        if true_pri is None:
            true_pri = 3

        # Category scoring: exact match only
        if pred_cat == true_cat:
            cat_score += 1.0

        # Priority scoring: partial credit for close guesses
        pri_diff = abs(int(pred_pri) - int(true_pri))
        if pri_diff == 0:
            pri_score += 1.0
        elif pri_diff == 1:
            pri_score += 0.5
        elif pri_diff == 2:
            pri_score += 0.2
        # Off by 3+ = 0.0

    cat_accuracy = cat_score / n
    pri_accuracy = pri_score / n

    # Weighted final score
    final = 0.6 * cat_accuracy + 0.4 * pri_accuracy
    return round(final, 3)
