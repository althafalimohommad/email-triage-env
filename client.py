# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Email Triage Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import (
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
)


class EmailTriageEnv(
    EnvClient[EmailTriageAction, EmailTriageObservation, EmailTriageState]
):
    """
    Client for the Email Triage Environment.

    Maintains a persistent WebSocket connection to the environment server
    for efficient multi-step interactions.

    Example:
        >>> with EmailTriageEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.subject)
        ...
        ...     action = EmailTriageAction(
        ...         action_type="classify",
        ...         category="spam",
        ...         priority=1,
        ...         reason="Looks like a phishing email"
        ...     )
        ...     result = client.step(action)
        ...     print(f"Reward: {result.reward}")
    """

    def _step_payload(self, action: EmailTriageAction) -> Dict:
        """Convert EmailTriageAction to JSON payload for step message."""
        payload = {
            "action_type": action.action_type.value,
        }
        if action.category is not None:
            payload["category"] = action.category.value
        if action.priority is not None:
            payload["priority"] = action.priority.value
        if action.reply_content is not None:
            payload["reply_content"] = action.reply_content
        if action.reason is not None:
            payload["reason"] = action.reason
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[EmailTriageObservation]:
        """Parse server response into StepResult."""
        obs_data = payload.get("observation", {})

        observation = EmailTriageObservation(
            # Email fields
            email_id=obs_data.get("email_id", ""),
            sender=obs_data.get("sender", ""),
            sender_domain=obs_data.get("sender_domain", ""),
            subject=obs_data.get("subject", ""),
            body=obs_data.get("body", ""),
            timestamp=obs_data.get("timestamp", ""),
            has_attachments=obs_data.get("has_attachments", False),
            reply_to=obs_data.get("reply_to"),
            # Inbox status
            inbox_remaining=obs_data.get("inbox_remaining", 0),
            emails_processed=obs_data.get("emails_processed", 0),
            time_remaining=obs_data.get("time_remaining", 0.0),
            # Task info
            task_description=obs_data.get("task_description", ""),
            available_actions=obs_data.get("available_actions", []),
            # Base fields
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> EmailTriageState:
        """Parse server response into EmailTriageState."""
        return EmailTriageState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", "easy"),
            total_emails=payload.get("total_emails", 0),
            processed_emails=payload.get("processed_emails", 0),
            correct_classifications=payload.get("correct_classifications", 0),
            incorrect_classifications=payload.get("incorrect_classifications", 0),
            missed_urgent=payload.get("missed_urgent", 0),
            current_score=payload.get("current_score", 0.0),
        )
