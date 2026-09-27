"""
chatbot/services.py — the brain of the AI Assistant.

Flow:

    User asks question
            ↓
    detect_intent()
            ↓
    Permission-aware data fetcher
            ↓
    Gemini AI API
            ↓
    If Gemini fails → Database fallback
            ↓
    Save response to ChatHistory
            ↓
    Return response
"""

from __future__ import annotations

import json
import re
import logging
import time

from dataclasses import dataclass, field
from typing import List, Dict, Any
from decimal import Decimal

import requests

from django.conf import settings
from accounts.models import User
from chatbot.models import ChatHistory


log = logging.getLogger(__name__)


# ============================================================================
# INTENT DETECTION
# ============================================================================

INTENT_KEYWORDS: Dict[str, List[str]] = {

    "my_attendance": [
        "my attendance",
        "my attend",
        "attendance",
        "আমার attendance",
        "attendance কেমন",
        "how many class",
    ],

    "my_cgpa": [
        "my cgpa",
        "my gpa",
        "আমার cgpa",
        "আমার gpa",
        "my grade",
        "my result",
    ],

    "my_fees": [
        "my fee",
        "my fees",
        "my due",
        "my dues",
        "fee",
        "fees",
        "due",
        "আমার fee",
        "আমার fees",
        "আমার due",
        "payment status",
        "unpaid fee",
        "unpaid fees",
    ],

    "my_courses": [
        "my course",
        "my courses",
        "আমার course",
        "আমার courses",
        "এই semester",
        "my subjects",
    ],

    "my_routine": [
        "my routine",
        "আমার routine",
        "class schedule",
        "my schedule",
    ],

    "my_notices": [
        "notice",
        "notices",
        "announcement",
        "what is new",
        "আজকের notice",
    ],

    "public_courses": [
        "courses available",
        "list courses",
        "cse courses",
        "department course",
    ],

    "public_teachers": [
        "who teaches",
        "teacher",
        "teachers",
        "faculty",
        "instructor of",
    ],

    "general": [],
}


# ============================================================================
# OTHER STUDENT DETECTION
# ============================================================================

OTHER_STUDENT_PATTERN = re.compile(
    r"\b("
    r"another student|"
    r"other student|"
    r"Rahim|"
    r"Karim|"
    r"someone else"
    r")\b",
    re.IGNORECASE,
)


def detect_intent(question: str) -> str:
    """
    Detect the intent of a question using simple keywords.
    """

    q = question.lower().strip()

    for intent in [
        "my_attendance",
        "my_cgpa",
        "my_fees",
        "my_courses",
        "my_routine",
        "my_notices",
        "public_courses",
        "public_teachers",
    ]:

        for keyword in INTENT_KEYWORDS[intent]:

            if keyword in q:
                return intent

    return "general"


def asks_about_other_student(question: str) -> bool:
    """
    Detect if the question is asking about another student's data.
    """

    return bool(
        OTHER_STUDENT_PATTERN.search(question or "")
    )


# ============================================================================
# PERMISSION RESULT
# ============================================================================

@dataclass
class PermissionResult:

    allowed: bool

    intent: str

    context: Dict[str, Any] = field(
        default_factory=dict
    )

    reason: str = ""


# ============================================================================
# PERMISSION-AWARE DATA FETCHER
# ============================================================================

