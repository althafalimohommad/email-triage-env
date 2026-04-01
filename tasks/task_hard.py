"""
HARD TASK GRADER: Full Triage + Response Drafting

Agent receives 40 emails (some threaded) and must:
1. Classify each into one of 6 categories
2. Assign priority (1-5)
3. Draft replies for urgent/approval emails
4. Archive spam, escalate complex issues

Scoring:
    Final = 0.40 × category_accuracy
          + 0.20 × priority_accuracy
          + 0.30 × response_quality
          + 0.10 × urgency_handling_bonus

    Response quality: keyword matching against expected response elements
    Urgency bonus: 1.0 if ALL urgent emails correctly identified, else proportional

This grader is fully DETERMINISTIC.
"""


def grade(results: list[dict]) -> float:
    """
    Grade the hard task: full triage with response drafting.

    Args:
        results: List of dicts with 'action' and 'truth' keys.

    Returns:
        Score between 0.0 and 1.0
    """
    if not results:
        return 0.0

    n = len(results)
    cat_score = 0.0
    pri_score = 0.0
    response_score = 0.0
    urgent_handled = 0
    urgent_total = 0
    replies_needed = 0

    for r in results:
        truth = r["truth"]
        action = r["action"]

        true_cat = truth.get("category", "")
        pred_cat = action.get("category", "")
        true_pri = truth.get("priority", 3)
        pred_pri = action.get("priority", 3)

        if pred_pri is None:
            pred_pri = 3
        if true_pri is None:
            true_pri = 3

        # ── Category accuracy ──
        if pred_cat == true_cat:
            cat_score += 1.0

        # ── Priority accuracy (partial credit) ──
        pri_diff = abs(int(pred_pri) - int(true_pri))
        if pri_diff == 0:
            pri_score += 1.0
        elif pri_diff == 1:
            pri_score += 0.5
        elif pri_diff == 2:
            pri_score += 0.2

        # ── Response quality (for emails that need replies) ──
        if truth.get("needs_reply", False):
            replies_needed += 1
            reply_content = action.get("reply_content", "") or ""
            expected_keywords = truth.get("response_keywords", [])

            if reply_content and expected_keywords:
                keyword_hits = sum(
                    1 for kw in expected_keywords
                    if kw.lower() in reply_content.lower()
                )
                response_score += min(
                    1.0, keyword_hits / max(len(expected_keywords), 1)
                )
            elif reply_content:
                # Gave a reply but no keywords to check — give partial credit
                response_score += 0.3

        # ── Urgency tracking ──
        if true_cat == "urgent":
            urgent_total += 1
            if pred_cat == "urgent":
                urgent_handled += 1

    # ── Compute final weighted score ──
    cat_accuracy = cat_score / n
    pri_accuracy = pri_score / n
    resp_accuracy = response_score / max(replies_needed, 1)
    urgency_bonus = urgent_handled / max(urgent_total, 1)

    final = (
        0.40 * cat_accuracy
        + 0.20 * pri_accuracy
        + 0.30 * resp_accuracy
        + 0.10 * urgency_bonus
    )

    return round(min(1.0, final), 3)
