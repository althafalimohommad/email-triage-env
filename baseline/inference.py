"""
Baseline Inference Script for Email Triage Environment.

Uses the OpenAI API client to run an LLM agent against all 3 tasks
and reports reproducible baseline scores.

Requirements:
    - OPENAI_API_KEY environment variable set
    - Email Triage Environment server running on localhost:8000

Usage:
    # Start the server first:
    uvicorn server.app:app --host 0.0.0.0 --port 8000

    # Then run baseline:
    python baseline/inference.py

    # Or specify a different API/model:
    OPENAI_API_KEY=your-key python baseline/inference.py --model gpt-4
"""

import json
import os
import sys
import argparse
import time

import requests
from openai import OpenAI


# ── Configuration ────────────────────────────────────────────────────────────

DEFAULT_ENV_URL = "http://localhost:8000"
DEFAULT_MODEL = "gpt-4"

SYSTEM_PROMPT = """You are an expert email triage assistant. You process emails from a busy professional inbox.

Given an email, you MUST respond with a valid JSON object (no markdown, no extra text) containing:
{
    "action_type": "classify" | "reply" | "archive" | "flag" | "escalate" | "skip",
    "category": "urgent" | "follow_up" | "fyi" | "spam" | "meeting" | "approval",
    "priority": <integer 1 to 5, where 5 is critical>,
    "reply_content": "<only if action_type is reply — write a professional response>",
    "reason": "<brief 1-sentence explanation of your decision>"
}

Rules:
- For spam emails: set category="spam", priority=1, action_type="archive"
- For urgent emails: set category="urgent", priority=5, action_type="reply" and draft a response
- For approval requests: set category="approval", priority=4, action_type="reply" and acknowledge
- For informational emails: set category="fyi", priority=2, action_type="classify"
- For meeting-related: set category="meeting", priority=3, action_type="classify"
- For follow-up needed: set category="follow_up", priority=3, action_type="flag"

IMPORTANT: Respond ONLY with valid JSON. No markdown code blocks, no explanations outside the JSON."""


# ── Agent Logic ──────────────────────────────────────────────────────────────


def create_agent_prompt(observation: dict) -> str:
    """Build the user prompt from the observation."""
    return f"""Process this email and decide what action to take.

**Task Instructions**: {observation.get('task_description', 'Classify the email.')}
**Available Actions**: {observation.get('available_actions', ['classify'])}

---

**Email Details:**
- **From**: {observation.get('sender', 'unknown')}
- **Domain**: {observation.get('sender_domain', 'unknown')}
- **Subject**: {observation.get('subject', 'No subject')}
- **Has Attachments**: {observation.get('has_attachments', False)}

**Body**:
{observation.get('body', 'No body')}

---

Emails remaining in inbox: {observation.get('inbox_remaining', 0)}
Time remaining: {observation.get('time_remaining', 0):.0f}s

Respond with a JSON object specifying your action."""


def run_agent_step(client: OpenAI, model: str, observation: dict) -> dict:
    """Ask the LLM to process one email and return an action."""
    user_msg = create_agent_prompt(observation)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,  # Deterministic for reproducibility
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        action = json.loads(content)

        # Ensure required fields
        if "action_type" not in action:
            action["action_type"] = "classify"
        if "category" not in action:
            action["category"] = "fyi"
        if "priority" not in action:
            action["priority"] = 3

        return action

    except Exception as e:
        print(f"  ⚠ LLM error: {e} — using default action")
        return {
            "action_type": "classify",
            "category": "fyi",
            "priority": 3,
            "reason": f"Fallback due to error: {e}",
        }


# ── Task Runner ──────────────────────────────────────────────────────────────


def run_task(
    env_url: str, client: OpenAI, model: str, task_id: str
) -> tuple[float, list[dict]]:
    """
    Run the agent through a complete task episode.

    Returns:
        Tuple of (average_reward, list_of_step_results)
    """
    print(f"\n{'='*60}")
    print(f"  TASK: {task_id.upper()}")
    print(f"{'='*60}")

    # Reset environment
    resp = requests.post(f"{env_url}/reset", timeout=30)
    if resp.status_code != 200:
        print(f"  ❌ Reset failed: {resp.status_code} — {resp.text}")
        return 0.0, []

    obs = resp.json()
    total_reward = 0.0
    steps = 0
    results = []

    while True:
        # Get agent action from LLM
        action = run_agent_step(client, model, obs)

        print(
            f"  Step {steps + 1:2d} | "
            f"Subject: {obs.get('subject', '?')[:40]:40s} | "
            f"Action: {action.get('action_type', '?'):10s} | "
            f"Category: {action.get('category', '?'):10s} | "
            f"Priority: {action.get('priority', '?')}"
        )

        # Send action to environment
        step_resp = requests.post(
            f"{env_url}/step",
            json=action,
            timeout=30,
        )

        if step_resp.status_code != 200:
            print(f"  ❌ Step failed: {step_resp.status_code} — {step_resp.text}")
            break

        result = step_resp.json()
        reward = result.get("reward", 0.0)
        total_reward += reward
        steps += 1

        results.append({
            "step": steps,
            "action": action,
            "reward": reward,
            "done": result.get("done", False),
        })

        obs_data = result.get("observation", result)
        if result.get("done", False) or obs_data.get("done", False):
            print(f"\n  ✅ Episode complete after {steps} steps")
            break

        obs = obs_data

        # Safety: prevent infinite loops
        if steps > 100:
            print("  ⚠ Safety limit reached (100 steps)")
            break

    avg_score = total_reward / steps if steps > 0 else 0.0
    print(f"  📊 Average reward: {avg_score:.3f}")
    print(f"  📊 Total reward:   {total_reward:.3f}")

    return round(avg_score, 3), results


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Baseline inference for Email Triage Environment"
    )
    parser.add_argument(
        "--env-url",
        default=os.environ.get("ENV_URL", DEFAULT_ENV_URL),
        help="URL of the environment server",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        help="OpenAI model to use",
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=["easy", "medium", "hard"],
        help="Tasks to run (default: all three)",
    )
    args = parser.parse_args()

    # Validate API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("   Set it with: $env:OPENAI_API_KEY = 'your-key-here'")
        sys.exit(1)

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Email Triage Environment — Baseline Inference         ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║  Model:    {args.model:47s}║")
    print(f"║  Env URL:  {args.env_url:47s}║")
    print(f"║  Tasks:    {', '.join(args.tasks):47s}║")
    print("╚════════════════════════════════════════════════════════════╝")

    all_scores = {}
    start_time = time.time()

    for task_id in args.tasks:
        score, results = run_task(args.env_url, client, args.model, task_id)
        all_scores[task_id] = score

    elapsed = time.time() - start_time

    # ── Final Report ──
    print("\n" + "=" * 60)
    print("  BASELINE SCORES — Email Triage Environment")
    print("=" * 60)
    for task_id, score in all_scores.items():
        bar = "█" * int(score * 30) + "░" * (30 - int(score * 30))
        print(f"  {task_id:8s}: {score:.3f}  [{bar}]")
    print(f"\n  Overall:  {sum(all_scores.values()) / len(all_scores):.3f}")
    print(f"  Time:     {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
