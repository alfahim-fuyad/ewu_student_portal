"""
chatbot/services.py — the brain of the AI Assistant.

This is the ONLY place that decides what data the AI is allowed to see and
the only place that talks to the upstream AI API. Keeping this isolated makes
permission rules auditable.

Flow:
    User asks question
        ↓
    services.respond(user, question)
        ↓
    Intent detector extracts:
        - my_attendance / my_cgpa / my_fees / my_courses / my_routine
        - public_course_info / public_teacher_info
        - notice_query
        - general_query
        ↓
    Permission-aware data fetcher returns ALLOWED context as JSON
        ↓
    AI is called with this small, pre-filtered context as system prompt
        ↓
    Response saved to ChatHistory + returned to caller

PERMISSION RULES (hard-coded & testable):
    ✅ Student can ask about THEIR OWN attendance / results / fees / courses
    ✅ Anyone can ask about public course / department / teacher info
    ❌ Student CANNOT ask about another student's private data
    ❌ Teacher info past department/code/designation is restricted
"""
from __future__ import annotations
import json
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any
from decimal import Decimal

import requests
from django.conf import settings
from django.utils.timezone import now

from accounts.models import User
from chatbot.models import ChatHistory

log = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Intent detection — keyword based (no AI needed, fully testable)
# ----------------------------------------------------------------------------

INTENT_KEYWORDS: Dict[str, List[str]] = {
    'my_attendance': ['my attendance', 'আমার attendance', 'attendance কেমন', 'how many class'],
    'my_cgpa': ['my cgpa', 'my gpa', 'আমার cgpa', 'আমার gpa', 'my grade', 'my result'],
    'my_fees': ['my fee', 'my due', 'আমার fee', 'আমার due', 'payment status', 'unpaid fee'],
    'my_courses': ['my course', 'my courses', 'আমার course', 'এই semester', 'my subjects'],
    'my_routine': ['my routine', 'আমার routine', 'class schedule', 'my schedule'],
    'my_notices': ['notice', 'announcement', 'what is new', 'আজকের notice'],
    'public_courses': ['courses available', 'list courses', 'cse courses', 'department course'],
    'public_teachers': ['who teaches', 'teacher', 'faculty', 'instructor of'],
    'general': [],
}

# Patterns that indicate the user is asking about ANOTHER student's data
OTHER_STUDENT_PATTERN = re.compile(
    r'\b(another student|other student|Rahim|Karim|someone else|'
    r'(\w+)-er (cgpa|gpa|result|attendance|fee))', re.IGNORECASE,
)


def detect_intent(question: str) -> str:
    """Detect the intent of a question from keywords. Returns 'general' if no match."""
    q = question.lower().strip()
    # Check from most-specific to least-specific
    for intent in [
        'my_attendance', 'my_cgpa', 'my_fees', 'my_courses',
        'my_routine', 'my_notices', 'public_courses', 'public_teachers',
    ]:
        for kw in INTENT_KEYWORDS[intent]:
            if kw in q:
                return intent
    return 'general'


def asks_about_other_student(question: str) -> bool:
    """Detect if the question is asking about another student's data."""
    return bool(OTHER_STUDENT_PATTERN.search(question or ''))


# ----------------------------------------------------------------------------
# Permission-aware data fetcher
# ----------------------------------------------------------------------------

@dataclass
class PermissionResult:
    allowed: bool
    intent: str
    context: Dict[str, Any] = field(default_factory=dict)
    reason: str = ''