def fetch_allowed_context(
    user: User,
    question: str,
    intent: str
) -> PermissionResult:

    """
    Return only the data the user is allowed to access.
    """

    # ------------------------------------------------------------------------
    # Anonymous user
    # ------------------------------------------------------------------------

    if not user or not user.is_authenticated:

        return PermissionResult(
            allowed=True,
            intent=intent,
            context={
                "note": (
                    "Anonymous access — "
                    "public information only."
                )
            },
            reason="anonymous",
        )

    # ------------------------------------------------------------------------
    # Student asking about another student's private information
    # ------------------------------------------------------------------------

    if (
        asks_about_other_student(question)
        and user.is_student
    ):

        return PermissionResult(
            allowed=False,
            intent=intent,
            context={},
            reason=(
                "Permission denied: cannot access "
                "another student's private data."
            ),
        )

    # ------------------------------------------------------------------------
    # Student / Teacher profile
    # ------------------------------------------------------------------------

    profile = (
        getattr(user, "student_profile", None)
        if user.is_student
        else None
    )

    teacher_profile = (
        getattr(user, "teacher_profile", None)
        if user.is_teacher
        else None
    )

    try:

        # Student information
        if intent == "my_attendance" and profile:
            return _fetch_my_attendance(profile)

        if intent == "my_cgpa" and profile:
            return _fetch_my_cgpa(profile)

        if intent == "my_fees" and profile:
            return _fetch_my_fees(profile)

        if intent == "my_courses" and profile:
            return _fetch_my_courses(profile)

        if intent == "my_routine" and profile:
            return _fetch_my_routine(profile)

        # Notices
        if intent == "my_notices":
            return _fetch_my_notices(user)

        # Public information
        if intent == "public_courses":
            return _fetch_public_courses()

        if intent == "public_teachers":
            return _fetch_public_teachers()

        # General question
        if intent == "general":

            return PermissionResult(
                allowed=True,
                intent=intent,
                context={
                    "note": (
                        "General conversational question — "
                        "no database access required."
                    ),
                    "university": "University Student Portal",
                },
                reason="general",
            )

    except Exception as e:

        log.exception(
            "Failed to fetch context for intent %s: %s",
            intent,
            e,
        )

        return PermissionResult(
            allowed=True,
            intent=intent,
            context={
                "note": (
                    "Could not retrieve context."
                )
            },
            reason="error",
        )

    return PermissionResult(
        allowed=True,
        intent=intent,
        context={
            "note": "No relevant data available."
        },
        reason="no_match",
    )


# ============================================================================
# ATTENDANCE
# ============================================================================

def _fetch_my_attendance(profile):

    from attendance.models import Attendance

    records = Attendance.objects.filter(
        enrollment__student=profile
    )

    total = records.count()

    present = records.filter(
        status="present"
    ).count()

    percentage = (
        present / total * 100
        if total
        else 0
    )

    return PermissionResult(
        allowed=True,
        intent="my_attendance",
        context={
            "student": str(profile),

            "total_classes": total,

            "present": present,

            "absent": total - present,

            "attendance_percent": round(
                percentage,
                2
            ),
        },
        reason="own_data",
    )


# ============================================================================
# CGPA
# ============================================================================

def _fetch_my_cgpa(profile):

    from results.models import (
        compute_cgpa,
        compute_gpa,
    )

    cgpa = compute_cgpa(profile)

    semester = profile.current_semester

    gpa = (
        compute_gpa(
            profile,
            semester
        )
        if semester
        else None
    )

    return PermissionResult(
        allowed=True,
        intent="my_cgpa",
        context={
            "student": str(profile),

            "cgpa": str(cgpa),

            "current_semester_gpa": (
                str(gpa)
                if gpa is not None
                else "N/A"
            ),

            "current_semester": (
                str(semester)
                if semester
                else "N/A"
            ),
        },
        reason="own_data",
    )


# ============================================================================
# FEES
# ============================================================================

def _fetch_my_fees(profile):

    from fees.models import Fee

    fees = Fee.objects.filter(
        student=profile
    )

    unpaid = fees.exclude(
        status="paid"
    )

    total_due = (
        sum(
            (
                fee.due_amount
                for fee in unpaid
            ),
            Decimal("0"),
        )
    )

    return PermissionResult(
        allowed=True,
        intent="my_fees",
        context={

            "student": str(profile),

            "total_fees": fees.count(),

            "unpaid_count": unpaid.count(),

            "total_due": str(total_due),

            "unpaid_items": [

                {
                    "type": fee.get_fee_type_display(),

                    "amount": str(
                        fee.amount
                    ),

                    "due": str(
                        fee.due_amount
                    ),
                }

                for fee in unpaid[:10]
            ],
        },

        reason="own_data",
    )


# ============================================================================
# COURSES
# ============================================================================

