from typing import Any, Dict

from .auth import (
    Account,
    AccountParameters,
    FamilyProfile,
    LoginResponse,
    StudentProfile,
)
from .common import ClasseInfo, Contact, Module, Subject
from .grades import (
    Grade,
    GradesResponse,
    Period,
    ProgramElement,
    SubjectGrades,
)
from .homework import HomeworkAssignment, HomeworkResponse
from .messages import Message, MessageFile, MessagesResponse
from .schedule import ScheduleEvent, ScheduleResponse

# Type alias for backward compatibility during refactor
ApiResponse = Dict[str, Any]

__all__ = [
    "Module",
    "ClasseInfo",
    "Subject",
    "Contact",
    "Account",
    "AccountParameters",
    "FamilyProfile",
    "LoginResponse",
    "StudentProfile",
    "Grade",
    "GradesResponse",
    "Period",
    "ProgramElement",
    "SubjectGrades",
    "HomeworkAssignment",
    "HomeworkResponse",
    "ScheduleEvent",
    "ScheduleResponse",
    "Message",
    "MessageFile",
    "MessagesResponse",
]
