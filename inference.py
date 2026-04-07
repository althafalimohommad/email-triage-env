"""
Inference Script — Email Triage Environment
============================================
MANDATORY env variables (injected by the hackathon validator):
    API_BASE_URL    The LiteLLM proxy endpoint (REQUIRED — injected by validator)
    API_KEY         The proxy API key          (REQUIRED — injected by validator)
    MODEL_NAME      The model identifier (default: meta-llama/Llama-3.3-70B-Instruct)
    ENV_URL         Email Triage environment base URL (default: localhost:8000)

STDOUT FORMAT (strictly enforced):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>

NOTE: API_BASE_URL and API_KEY MUST come from environment variables.
      Do NOT hardcode keys or use alternative providers.

Usage:
    # Against local server:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 &
    API_BASE_URL=<proxy_url> API_KEY=<proxy_key> python inference.py

    # Against deployed HF Space (hackathon):
    ENV_URL=https://althafali-email-triage-env.hf.space python inference.py
"""

import json
import os
import re
import sys
import time
from typing import List, Optional

import requests
from openai import OpenAI

# ── Environment variables (evaluator-injected) ─
# Read EXACTLY as evaluator provides them — no fallbacks
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
# LOCAL_IMAGE_NAME: optional — only needed when using from_docker_image()
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
# ENV_URL: the running OpenEnv environment server
ENV_URL          = os.getenv("ENV_URL", "http://localhost:8000").rstrip("/")

BENCHMARK       = "email_triage_env"
TASKS           = ["easy", "medium", "hard"]
MAX_STEPS       = 60          # safety cap per task
SUCCESS_THRESHOLD = 0.5       # score >= 0.5 → success

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert email triage assistant processing a busy professional inbox.

Given an email, respond ONLY with a valid JSON object (no markdown, no extra text):
{
    "action_type": "classify" | "reply" | "archive" | "flag" | "escalate" | "skip",
    "category":    "urgent" | "follow_up" | "fyi" | "spam" | "meeting" | "approval",
    "priority":    <integer 1-5, where 5 is critical>,
    "reply_content": "<draft reply — only when action_type is reply>",
    "reason": "<one-sentence explanation>"
}

Rules:
- Spam → category=spam, priority=1, action_type=archive
- Urgent → category=urgent, priority=5, action_type=reply (draft a reply)
- Approval → category=approval, priority=4, action_type=reply
- Informational → category=fyi, priority=2, action_type=classify
- Meeting → category=meeting, priority=3, action_type=classify
- Follow-up → category=follow_up, priority=3, action_type=flag

IMPORTANT: Respond ONLY with valid JSON. No markdown, no extra text."""


# ── Structured stdout loggers ─────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    # Sanitise action string: single line, no spaces that break parsing
    action_str = action.replace("\n", " ").replace("\r", "")[:120]
    print(
        f"[STEP] step={step} action={action_str!r} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── LLM helper ────────────────────────────────────────────────────────────────

def build_user_prompt(obs: dict) -> str:
    return (
        f"Task instructions: {obs.get('task_description', 'Triage this email.')}\n"
        f"From: {obs.get('sender', '?')} ({obs.get('sender_domain', '?')})\n"
        f"Subject: {obs.get('subject', '(no subject)')}\n"
        f"Body:\n{obs.get('body', '')}\n\n"
        f"Emails remaining: {obs.get('inbox_remaining', 0)}\n"
        "Respond with the JSON action object."
    )


def get_llm_action(client: OpenAI, obs: dict) -> dict:
    """Call LLM, parse JSON action, return dict with required fields."""
    user_msg = build_user_prompt(obs)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=256,
        )
        raw = (completion.choices[0].message.content or "").strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        action = json.loads(raw)
    except Exception as exc:
        print(f"[DEBUG] LLM/parse error: {exc}", flush=True)
        action = {}

    # Ensure required fields with safe defaults
    action.setdefault("action_type", "classify")
    action.setdefault("category",    "fyi")
    action.setdefault("priority",    3)
    if "priority" in action:
        action["priority"] = int(action["priority"])
    return action


# ── Task runner ───────────────────────────────────────────────────────────────

def run_task(client: OpenAI, task_id: str) -> None:
    """Run one full episode for task_id, emitting START/STEP/END lines."""
    rewards: List[float] = []
    steps_taken = 0
    score  = 0.0
    success = False
    last_error: Optional[str] = None

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset environment
        r = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id}, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"reset() failed: {r.status_code} {r.text[:200]}")
        obs = r.json()

        for step in range(1, MAX_STEPS + 1):
            # Get action from LLM
            action = get_llm_action(client, obs)
            action_str = f"{action.get('action_type','?')}:{action.get('category','?')}:p{action.get('priority','?')}"

            # Send to environment
            step_r = requests.post(f"{ENV_URL}/step", json={"action": action}, timeout=30)
            if step_r.status_code == 422:
                # Fallback: send action directly (not wrapped)
                step_r = requests.post(f"{ENV_URL}/step", json=action, timeout=30)

            if step_r.status_code != 200:
                last_error = f"step_failed_{step_r.status_code}"
                log_step(step=step, action=action_str, reward=0.0, done=True, error=last_error)
                break

            result  = step_r.json()
            reward  = float(result.get("reward", 0.0))
            done    = bool(result.get("done", False))
            err_msg = result.get("error") or None

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=err_msg)

            if done:
                break

            # Next observation
            obs = result.get("observation", result)
            if not isinstance(obs, dict):
                obs = result

        # Compute final score from /state
        try:
            state_r = requests.get(f"{ENV_URL}/state", timeout=10)
            if state_r.status_code == 200:
                st = state_r.json()
                base_score = float(
                    st.get("current_score")
                    or st.get("score")
                    or (sum(rewards) / len(rewards) if rewards else 0.0)
                )
            else:
                base_score = sum(rewards) / len(rewards) if rewards else 0.0
        except Exception:
            base_score = sum(rewards) / len(rewards) if rewards else 0.0

        # Binary scoring: 0.9 for success, 0.1 for failure
        # (Strictly between 0 and 1, not 0.0 or 1.0)
        success = base_score >= SUCCESS_THRESHOLD
        score = 0.9 if success else 0.1

    except Exception as exc:
        last_error = str(exc)
        print(f"[DEBUG] Task {task_id} error: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    # Initialize OpenAI client with evaluator-injected credentials
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )

    print(f"[INFO] MODEL_NAME={MODEL_NAME}", flush=True)
    print(f"[INFO] Running tasks: {TASKS}", flush=True)
    print("", flush=True)

    start_time = time.time()
    for task_id in TASKS:
        run_task(client, task_id)
        print("", flush=True)

    elapsed = time.time() - start_time
    print(f"[INFO] Total runtime: {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
