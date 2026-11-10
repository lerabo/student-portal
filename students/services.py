"""Доступ представлень до даних ядра student_portal."""

from django.conf import settings
from django.http import Http404

from student_portal.exceptions import StudentNotFoundError
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import load_group


def get_group() -> Group:
    """Завантажує групу з файлу, заданого в settings.STUDENT_PORTAL_DATA."""
    return load_group(settings.STUDENT_PORTAL_DATA)


def get_student_or_404(group: Group, student_id: int) -> Student:
    """Повертає студента групи або кидає Http404, якщо його немає."""
    try:
        return group.get(student_id)
    except StudentNotFoundError:
        raise Http404(f"Студента з id={student_id} немає") from None
