# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Email Triage Environment.

Defines typed Pydantic models for Actions (what the agent can do),
Observations (what the agent sees), and custom State tracking.
"""

from enum import Enum
from typing import Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


# ── Enums ────────────────────────────────────────────────────────────────────


class EmailCategory(str, Enum):
    """Categories an email can be classified into."""

    URGENT = "urgent"
    FOLLOW_UP = "follow_up"
    FYI = "fyi"
    SPAM = "spam"
    MEETING = "meeting"
    APPROVAL = "approval"


class Priority(int, Enum):
    """Priority levels for emails (1 = lowest, 5 = critical)."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    NONE = 1


class ActionType(str, Enum):
    """Types of actions the agent can take on an email."""

    CLASSIFY = "classify"
    REPLY = "reply"
    ARCHIVE = "archive"
    FLAG = "flag"
    ESCALATE = "escalate"
    SKIP = "skip"


# ── Action Model ─────────────────────────────────────────────────────────────


class EmailTriageAction(Action):
    """
    Action for the Email Triage environment.

    The agent sends this to indicate what it wants to do with the current email.
    Different tasks allow different action types.
    """

    action_type: ActionType = Field(
        ..., description="The type of action to take on the current email"
    )
    category: Optional[EmailCategory] = Field(
        default=None,
        description="Email category (required for CLASSIFY action)",
    )
    priority: Optional[Priority] = Field(
        default=None,
        description="Priority level 1-5 (required for CLASSIFY action)",
    )
    reply_content: Optional[str] = Field(
        default=None,
        description="Draft reply content (required for REPLY action)",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Brief explanation of why the agent chose this action",
    )


# ── Observation Model ────────────────────────────────────────────────────────


class EmailTriageObservation(Observation):
    """
    Observation from the Email Triage environment.

    Contains the current email to process and inbox status information.
    """

    # Current email fields
    email_id: str = Field(default="", description="Unique ID of the current email")
    sender: str = Field(default="", description="Sender email address")
    sender_domain: str = Field(default="", description="Domain of the sender")
    subject: str = Field(default="", description="Email subject line")
    body: str = Field(default="", description="Email body content")
    timestamp: str = Field(default="", description="When the email was sent")
    has_attachments: bool = Field(default=False, description="Whether email has attachments")
    reply_to: Optional[str] = Field(default=None, description="Thread parent (if reply)")

    # Inbox status
    inbox_remaining: int = Field(default=0, description="Emails left to process")
    emails_processed: int = Field(default=0, description="Emails already handled")
    time_remaining: float = Field(default=0.0, description="Seconds left in episode")

    # Task info
    task_description: str = Field(default="", description="What the agent should do")
    available_actions: list[str] = Field(
        default_factory=list, description="Valid action types for this task"
    )


# ── Custom State ─────────────────────────────────────────────────────────────


class EmailTriageState(State):
    """
    Extended state for tracking email triage episode progress.
    """

    task_id: str = Field(default="easy", description="Current task identifier")
    total_emails: int = Field(default=0, description="Total emails in this episode")
    processed_emails: int = Field(default=0, description="Emails processed so far")
    correct_classifications: int = Field(default=0, description="Correct actions taken")
    incorrect_classifications: int = Field(default=0, description="Incorrect actions taken")
    missed_urgent: int = Field(default=0, description="Urgent emails missed (penalty)")
    current_score: float = Field(default=0.0, description="Running average score")
