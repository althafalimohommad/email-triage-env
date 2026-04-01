"""
Quick smoke test — runs the environment through a complete easy episode
with a simple rule-based agent (no LLM needed).
"""

import sys
sys.path.insert(0, ".")

from server.email_triage_env_environment import EmailTriageEnvironment
from models import EmailTriageAction, ActionType, EmailCategory, Priority
from tasks.task_easy import grade as grade_easy
from tasks.task_medium import grade as grade_medium
from tasks.task_hard import grade as grade_hard


def simple_agent(obs) -> EmailTriageAction:
    """A rule-based agent for testing — no LLM needed."""
    subject = (obs.subject or "").lower()
    body = (obs.body or "").lower()
    sender = (obs.sender_domain or "").lower()

    # Simple heuristics
    spam_signals = ["won", "prize", "click", "verify", "free", "deal", "offer",
                    "congratulations", "selected", "million", "prince"]
    urgent_signals = ["urgent", "critical", "emergency", "p0", "breach",
                      "down", "failing", "asap", "immediately"]
    meeting_signals = ["meeting", "sync", "1:1", "standup", "retrospective",
                       "calendar", "invite", "schedule"]
    approval_signals = ["approval", "approve", "expense", "pto", "purchase",
                        "request", "authorization", "sign-off"]
    fyi_signals = ["fyi", "newsletter", "update", "recording", "photos",
                   "new blog", "schedule", "policy"]

    text = f"{subject} {body}"

    if any(s in text for s in spam_signals) and sender not in ("acmecorp.com",):
        return EmailTriageAction(
            action_type=ActionType.CLASSIFY,
            category=EmailCategory.SPAM,
            priority=Priority.NONE,
            reason="Spam indicators detected"
        )
    elif any(s in text for s in urgent_signals):
        return EmailTriageAction(
            action_type=ActionType.CLASSIFY,
            category=EmailCategory.URGENT,
            priority=Priority.CRITICAL,
            reply_content="Acknowledged. I'm investigating this immediately and will update the team shortly.",
            reason="Urgent signals detected"
        )
    elif any(s in text for s in approval_signals):
        return EmailTriageAction(
            action_type=ActionType.CLASSIFY,
            category=EmailCategory.APPROVAL,
            priority=Priority.HIGH,
            reply_content="I've reviewed this request and approved it. Please proceed.",
            reason="Approval request detected"
        )
    elif any(s in text for s in meeting_signals):
        return EmailTriageAction(
            action_type=ActionType.CLASSIFY,
            category=EmailCategory.MEETING,
            priority=Priority.MEDIUM,
            reason="Meeting related"
        )
    elif any(s in text for s in fyi_signals):
        return EmailTriageAction(
            action_type=ActionType.CLASSIFY,
            category=EmailCategory.FYI,
            priority=Priority.LOW,
            reason="Informational email"
        )
    else:
        return EmailTriageAction(
            action_type=ActionType.CLASSIFY,
            category=EmailCategory.FOLLOW_UP,
            priority=Priority.MEDIUM,
            reason="Needs follow-up"
        )


def run_episode(task_id: str):
    """Run a complete episode and grade it."""
    env = EmailTriageEnvironment()
    obs = env.reset_task(task_id)

    results = []
    step = 0

    while not obs.done:
        action = simple_agent(obs)
        obs = env.step(action)
        step += 1

        # Collect results for grading
        if env._results:
            results = env._results

    state = env.state
    print(f"\n{'='*50}")
    print(f"Task: {task_id.upper()}")
    print(f"{'='*50}")
    print(f"  Emails processed:    {state.processed_emails}/{state.total_emails}")
    print(f"  Correct:             {state.correct_classifications}")
    print(f"  Incorrect:           {state.incorrect_classifications}")
    print(f"  Missed urgent:       {state.missed_urgent}")
    print(f"  Cumulative score:    {state.current_score:.3f}")

    # Run the official grader
    graders = {"easy": grade_easy, "medium": grade_medium, "hard": grade_hard}
    grade = graders[task_id](results)
    print(f"  Official grade:      {grade:.3f}")
    return grade


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║   Email Triage Environment — Smoke Test         ║")
    print("║   (Rule-based agent, no LLM needed)             ║")
    print("╚══════════════════════════════════════════════════╝")

    scores = {}
    for task in ["easy", "medium", "hard"]:
        scores[task] = run_episode(task)

    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for task, score in scores.items():
        bar = "█" * int(score * 30) + "░" * (30 - int(score * 30))
        print(f"  {task:8s}: {score:.3f}  [{bar}]")
    print(f"  Overall:  {sum(scores.values()) / len(scores):.3f}")
    print(f"{'='*50}")
