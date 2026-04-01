# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Email Triage Environment Implementation.

A real-world task simulation where an AI agent processes an inbox of emails,
classifying them by category and priority, flagging important ones,
archiving spam, and drafting replies for urgent/approval emails.
"""

import json
import time
from pathlib import Path
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

try:
    from ..models import (
        EmailCategory,
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        ActionType,
    )
except ImportError:
    from models import (
        EmailCategory,
        EmailTriageAction,
        EmailTriageObservation,
        EmailTriageState,
        ActionType,
    )


class EmailTriageEnvironment(Environment):
    """
    OpenEnv-compliant environment for email triage.

    The agent processes a queue of emails one by one, choosing actions like
    classify, reply, archive, flag, or escalate. The environment scores
    each action against ground-truth labels and provides partial-credit
    rewards throughout the episode.

    Tasks:
        - easy:   20 emails, spam detection (classify only)
        - medium: 30 emails, multi-label categorization + priority
        - hard:   40 emails, full triage with response drafting
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the Email Triage environment."""
        self._state = EmailTriageState(episode_id=str(uuid4()), step_count=0)
        self._emails: list[dict] = []
        self._ground_truth: dict[str, dict] = {}
        self._current_index: int = 0
        self._results: list[dict] = []
        self._task_config: dict = {}
        self._start_time: float = 0.0
        self._time_limit: float = 300.0
        self._data_dir = Path(__file__).parent.parent / "data"

    def reset(self) -> EmailTriageObservation:
        """
        Reset the environment for a new episode.

        Loads the task data and returns the first email observation.
        The task_id is read from metadata if provided, defaults to 'easy'.
        """
        # Default to easy task — the client can pass task_id via metadata
        task_id = "easy"

        self._state = EmailTriageState(
            episode_id=str(uuid4()),
            step_count=0,
            task_id=task_id,
        )
        self._current_index = 0
        self._results = []
        self._start_time = time.time()

        # Load task data
        self._load_task_data(task_id)

        self._state.total_emails = len(self._emails)
        self._state.processed_emails = 0
        self._state.correct_classifications = 0
        self._state.incorrect_classifications = 0
        self._state.missed_urgent = 0
        self._state.current_score = 0.0

        return self._make_observation()

    def reset_task(self, task_id: str = "easy") -> EmailTriageObservation:
        """
        Reset the environment with a specific task.

        Args:
            task_id: One of 'easy', 'medium', 'hard'
        """
        self._state = EmailTriageState(
            episode_id=str(uuid4()),
            step_count=0,
            task_id=task_id,
        )
        self._current_index = 0
        self._results = []
        self._start_time = time.time()

        self._load_task_data(task_id)

        self._state.total_emails = len(self._emails)
        self._state.processed_emails = 0
        self._state.correct_classifications = 0
        self._state.incorrect_classifications = 0
        self._state.missed_urgent = 0
        self._state.current_score = 0.0

        return self._make_observation()

    def step(self, action: EmailTriageAction) -> EmailTriageObservation:
        """
        Process the agent's action on the current email.

        Args:
            action: The action the agent wants to take

        Returns:
            EmailTriageObservation with next email, reward, and done status
        """
        self._state.step_count += 1

        # Handle edge case: already done
        if self._current_index >= len(self._emails):
            return self._make_done_observation(reward=0.0, reason="Episode already complete.")

        # Get ground truth for current email
        current_email = self._emails[self._current_index]
        email_id = current_email["email_id"]
        truth = self._ground_truth[email_id]

        # Compute reward with partial credit
        reward, reason = self._compute_reward(action, truth)

        # Track results
        self._results.append({
            "email_id": email_id,
            "action": {
                "action_type": action.action_type.value if action.action_type else None,
                "category": action.category.value if action.category else None,
                "priority": action.priority.value if action.priority else None,
                "reply_content": action.reply_content,
            },
            "truth": truth,
            "reward": reward,
        })

        # Update state counters
        if reward >= 0.7:
            self._state.correct_classifications += 1
        elif reward < 0.4:
            self._state.incorrect_classifications += 1

        if (
            truth.get("category") == "urgent"
            and (not action.category or action.category.value != "urgent")
        ):
            self._state.missed_urgent += 1

        # Advance to next email
        self._current_index += 1
        self._state.processed_emails = self._current_index
        self._state.current_score = self._cumulative_score()

        # Check if episode is done
        done = (
            self._current_index >= len(self._emails)
            or self._time_remaining() <= 0
        )

        if done:
            return self._make_done_observation(reward=reward, reason=reason)

        # Return next email observation
        obs = self._make_observation()
        obs.reward = reward
        obs.done = False
        obs.metadata = {
            "step": self._state.step_count,
            "reward_reason": reason,
            "cumulative_score": self._state.current_score,
        }
        return obs

    @property
    def state(self) -> EmailTriageState:
        """Get the current environment state."""
        return self._state

    # ── Private Methods ──────────────────────────────────────────────────

    def _load_task_data(self, task_id: str):
        """Load emails and ground truth for the specified task."""
        filepath = self._data_dir / f"emails_{task_id}.json"

        if not filepath.exists():
            # Generate data on the fly if not present
            try:
                from .email_generator import generate_dataset
            except ImportError:
                from server.email_generator import generate_dataset

            import os
            os.makedirs(self._data_dir, exist_ok=True)
            data = generate_dataset(task_id)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

        self._emails = data["emails"]
        self._ground_truth = {
            e["email_id"]: e["labels"] for e in data["emails"]
        }
        self._task_config = data["task_config"]
        self._time_limit = data["task_config"].get("time_limit", 300)

    def _make_observation(self) -> EmailTriageObservation:
        """Build an observation for the current email."""
        email = self._emails[self._current_index]

        return EmailTriageObservation(
            # Email fields
            email_id=email["email_id"],
            sender=email["sender"],
            sender_domain=email["sender_domain"],
            subject=email["subject"],
            body=email["body"],
            timestamp=email["timestamp"],
            has_attachments=email.get("has_attachments", False),
            reply_to=email.get("reply_to"),
            # Inbox status
            inbox_remaining=len(self._emails) - self._current_index - 1,
            emails_processed=self._current_index,
            time_remaining=self._time_remaining(),
            # Task info
            task_description=self._task_config["description"],
            available_actions=self._task_config["available_actions"],
            # Base observation fields
            done=False,
            reward=0.0,
        )

    def _make_done_observation(self, reward: float, reason: str) -> EmailTriageObservation:
        """Build a terminal observation when the episode is complete."""
        # Use last email for reference
        last_email = self._emails[-1] if self._emails else {}

        final_score = self._cumulative_score()

        return EmailTriageObservation(
            email_id=last_email.get("email_id", "done"),
            sender="system",
            sender_domain="system",
            subject="Episode Complete",
            body=f"All emails processed. Final score: {final_score:.3f}",
            timestamp="",
            has_attachments=False,
            reply_to=None,
            inbox_remaining=0,
            emails_processed=len(self._emails),
            time_remaining=0.0,
            task_description="Episode complete. No more actions needed.",
            available_actions=[],
            done=True,
            reward=reward,
            metadata={
                "final_score": final_score,
                "total_emails": len(self._emails),
                "correct": self._state.correct_classifications,
                "incorrect": self._state.incorrect_classifications,
                "missed_urgent": self._state.missed_urgent,
                "reward_reason": reason,
            },
        )

    def _compute_reward(self, action: EmailTriageAction, truth: dict) -> tuple[float, str]:
        """
        Compute reward with PARTIAL CREDIT.

        Scoring breakdown:
        - Category correct:    +0.50
        - Category close:      +0.20
        - Priority correct:    +0.30
        - Priority close (±1): +0.15
        - Action type correct: +0.20
        - Missing urgent:      -0.30 penalty

        Returns:
            Tuple of (score: float 0.0-1.0, reason: str)
        """
        score = 0.0
        reasons = []

        true_category = truth.get("category", "")
        true_priority = truth.get("priority", 3)
        expected_action = truth.get("expected_action", "classify")

        # ── Category accuracy (weight: 0.50) ──
        if action.category:
            predicted_cat = action.category.value
            if predicted_cat == true_category:
                score += 0.50
                reasons.append(f"✅ Category correct: {predicted_cat} (+0.50)")
            elif self._is_partially_correct(predicted_cat, true_category):
                score += 0.20
                reasons.append(
                    f"⚡ Category close: predicted={predicted_cat}, "
                    f"actual={true_category} (+0.20)"
                )
            else:
                reasons.append(
                    f"❌ Category wrong: predicted={predicted_cat}, "
                    f"actual={true_category} (+0.00)"
                )
        else:
            reasons.append("❌ No category provided (+0.00)")

        # ── Priority accuracy (weight: 0.30) ──
        if action.priority:
            predicted_pri = action.priority.value
            pri_diff = abs(predicted_pri - true_priority)
            if pri_diff == 0:
                score += 0.30
                reasons.append(f"✅ Priority correct: {predicted_pri} (+0.30)")
            elif pri_diff == 1:
                score += 0.15
                reasons.append(
                    f"⚡ Priority close: predicted={predicted_pri}, "
                    f"actual={true_priority} (+0.15)"
                )
            else:
                reasons.append(
                    f"❌ Priority wrong: predicted={predicted_pri}, "
                    f"actual={true_priority} (+0.00)"
                )
        else:
            reasons.append("❌ No priority provided (+0.00)")

        # ── Action type appropriateness (weight: 0.20) ──
        if action.action_type:
            if action.action_type.value == expected_action:
                score += 0.20
                reasons.append(f"✅ Action type correct: {expected_action} (+0.20)")
            else:
                reasons.append(
                    f"❌ Action type: predicted={action.action_type.value}, "
                    f"expected={expected_action} (+0.00)"
                )

        # ── PENALTY: Missing urgent emails ──
        if true_category == "urgent" and (
            not action.category or action.category.value != "urgent"
        ):
            score -= 0.30
            reasons.append("🚨 MISSED URGENT EMAIL (-0.30)")

        # ── BONUS: Quality reply for emails that need one ──
        if truth.get("needs_reply", False) and action.reply_content:
            expected_keywords = truth.get("response_keywords", [])
            if expected_keywords:
                hits = sum(
                    1 for kw in expected_keywords
                    if kw.lower() in action.reply_content.lower()
                )
                reply_bonus = min(0.10, (hits / len(expected_keywords)) * 0.10)
                score += reply_bonus
                if reply_bonus > 0:
                    reasons.append(
                        f"📝 Reply quality bonus: {hits}/{len(expected_keywords)} "
                        f"keywords (+{reply_bonus:.2f})"
                    )

        # Clamp to [0.0, 1.0]
        score = max(0.0, min(1.0, score))

        return round(score, 3), " | ".join(reasons)

    def _is_partially_correct(self, predicted: str, actual: str) -> bool:
        """Check if a prediction is in a similar neighborhood as the truth."""
        similar_groups = [
            {"urgent", "follow_up"},  # Both need attention
            {"fyi", "meeting"},       # Both informational
            {"spam"},                 # Spam is unique
            {"approval"},             # Approval is unique
        ]
        for group in similar_groups:
            if predicted in group and actual in group:
                return True
        return False

    def _cumulative_score(self) -> float:
        """Calculate the running average score."""
        if not self._results:
            return 0.0
        return round(
            sum(r["reward"] for r in self._results) / len(self._results),
            3,
        )

    def _time_remaining(self) -> float:
        """Calculate time remaining in the episode."""
        elapsed = time.time() - self._start_time
        return max(0.0, self._time_limit - elapsed)
