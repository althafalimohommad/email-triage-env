"""Task graders package for Email Triage Environment."""

from .task_easy import grade as grade_easy
from .task_medium import grade as grade_medium
from .task_hard import grade as grade_hard

__all__ = ["grade_easy", "grade_medium", "grade_hard"]
