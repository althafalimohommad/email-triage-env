# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Email Triage Environment — An OpenEnv environment for AI email triage."""

from .client import EmailTriageEnv
from .models import (
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageState,
    EmailCategory,
    Priority,
    ActionType,
)

__all__ = [
    "EmailTriageAction",
    "EmailTriageObservation",
    "EmailTriageState",
    "EmailTriageEnv",
    "EmailCategory",
    "Priority",
    "ActionType",
]