def fetch_allowed_context(user: User, question: str, intent: str) -> PermissionResult:
    """Return the slice of data the AI is allowed to see, given the question intent."""

    # No user → no private context
    if not user or not user.is_authenticated:
        return PermissionResult(
            allowed=True,
            intent=intent,
            context={'note': 'Anonymous access — public info only.'},
            reason='anonymous',
        )

    # If the user asks about another student, BLOCK immediately
    if asks_about_other_student(question) and user.is_student:
        return PermissionResult(
            allowed=False,
            intent=intent,
            context={},
            reason='Permission denied: cannot access another student private data.',
        )

    profile = getattr(user, 'student_profile', None) if user.is_student else None
    teacher_profile = getattr(user, 'teacher_profile', None) if user.is_teacher else None

    try:
        if intent == 'my_attendance' and profile:
            return _fetch_my_attendance(profile)
        if intent == 'my_cgpa' and profile:
            return _fetch_my_cgpa(profile)
        if intent == 'my_fees' and profile:
            return _fetch_my_fees(profile)
        if intent == 'my_courses' and profile:
            return _fetch_my_courses(profile)
        if intent == 'my_routine' and profile:
            return _fetch_my_routine(profile)
        if intent == 'my_notices':
            return _fetch_my_notices(user)
        if intent == 'public_courses':
            return _fetch_public_courses()
        if intent == 'public_teachers':
            return _fetch_public_teachers()
        if intent == 'general':
            return PermissionResult(
                allowed=True,
                intent=intent,
                context={
                    'note': 'General conversational question — no database access required.',
                    'university': 'University Student Portal',
                },
                reason='general',
            )
    except Exception as e:
        log.exception('Failed to fetch context for intent %s: %s', intent, e)
        return PermissionResult(
            allowed=True, intent=intent,
            context={'note': f'Could not retrieve context: {e}'},
            reason='error',
        )

    # No matching permission — return general context
    return PermissionResult(
        allowed=True,
        intent=intent,
        context={'note': 'No relevant data available.'},
        reason='no_match',
    )


def _fetch_my_attendance(profile):
    from attendance.models import Attendance
    from django.db.models import Count, Q
    records = Attendance.objects.filter(enrollment__student=profile)
    total = records.count()
    present = records.filter(status='present').count()
    pct = (present / total * 100) if total else 0
    return PermissionResult(
        allowed=True, intent='my_attendance',
        context={
            'student': str(profile),
            'total_classes': total,
            'present': present,
            'absent': total - present,
            'attendance_percent': round(pct, 2),
        },
        reason='own_data',
    )


def _fetch_my_cgpa(profile):
    from results.models import compute_cgpa, compute_gpa
    cgpa = compute_cgpa(profile)
    sem = profile.current_semester
    gpa = compute_gpa(profile, sem) if sem else None
    return PermissionResult(
        allowed=True, intent='my_cgpa',
        context={
            'student': str(profile),
            'cgpa': str(cgpa),
            'current_semester_gpa': str(gpa) if gpa else 'N/A',
            'current_semester': str(sem) if sem else 'N/A',
        },
        reason='own_data',
    )


def _fetch_my_fees(profile):
    from fees.models import Fee
    fees = Fee.objects.filter(student=profile)
    unpaid = fees.exclude(status='paid')
    total_due = sum(f.due_amount for f in unpaid) or Decimal('0')
    return PermissionResult(
        allowed=True, intent='my_fees',
        context={
            'student': str(profile),
            'total_fees': fees.count(),
            'unpaid_count': unpaid.count(),
            'total_due': str(total_due),
            'unpaid_items': [
                {'type': f.get_fee_type_display(), 'amount': str(f.amount), 'due': str(f.due_amount)}
                for f in unpaid[:10]
            ],
        },
        reason='own_data',
    )


def _fetch_my_courses(profile):
    from academics.models import Enrollment
    enrolls = Enrollment.objects.filter(
        student=profile, status='enrolled',
    ).select_related('course', 'course__instructor', 'course__instructor__user')
    return PermissionResult(
        allowed=True, intent='my_courses',
        context={
            'student': str(profile),
            'current_semester': str(profile.current_semester) if profile.current_semester else 'N/A',
            'courses': [
                {
                    'code': e.course.course_code,
                    'title': e.course.title,
                    'credits': str(e.course.credits),
                    'section': e.course.section,
                    'instructor': str(e.course.instructor) if e.course.instructor else 'TBA',
                }
                for e in enrolls
            ],
        },
        reason='own_data',
    )


def _fetch_my_routine(profile):
    from academics.models import Enrollment
    enrolls = Enrollment.objects.filter(
        student=profile, status='enrolled',
    ).select_related('course')
    return PermissionResult(
        allowed=True, intent='my_routine',
        context={
            'student': str(profile),
            'routine': [
                {
                    'code': e.course.course_code,
                    'schedule': e.course.schedule or 'TBA',
                    'room': e.course.room or 'TBA',
                }
                for e in enrolls
            ],
        },
        reason='own_data',
    )


def _fetch_my_notices(user):
    from notices.models import Notice
    qs = Notice.visible_to(user)[:5]
    return PermissionResult(
        allowed=True, intent='my_notices',
        context={
            'notices': [
                {'title': n.title, 'audience': n.get_audience_display()} for n in qs
            ]
        },
        reason='own_data',
    )