def _fetch_my_courses(profile):

    from academics.models import Enrollment

    enrollments = (
        Enrollment.objects
        .filter(
            student=profile,
            status="enrolled",
        )
        .select_related(
            "course",
            "course__instructor",
            "course__instructor__user",
        )
    )

    return PermissionResult(
        allowed=True,

        intent="my_courses",

        context={

            "student": str(profile),

            "current_semester": (
                str(profile.current_semester)
                if profile.current_semester
                else "N/A"
            ),

            "courses": [

                {
                    "code": enrollment.course.course_code,

                    "title": enrollment.course.title,

                    "credits": str(
                        enrollment.course.credits
                    ),

                    "section": enrollment.course.section,

                    "instructor": (
                        str(
                            enrollment.course.instructor
                        )
                        if enrollment.course.instructor
                        else "TBA"
                    ),
                }

                for enrollment in enrollments
            ],
        },

        reason="own_data",
    )


# ============================================================================
# ROUTINE
# ============================================================================

def _fetch_my_routine(profile):

    from academics.models import Enrollment

    enrollments = (
        Enrollment.objects
        .filter(
            student=profile,
            status="enrolled",
        )
        .select_related("course")
    )

    return PermissionResult(
        allowed=True,

        intent="my_routine",

        context={

            "student": str(profile),

            "routine": [

                {
                    "code": enrollment.course.course_code,

                    "schedule": (
                        enrollment.course.schedule
                        or "TBA"
                    ),

                    "room": (
                        enrollment.course.room
                        or "TBA"
                    ),
                }

                for enrollment in enrollments
            ],
        },

        reason="own_data",
    )


# ============================================================================
# NOTICES
# ============================================================================

def _fetch_my_notices(user):

    from notices.models import Notice

    notices = Notice.visible_to(user)[:5]

    return PermissionResult(
        allowed=True,

        intent="my_notices",

        context={

            "notices": [

                {
                    "title": notice.title,

                    "audience": (
                        notice.get_audience_display()
                    ),
                }

                for notice in notices
            ]
        },

        reason="own_data",
    )


# ============================================================================
# PUBLIC COURSES
# ============================================================================

def _fetch_public_courses():

    from academics.models import (
        Course,
        Department,
    )

    departments = Department.objects.filter(
        is_active=True
    )

    courses_by_department = {}

    for department in departments:

        courses_by_department[
            department.code
        ] = [

            {
                "code": course.course_code,

                "title": course.title,

                "credits": str(
                    course.credits
                ),
            }

            for course in Course.objects.filter(
                department=department,
                is_active=True,
            )[:5]
        ]

    return PermissionResult(
        allowed=True,

        intent="public_courses",

        context={
            "departments": courses_by_department
        },

        reason="public",
    )


# ============================================================================
# PUBLIC TEACHERS
# ============================================================================

def _fetch_public_teachers():

    from teachers.models import Teacher

    teachers = (
        Teacher.objects
        .filter(is_active=True)
        .select_related(
            "user",
            "department",
        )[:10]
    )

    return PermissionResult(
        allowed=True,

        intent="public_teachers",

        context={

            "teachers": [

                {
                    "name": teacher.full_name,

                    "department": (
                        teacher.department.code
                        if teacher.department
                        else "N/A"
                    ),

                    "designation": (
                        teacher.get_designation_display()
                    ),
                }

                for teacher in teachers
            ]
        },

        reason="public",
    )


# ============================================================================
# GEMINI API
# ============================================================================

