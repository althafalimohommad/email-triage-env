# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from typing import Optional

"""
FastAPI application for the Email Triage Environment.

Provides both the standard OpenEnv HTTP/WebSocket interface and custom
endpoints for task selection and grading.

Endpoints:
    Standard OpenEnv:
        - POST /reset: Reset the environment
        - POST /step: Execute an action
        - GET /state: Get current environment state
        - GET /schema: Get action/observation schemas
        - WS /ws: WebSocket endpoint for persistent sessions

    Custom:
        - POST /reset_task: Reset with a specific task_id
        - GET /tasks: List available tasks
        - POST /grade: Get final grade for completed episode

Usage:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

try:
    from ..models import EmailTriageAction, EmailTriageObservation
    from .email_triage_env_environment import EmailTriageEnvironment
except (ImportError, ModuleNotFoundError):
    from models import EmailTriageAction, EmailTriageObservation
    from server.email_triage_env_environment import EmailTriageEnvironment


# Create the standard OpenEnv app
app = create_app(
    EmailTriageEnvironment,
    EmailTriageAction,
    EmailTriageObservation,
    env_name="email_triage_env",
    max_concurrent_envs=5,
)


# ── Custom endpoints ─────────────────────────────────────────────────────────

@app.post("/reset")
async def reset_env(task_id: Optional[str] = "easy"):
    """
    Reset the environment with a specific task.

    Query params:
        task_id: One of 'easy', 'medium', 'hard' (default: 'easy')

    This overrides the default /reset to allow per-task selection.
    """
    valid_tasks = {"easy", "medium", "hard"}
    if task_id not in valid_tasks:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id '{task_id}'. Must be one of: {sorted(valid_tasks)}",
        )
    env = EmailTriageEnvironment()
    obs = env.reset_task(task_id)
    # Store env reference for subsequent /step calls is handled by the framework.
    # This endpoint is mainly for clients that bypass the standard session model.
    return obs.model_dump()


@app.post("/reset_task")
async def reset_task(task_id: str = "easy"):
    """Alias for /reset with task_id body parameter."""
    valid_tasks = {"easy", "medium", "hard"}
    if task_id not in valid_tasks:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id '{task_id}'. Must be one of: {sorted(valid_tasks)}",
        )
    env = EmailTriageEnvironment()
    obs = env.reset_task(task_id)
    return obs.model_dump()


@app.get("/health")
async def health():
    """Health check endpoint used by Docker HEALTHCHECK."""
    return {"status": "ok", "service": "email_triage_env"}

@app.get("/")
async def root():
    """Welcome page with API overview."""
    return {
        "name": "Email Triage Environment",
        "version": "1.0.0",
        "status": "running ✅",
        "description": (
            "A real-world OpenEnv environment where an AI agent processes "
            "an inbox of emails — classifying, prioritizing, flagging, "
            "archiving, and drafting replies."
        ),
        "endpoints": {
            "OpenEnv Standard": {
                "POST /reset": "Reset the environment (start a new episode)",
                "POST /step": "Execute an action on the current email",
                "GET /state": "Get current environment state",
                "GET /schema": "Get action/observation JSON schemas",
                "WS /ws": "WebSocket endpoint for persistent sessions",
            },
            "Custom": {
                "GET /tasks": "List all available tasks (easy/medium/hard)",
                "GET /health": "Health check",
                "GET /docs": "Interactive Swagger API documentation",
            },
        },
        "tasks": ["easy (Spam Detection)", "medium (Multi-Label)", "hard (Full Triage + Reply)"],
        "quick_start": (
            "1. POST /reset to start → 2. Read the email in the observation → "
            "3. POST /step with your action → 4. Repeat until done=true"
        ),
    }


@app.get("/tasks")
async def list_tasks():
    """List available tasks with descriptions."""
    return {
        "tasks": [
            {
                "id": "easy",
                "name": "Spam Detection",
                "difficulty": "easy",
                "num_emails": 20,
                "time_limit": 120,
                "description": "Classify 20 emails as spam or not-spam",
                "available_actions": ["classify"],
            },
            {
                "id": "medium",
                "name": "Multi-Label Categorization",
                "difficulty": "medium",
                "num_emails": 30,
                "time_limit": 180,
                "description": "Categorize 30 emails by type and priority",
                "available_actions": ["classify", "flag", "archive"],
            },
            {
                "id": "hard",
                "name": "Full Triage + Response Drafting",
                "difficulty": "hard",
                "num_emails": 40,
                "time_limit": 300,
                "description": "Classify, prioritize, and draft replies for 40 emails",
                "available_actions": [
                    "classify", "reply", "flag", "archive", "escalate"
                ],
            },
        ]
    }


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution.

    Usage:
        python -m email_triage_env.server.app
        uv run --project . server
    """
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Email Triage Environment Server")
    parser.add_argument("--host", type=str, default=host)
    parser.add_argument("--port", type=int, default=port)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