def _fetch_public_courses():
    from academics.models import Course, Department
    depts = Department.objects.filter(is_active=True)
    courses_by_dept = {}
    for d in depts:
        courses_by_dept[d.code] = [
            {'code': c.course_code, 'title': c.title, 'credits': str(c.credits)}
            for c in Course.objects.filter(department=d, is_active=True)[:5]
        ]
    return PermissionResult(
        allowed=True, intent='public_courses',
        context={'departments': courses_by_dept},
        reason='public',
    )


def _fetch_public_teachers():
    from teachers.models import Teacher
    teachers = Teacher.objects.filter(is_active=True).select_related('user', 'department')[:10]
    return PermissionResult(
        allowed=True, intent='public_teachers',
        context={
            'teachers': [
                {
                    'name': t.full_name,
                    'department': t.department.code if t.department else 'N/A',
                    'designation': t.get_designation_display(),
                }
                for t in teachers
            ]
        },
        reason='public',
    )


# ----------------------------------------------------------------------------
# AI API integration
# ----------------------------------------------------------------------------

def call_openai_api(messages: List[Dict[str, str]]) -> str:
    """Call the configured AI API. Returns the assistant's text reply."""
    if not settings.OPENAI_API_KEY:
        return (
            '🤖 I understand your question. However, no AI API key is configured. '
            'Set OPENAI_API_KEY in your .env file to enable real answers.'
        )

    headers = {
        'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': settings.OPENAI_MODEL,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 400,
    }

    try:
        response = requests.post(
            settings.OPENAI_API_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except requests.exceptions.HTTPError as e:
        log.exception('OpenAI API HTTP error: %s', e)
        return f'🤖 The AI service returned an error. Please try again later. (HTTP {response.status_code})'
    except Exception as e:
        log.exception('AI API call failed: %s', e)
        return f'🤖 Sorry, I could not reach the AI service right now. ({type(e).__name__})'


# ----------------------------------------------------------------------------
# Public entrypoint used by views
# ----------------------------------------------------------------------------

SYSTEM_PROMPT = (
    'You are the AI Student Assistant for a University Student Portal. '
    'Answer the user based ONLY on the data provided in the "context" below. '
    'Be concise, friendly, and answer in the user\'s language (English or Bangla). '
    'If the context is empty or marked as permission-denied, refuse politely. '
    'Do NOT invent any student data not present in the context.'
)


def respond(user, question: str) -> Dict[str, Any]:
    """Top-level entrypoint — given a user + question, return AI reply dict."""
    if not question or not question.strip():
        return {'reply': 'Please type a question first.', 'intent': 'empty', 'allowed': True}

    intent = detect_intent(question)
    perm = fetch_allowed_context(user, question, intent)

    # Save user question to history
    if user and user.is_authenticated:
        ChatHistory.objects.create(
            user=user,
            role=ChatHistory.Role.USER,
            content=question,
            intent=intent,
            is_allowed=perm.allowed,
            metadata={'reason': perm.reason, 'context_keys': list(perm.context.keys())},
        )

    if not perm.allowed:
        reply = (
            '🚫 I cannot share another student\'s private data. '
            'You can only ask about your own attendance, results, fees, and courses. '
            'If you need help with another student, please contact the academic office.'
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
            'reply': reply,
            'intent': intent,
            'allowed': False,
            'reason': perm.reason,
        }

    # Build AI messages
    context_str = json.dumps(perm.context, default=str, ensure_ascii=False, indent=2)
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'system', 'content': f'Allowed context:\n{context_str}'},
        {'role': 'user', 'content': question},
    ]

    reply = call_openai_api(messages)

    # Save assistant reply
    if user and user.is_authenticated:
        ChatHistory.objects.create(
            user=user,
            role=ChatHistory.Role.ASSISTANT,
            content=reply,
            intent=intent,
            is_allowed=True,
            metadata={'context_summary': perm.context.get('note', '')[:80]},
        )

    return {
        'reply': reply,
        'intent': intent,
        'allowed': True,
        'reason': perm.reason,
    }


def get_recent_history(user, limit: int = 10) -> List[Dict[str, Any]]:
    """Get the user's recent conversation for display in the chat window."""
    if not user or not user.is_authenticated:
        return []
    limit = limit or settings.CHATBOT_MAX_HISTORY
    rows = (ChatHistory.objects
            .filter(user=user)
            .order_by('-created_at')[:limit])[::-1]
    return [
        {
            'role': h.role,
            'content': h.content,
            'intent': h.intent,
            'ts': h.created_at.isoformat(),
        }
        for h in rows
    ]