def call_openai_api(
    messages: List[Dict[str, str]]
) -> str:

    """
    Call Gemini through the OpenAI-compatible API.

    Includes retry for temporary errors such as:
    429, 500, 502, 503 and 504.

    The actual API key is NEVER written to logs.
    """

    # ------------------------------------------------------------------------
    # Safe configuration logging
    # ------------------------------------------------------------------------

    log.info(
        "OpenAI config: key_exists=%s, key_length=%s, model=%s, url=%s",

        bool(settings.OPENAI_API_KEY),

        len(
            settings.OPENAI_API_KEY or ""
        ),

        settings.OPENAI_MODEL,

        settings.OPENAI_API_URL,
    )

    # ------------------------------------------------------------------------
    # API KEY CHECK
    # ------------------------------------------------------------------------

    if not settings.OPENAI_API_KEY:

        return "NO_API_KEY"

    # ------------------------------------------------------------------------
    # HEADERS
    # ------------------------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {settings.OPENAI_API_KEY}"
        ),

        "Content-Type": "application/json",
    }

    # ------------------------------------------------------------------------
    # REQUEST DATA
    # ------------------------------------------------------------------------

    payload = {

        "model": settings.OPENAI_MODEL,

        "messages": messages,

        "temperature": 0.3,

        "max_tokens": 400,
    }

    # ------------------------------------------------------------------------
    # RETRY
    # ------------------------------------------------------------------------

    for attempt in range(3):

        try:

            response = requests.post(

                settings.OPENAI_API_URL,

                headers=headers,

                json=payload,

                timeout=20,
            )

            # ---------------------------------------------------------------
            # HTTP ERROR
            # ---------------------------------------------------------------

            response.raise_for_status()

            # ---------------------------------------------------------------
            # JSON RESPONSE
            # ---------------------------------------------------------------

            data = response.json()

            # ---------------------------------------------------------------
            # EXTRACT ANSWER
            # ---------------------------------------------------------------

            reply = (
                data["choices"][0]["message"]["content"]
                .strip()
            )

            return reply

        # --------------------------------------------------------------------
        # HTTP ERROR
        # --------------------------------------------------------------------

        except requests.exceptions.HTTPError:

            status = response.status_code

            log.error(
                "AI API error: status=%s body=%s",
                status,
                response.text[:1000],
            )

            # Temporary errors
            if status in [
                429,
                500,
                502,
                503,
                504,
            ]:

                if attempt < 2:

                    log.warning(
                        "Temporary AI error. "
                        "Retrying... attempt=%s",
                        attempt + 2,
                    )

                    time.sleep(2)

                    continue

            return f"API_ERROR_{status}"

        # --------------------------------------------------------------------
        # CONNECTION / OTHER ERROR
        # --------------------------------------------------------------------

        except Exception as e:

            log.exception(
                "AI API call failed: %s",
                e,
            )

            if attempt < 2:

                log.warning(
                    "Retrying AI request..."
                )

                time.sleep(2)

                continue

            return "API_CONNECTION_ERROR"

    return "API_CONNECTION_ERROR"


# ============================================================================
# DATABASE FALLBACK
# ============================================================================

