"""Доступ вебшару до даних: база даних Django ↔ ядро student_portal."""

from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404

from student_portal.exceptions import StorageError, StudentNotFoundError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student

from . import models


def get_group() -> Group:
    """Група з бази даних як об'єкт ядра: правила (рейтинг, ECTS) лишаються в ядрі."""
    students = models.Student.objects.order_by("id").prefetch_related(
        Prefetch("grades", queryset=models.Grade.objects.order_by("graded_on", "id"))
    )
    record = models.Group.objects.prefetch_related(
        Prefetch("students", queryset=students)
    ).first()
    if record is None:
        raise StorageError("у базі даних немає групи: виконайте manage.py load_group")
    group = Group(record.name)
    for s in record.students.all():
        grades = [Grade(g.course, g.score, g.graded_on) for g in s.grades.all()]
        group.add(Student(s.id, s.first_name, s.last_name, grades))
    return group


@transaction.atomic
def store_group(group: Group) -> tuple[int, int]:
    """Зберігає групу ядра в базі даних; повторний виклик оновлює ті самі записи."""
    record, _ = models.Group.objects.get_or_create(name=group.name)
    grades = 0
    for s in group:
        student, _ = models.Student.objects.update_or_create(
            id=s.id,
            defaults={
                "group": record,
                "first_name": s.first_name,
                "last_name": s.last_name,
            },
        )
        student.grades.all().delete()
        models.Grade.objects.bulk_create(
            models.Grade(
                student=student, course=g.course, score=g.score, graded_on=g.graded_on
            )
            for g in s.grades
        )
        grades += len(s.grades)
    return len(group), grades


def get_student_or_404(group: Group, student_id: int) -> Student:
    """Повертає студента групи або кидає Http404, якщо його немає."""
    try:
        return group.get(student_id)
    except StudentNotFoundError:
        raise Http404(f"Студента з id={student_id} немає") from None
