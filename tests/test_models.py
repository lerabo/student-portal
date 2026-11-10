"""Моделі, перенесення групи в базу даних і адмінпанель."""

from datetime import date

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError
from django.db.models import ProtectedError

from student_portal.grades import Grade as CoreGrade
from student_portal.storage import save_group
from students.models import Grade, Group, Student
from students.services import get_group, store_group

pytestmark = pytest.mark.django_db


def test_store_group_creates_records(group):
    assert store_group(group) == (3, 3)

    assert Group.objects.get().name == "КН-11"
    assert list(Student.objects.order_by("id").values_list("last_name", flat=True)) == [
        "Коваль",
        "Мельник",
        "Бойко",
    ]
    assert Grade.objects.count() == 3


def test_store_group_twice_does_not_duplicate(group):
    store_group(group)
    store_group(group)

    assert (Group.objects.count(), Student.objects.count(), Grade.objects.count()) == (
        1,
        3,
        3,
    )


def test_get_group_after_store_gives_same_ranking(group):
    store_group(group)

    loaded = get_group()

    assert loaded.name == group.name
    assert [s.id for s in loaded.ranking()] == [s.id for s in group.ranking()]
    assert loaded.get(1).average() == group.get(1).average()


def test_get_group_keeps_grade_dates(group):
    group.get(2).grades[0] = CoreGrade("Python", 61, date(2026, 10, 1))
    store_group(group)

    assert get_group().get(2).grades[0].graded_on == date(2026, 10, 1)


def test_model_strings(group):
    store_group(group)

    student = Student.objects.get(id=2)
    assert str(student.group) == "КН-11"
    assert str(student) == "Мельник Андрій"
    assert str(student.grades.get()) == "Мельник Андрій: Python 61"


def test_database_rejects_score_above_100(group):
    store_group(group)

    with pytest.raises(IntegrityError):
        Grade.objects.create(
            student_id=1, course="Git", score=101, graded_on=date(2026, 10, 1)
        )


def test_group_with_students_cannot_be_deleted(group):
    store_group(group)

    with pytest.raises(ProtectedError):
        Group.objects.get().delete()


def test_deleting_student_deletes_grades(group):
    store_group(group)

    Student.objects.get(id=1).delete()

    assert Grade.objects.count() == 1


def test_load_group_command(tmp_path, group, capsys):
    path = tmp_path / "group.json"
    save_group(group, path)

    call_command("load_group", str(path))

    assert "Група КН-11: студентів - 3, оцінок - 3" in capsys.readouterr().out
    assert Student.objects.count() == 3


def test_load_group_missing_file_raises_command_error(tmp_path):
    with pytest.raises(CommandError, match="не знайдено"):
        call_command("load_group", str(tmp_path / "nope.json"))


def test_admin_student_list_has_search(admin_client, db_group):
    response = admin_client.get("/admin/students/student/", {"q": "Мельник"})

    assert response.status_code == 200
    assert [str(s) for s in response.context["cl"].result_list] == ["Мельник Андрій"]


def test_admin_student_page_has_grades_inline(admin_client, db_group):
    response = admin_client.get("/admin/students/student/2/change/")

    assert response.status_code == 200
    assert 'name="grades-0-course"' in response.text


def test_admin_rejects_score_above_100(admin_client, db_group):
    grade = Grade.objects.get(student_id=2)
    data = {
        "group": Group.objects.get().id,
        "first_name": "Андрій",
        "last_name": "Мельник",
        "grades-TOTAL_FORMS": "1",
        "grades-INITIAL_FORMS": "1",
        "grades-0-id": grade.id,
        "grades-0-student": "2",
        "grades-0-course": "Python",
        "grades-0-score": "101",
        "grades-0-graded_on": "01.10.2026",
    }

    response = admin_client.post("/admin/students/student/2/change/", data)

    assert response.status_code == 200
    assert "менше чи дорівнює 100" in response.text
    assert Grade.objects.get(id=grade.id).score == 61