def fallback_reply(
    intent: str,
    context: Dict[str, Any]
) -> str:

    """
    Create a simple database-based answer when Gemini
    is temporarily unavailable.

    This makes important student information available
    even when the AI API has a temporary problem.
    """

    # ------------------------------------------------------------------------
    # ATTENDANCE
    # ------------------------------------------------------------------------

    if intent == "my_attendance":

        return (
            "📊 Your attendance:\n\n"

            f"Student: "
            f"{context.get('student', 'N/A')}\n"

            f"Total Classes: "
            f"{context.get('total_classes', 0)}\n"

            f"Present: "
            f"{context.get('present', 0)}\n"

            f"Absent: "
            f"{context.get('absent', 0)}\n"

            f"Attendance: "
            f"{context.get('attendance_percent', 0)}%"
        )

    # ------------------------------------------------------------------------
    # CGPA
    # ------------------------------------------------------------------------

    if intent == "my_cgpa":

        return (
            "📚 Your academic result:\n\n"

            f"Student: "
            f"{context.get('student', 'N/A')}\n"

            f"CGPA: "
            f"{context.get('cgpa', 'N/A')}\n"

            f"Current Semester GPA: "
            f"{context.get('current_semester_gpa', 'N/A')}\n"

            f"Semester: "
            f"{context.get('current_semester', 'N/A')}"
        )

    # ------------------------------------------------------------------------
    # FEES
    # ------------------------------------------------------------------------

    if intent == "my_fees":

        items = context.get(
            "unpaid_items",
            []
        )

        reply = (
            "💰 Your fee information:\n\n"

            f"Student: "
            f"{context.get('student', 'N/A')}\n"

            f"Total Fee Records: "
            f"{context.get('total_fees', 0)}\n"

            f"Unpaid Items: "
            f"{context.get('unpaid_count', 0)}\n"

            f"Total Due: "
            f"{context.get('total_due', '0')}\n"
        )

        if items:

            reply += "\nUnpaid fees:\n"

            for item in items:

                reply += (
                    f"- "
                    f"{item.get('type', 'Fee')}: "
                    f"{item.get('due', '0')}\n"
                )

        else:

            reply += (
                "\n✅ You have no unpaid fees."
            )

        return reply

    # ------------------------------------------------------------------------
    # COURSES
    # ------------------------------------------------------------------------

    if intent == "my_courses":

        courses = context.get(
            "courses",
            []
        )

        reply = (
            "📚 Your courses:\n\n"

            f"Semester: "
            f"{context.get('current_semester', 'N/A')}\n"
        )

        if not courses:

            return (
                reply +
                "\nNo enrolled courses found."
            )

        for course in courses:

            reply += (

                f"\n• "
                f"{course.get('code', 'N/A')} - "
                f"{course.get('title', 'N/A')}\n"

                f"  Credits: "
                f"{course.get('credits', 'N/A')}\n"

                f"  Section: "
                f"{course.get('section', 'N/A')}\n"

                f"  Instructor: "
                f"{course.get('instructor', 'TBA')}\n"
            )

        return reply

    # ------------------------------------------------------------------------
    # ROUTINE
    # ------------------------------------------------------------------------

    if intent == "my_routine":

        routine = context.get(
            "routine",
            []
        )

        if not routine:

            return (
                "📅 No routine information "
                "was found."
            )

        reply = "📅 Your class routine:\n"

        for item in routine:

            reply += (

                f"\n• "
                f"{item.get('code', 'N/A')}\n"

                f"  Schedule: "
                f"{item.get('schedule', 'TBA')}\n"

                f"  Room: "
                f"{item.get('room', 'TBA')}\n"
            )

        return reply

    # ------------------------------------------------------------------------
    # NOTICES
    # ------------------------------------------------------------------------

    if intent == "my_notices":

        notices = context.get(
            "notices",
            []
        )

        if not notices:

            return (
                "📢 No notices are "
                "currently available."
            )

        reply = "📢 Recent notices:\n"

        for notice in notices:

            reply += (

                f"\n• "
                f"{notice.get('title', 'Untitled')}"

                f" "
                f"({notice.get('audience', 'All')})"
            )

        return reply

    # ------------------------------------------------------------------------
    # PUBLIC COURSES
    # ------------------------------------------------------------------------

    if intent == "public_courses":

        departments = context.get(
            "departments",
            {}
        )

        if not departments:

            return (
                "📚 No courses are "
                "currently available."
            )

        reply = "📚 Available courses:\n"

        for department, courses in departments.items():

            reply += (
                f"\n{department}:\n"
            )

            for course in courses:

                reply += (

                    f"• "
                    f"{course.get('code', 'N/A')} - "

                    f"{course.get('title', 'N/A')} "

                    f"({course.get('credits', 'N/A')} "
                    f"credits)\n"
                )

        return reply

    # ------------------------------------------------------------------------
    # PUBLIC TEACHERS
    # ------------------------------------------------------------------------

    if intent == "public_teachers":

        teachers = context.get(
            "teachers",
            []
        )

        if not teachers:

            return (
                "👨‍🏫 No teacher information "
                "is currently available."
            )

        reply = "👨‍🏫 Teachers:\n"

        for teacher in teachers:

            reply += (

                f"\n• "
                f"{teacher.get('name', 'N/A')}\n"

                f"  Department: "
                f"{teacher.get('department', 'N/A')}\n"

                f"  Designation: "
                f"{teacher.get('designation', 'N/A')}\n"
            )

        return reply

    # ------------------------------------------------------------------------
    # GENERAL
    # ------------------------------------------------------------------------

    return (
        "🤖 The AI service is temporarily "
        "unavailable. Please try again in a moment."
    )


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = (

    "You are the AI Student Assistant "
    "for a University Student Portal. "

    "Answer the user based ONLY on the "
    'data provided in the "context" below. '

    "Be concise and friendly. "

    "Answer in the user's language "
    "(English or Bangla). "

    "If the context is empty or marked "
    "as permission-denied, refuse politely. "

    "Do NOT invent any student data "
    "not present in the context."
)


# ============================================================================
# MAIN RESPOND FUNCTION
# ============================================================================

