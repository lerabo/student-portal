"""REST API: права DjangoModelPermissions, серіалізатори і кількість запитів."""

import pytest
from rest_framework.test import APIClient

from students.models import Grade, Group


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def teacher(api, role_user):
    api.force_authenticate(role_user("teacher", "Викладачі"))
    return api


@pytest.fixture
def dean(api, role_user):
    api.force_authenticate(role_user("dean", "Деканат"))
    return api


@pytest.fixture
def no_role(api, django_user_model):
    api.force_authenticate(django_user_model.objects.create_user("viewer"))
    return api


def test_anonymous_gets_403_with_message(api, db_group):
    response = api.get("/api/students/")

    assert response.status_code == 403
    assert response.json() == {"detail": "Реквізити перевірки достовірності не надані."}


def test_list_has_count_averages_and_letters(teacher, db_group):
    data = teacher.get("/api/students/").json()

    assert data["count"] == 3
    first = data["results"][0]
    assert (first["last_name"], first["average"]) == ("Коваль", 91.5)
    assert [g["ects"] for g in first["grades"]] == ["A", "B"]
    assert data["results"][2]["average"] is None


def test_list_makes_three_queries(teacher, db_group, django_assert_num_queries):
    # count для пагінації, студенти сторінки, оцінки всіх студентів (prefetch)
    with django_assert_num_queries(3):
        assert teacher.get("/api/students/").status_code == 200


def test_teacher_creates_grade_and_average_changes(teacher, db_group):
    response = teacher.post(
        "/api/grades/",
        {"student": 3, "course": "Git", "score": 74, "graded_on": "2026-11-02"},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["ects"] == "D"
    assert teacher.get("/api/students/3/").json()["average"] == 74


def test_score_101_gives_400_for_score_only(teacher, db_group):
    response = teacher.post(
        "/api/grades/",
        {"student": 3, "course": "Git", "score": 101, "graded_on": "2026-11-02"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "score": ["Переконайтесь, що значення менше або дорівнює 100."]
    }


def test_user_without_role_cannot_create_grade(no_role, db_group):
    response = no_role.post(
        "/api/grades/",
        {"student": 3, "course": "Git", "score": 74, "graded_on": "2026-11-02"},
        format="json",
    )

    assert response.status_code == 403
    assert not Grade.objects.filter(student_id=3).exists()


def test_dean_creates_student_without_grades(dean, db_group):
    response = dean.post(
        "/api/students/",
        {"first_name": "Олег", "last_name": "Новий", "group": Group.objects.get().pk},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["average"] is None
    assert response.json()["grades"] == []


def test_teacher_cannot_delete_student(teacher, db_group):
    response = teacher.delete("/api/students/3/")

    assert response.status_code == 403
    assert response.json() == {"detail": "У вас нема дозволу робити цю дію."}


def test_grades_cannot_be_changed_through_api(teacher, db_group):
    grade = Grade.objects.first()

    assert teacher.patch(f"/api/grades/{grade.pk}/", {"score": 100}).status_code == 404
    assert teacher.delete(f"/api/grades/{grade.pk}/").status_code == 404
