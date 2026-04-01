"""
EASY TASK GRADER: Binary Spam Classification

Agent receives 20 emails and must classify each as 'spam' or NOT 'spam'.
Only the CLASSIFY action is available.

Scoring:
    - Correct spam/not-spam detection: +1.0 per email
    - Incorrect: +0.0 per email
    - Final score = correct / total (0.0 to 1.0)

This grader is fully DETERMINISTIC — same inputs always produce same score.
"""


def grade(results: list[dict]) -> float:
    """
    Grade the easy task: binary spam detection.

    Args:
        results: List of dicts with 'action' and 'truth' keys.
                 action = {"category": str, "priority": int, ...}
                 truth  = {"category": str, "priority": int, ...}

    Returns:
        Score between 0.0 and 1.0
    """
    if not results:
        return 0.0

    correct = 0
    total = len(results)

    for r in results:
        predicted = r["action"].get("category", "")
        actual = r["truth"].get("category", "")

        # Binary classification: is it spam or not?
        predicted_is_spam = (predicted == "spam")
        actual_is_spam = (actual == "spam")

        if predicted_is_spam == actual_is_spam:
            correct += 1

    return round(correct / total, 3)