def respond(
    user,
    question: str
) -> Dict[str, Any]:

    """
    Main chatbot entrypoint.
    """

    # ------------------------------------------------------------------------
    # EMPTY QUESTION
    # ------------------------------------------------------------------------

    if not question or not question.strip():

        return {

            "reply": (
                "Please type a question first."
            ),

            "intent": "empty",

            "allowed": True,
        }

    # ------------------------------------------------------------------------
    # DETECT INTENT
    # ------------------------------------------------------------------------

    intent = detect_intent(question)

    # ------------------------------------------------------------------------
    # GET ALLOWED CONTEXT
    # ------------------------------------------------------------------------

    permission = fetch_allowed_context(
        user,
        question,
        intent,
    )

    # ------------------------------------------------------------------------
    # SAVE USER QUESTION
    # ------------------------------------------------------------------------

    if user and user.is_authenticated:

        ChatHistory.objects.create(

            user=user,

            role=ChatHistory.Role.USER,

            content=question,

            intent=intent,

            is_allowed=permission.allowed,

            metadata={

                "reason": permission.reason,

                "context_keys": list(
                    permission.context.keys()
                ),
            },
        )

    # ------------------------------------------------------------------------
    # PERMISSION DENIED
    # ------------------------------------------------------------------------

    if not permission.allowed:

        reply = (

            "🚫 I cannot share another student's "
            "private data. "

            "You can only ask about your own "
            "attendance, results, fees, and courses. "

            "If you need help with another student, "
            "please contact the academic office."
        )

        if user and user.is_authenticated:

            ChatHistory.objects.create(

                user=user,

                role=ChatHistory.Role.ASSISTANT,

                content=reply,

                intent=intent,

                is_allowed=False,
            )

        return {

            "reply": reply,

            "intent": intent,

            "allowed": False,

            "reason": permission.reason,
        }

    # ------------------------------------------------------------------------
    # PREPARE CONTEXT
    # ------------------------------------------------------------------------

    context_str = json.dumps(

        permission.context,

        default=str,

        ensure_ascii=False,

        indent=2,
    )

    # ------------------------------------------------------------------------
    # AI MESSAGES
    # ------------------------------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },

        {
            "role": "system",
            "content": (
                "Allowed context:\n"
                f"{context_str}"
            ),
        },

        {
            "role": "user",
            "content": question,
        },
    ]

    # ------------------------------------------------------------------------
    # CALL GEMINI
    # ------------------------------------------------------------------------

    reply = call_openai_api(messages)

    # ------------------------------------------------------------------------
    # FALLBACK IF GEMINI FAILS
    # ------------------------------------------------------------------------

    if (

        reply.startswith("API_ERROR_")

        or reply in [
            "API_CONNECTION_ERROR",
            "NO_API_KEY",
        ]
    ):

        log.warning(
            "Using database fallback for intent=%s",
            intent,
        )

        reply = fallback_reply(
            intent,
            permission.context,
        )

    # ------------------------------------------------------------------------
    # SAVE ASSISTANT REPLY
    # ------------------------------------------------------------------------

    if user and user.is_authenticated:

        ChatHistory.objects.create(

            user=user,

            role=ChatHistory.Role.ASSISTANT,

            content=reply,

            intent=intent,

            is_allowed=True,

            metadata={

                "context_summary": (

                    permission.context
                    .get("note", "")[:80]
                ),

            },
        )

    # ------------------------------------------------------------------------
    # RETURN RESULT
    # ------------------------------------------------------------------------

    return {

        "reply": reply,

        "intent": intent,

        "allowed": True,

        "reason": permission.reason,
    }


# ============================================================================
# CHAT HISTORY
# ============================================================================

def get_recent_history(
    user,
    limit: int = 10
) -> List[Dict[str, Any]]:

    """
    Get user's recent conversation history.
    """

    if not user or not user.is_authenticated:

        return []

    limit = (
        limit
        or settings.CHATBOT_MAX_HISTORY
    )

    rows = (

        ChatHistory.objects

        .filter(
            user=user
        )

        .order_by(
            "-created_at"
        )[:limit]
    )

    rows = rows[::-1]

    return [

        {

            "role": history.role,

            "content": history.content,

            "intent": history.intent,

            "ts": history.created_at.isoformat(),

        }

        for history in rows
    ]