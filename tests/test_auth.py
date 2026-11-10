"""Вхід, ролі і сторінки з формами: права перевіряються на сервері."""

import io
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group as Role
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from students.models import Grade, Group, Student

YESTERDAY = timezone.localdate() - timedelta(days=1)


@pytest.fixture
def teacher(client, role_user):
    """Клієнт від імені викладача."""
    client.force_login(role_user("teacher", "Викладачі"))
    return client


@pytest.fixture
def dean(client, role_user):
    """Клієнт від імені деканату."""
    client.force_login(role_user("dean", "Деканат"))
    return client


def test_anonymous_is_redirected_to_login(anonymous, db):
    response = anonymous.get("/students/")

    assertRedirects(
        response, "/accounts/login/?next=/students/", fetch_redirect_response=False
    )


def test_login_page_is_open(anonymous, db):
    assertContains(anonymous.get(reverse("login")), "Увійти")


def test_login_with_password_redirects_to_list(anonymous, django_user_model):
    django_user_model.objects.create_user("teacher", password="pass-12345")

    response = anonymous.post(
        reverse("login"), {"username": "teacher", "password": "pass-12345"}
    )

    assertRedirects(response, "/students/", fetch_redirect_response=False)


def test_logout_needs_post(client):
    assert client.get(reverse("logout")).status_code == 405

    response = client.post(reverse("logout"))

    assertRedirects(response, reverse("login"), fetch_redirect_response=False)


def test_menu_shows_user_and_logout_button(client, db_group):
    response = client.get("/students/")

    assertContains(response, '<span class="user">viewer</span>', html=True)
    assertContains(response, "Вийти")


def test_post_without_csrf_token_is_403(db_group, django_user_model):
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(
        django_user_model.objects.create_user("x", password="pass-12345")
    )

    assert csrf_client.post(reverse("logout")).status_code == 403


def test_setup_roles_twice_without_errors(db):
    out = io.StringIO()

    call_command("setup_roles", stdout=out)
    call_command("setup_roles", stdout=out)

    assert out.getvalue().count("Ролі налаштовано") == 2
    teachers = Role.objects.get(name="Викладачі")
    assert sorted(teachers.permissions.values_list("codename", flat=True)) == [
        "add_grade",
        "view_grade",
        "view_student",
    ]
    assert Role.objects.count() == 2


def test_user_without_role_gets_403_on_new_grade(client, db_group):
    response = client.get(reverse("students:add-grade", args=[3]))

    assert response.status_code == 403


def test_teacher_sees_new_grade_link_but_not_edit(teacher, db_group):
    response = teacher.get(reverse("students:detail", args=[3]))

    assertContains(response, reverse("students:add-grade", args=[3]))
    assertNotContains(response, reverse("students:edit", args=[3]))


def test_user_without_role_sees_no_links(client, db_group):
    response = client.get(reverse("students:detail", args=[3]))

    assertNotContains(response, "Нова оцінка")
    assertNotContains(response, "Змінити")


def test_teacher_opens_empty_grade_form(teacher, db_group):
    response = teacher.get(reverse("students:add-grade", args=[3]))

    assert response.status_code == 200
    assert not response.context["form"].is_bound
    assertContains(response, 'type="date"')
    assertContains(response, "csrfmiddlewaretoken")


def test_wrong_score_shows_form_again(teacher, db_group):
    before = Grade.objects.count()

    response = teacher.post(
        reverse("students:add-grade", args=[3]),
        {"course": "Git", "score": 101, "graded_on": YESTERDAY},
    )

    assert response.status_code == 200
    assert list(response.context["form"].errors) == ["score"]
    assert Grade.objects.count() == before


def test_valid_grade_redirects_to_card_with_message(teacher, db_group):
    response = teacher.post(
        reverse("students:add-grade", args=[3]),
        {"course": " Git ", "score": 74, "graded_on": YESTERDAY},
    )

    assertRedirects(
        response, reverse("students:detail", args=[3]), fetch_redirect_response=False
    )
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert messages == ["Оцінку 74 з Git збережено"]
    assert Grade.objects.get(student_id=3).course == "Git"


def test_message_is_shown_on_card_after_redirect(teacher, db_group):
    response = teacher.post(
        reverse("students:add-grade", args=[3]),
        {"course": "Git", "score": 74, "graded_on": YESTERDAY},
        follow=True,
    )

    assertContains(
        response, '<p class="message">Оцінку 74 з Git збережено</p>', html=True
    )
    assertContains(response, "<td>D</td>", html=True)


def test_new_grade_for_unknown_student_is_404(teacher, db_group):
    assert teacher.get(reverse("students:add-grade", args=[42])).status_code == 404


def test_dean_creates_and_changes_student(dean, db_group):
    group = Group.objects.get()

    response = dean.post(
        reverse("students:create"),
        {"first_name": "Олег", "last_name": "Новий", "group": group.pk},
    )
    assertRedirects(response, "/students/", fetch_redirect_response=False)
    student = Student.objects.get(last_name="Новий")

    response = dean.post(
        reverse("students:edit", args=[student.pk]),
        {"first_name": "Олег", "last_name": "Змінений", "group": group.pk},
    )
    assertRedirects(
        response,
        reverse("students:detail", args=[student.pk]),
        fetch_redirect_response=False,
    )
    student.refresh_from_db()
    assert student.last_name == "Змінений"


def test_dean_sees_create_and_edit_links(dean, db_group):
    assertContains(dean.get("/students/"), reverse("students:create"))
    assertContains(
        dean.get(reverse("students:detail", args=[1])),
        reverse("students:edit", args=[1]),
    )


def test_edit_form_title_names_student(dean, db_group):
    assertContains(dean.get(reverse("students:edit", args=[1])), "Зміна: Коваль Олена")
    assertContains(dean.get(reverse("students:create")), "Новий студент")


@pytest.mark.parametrize("url", ["/students/new/", "/students/1/edit/"])
def test_teacher_cannot_create_or_change_student(teacher, db_group, url):
    assert teacher.get(url).status_code == 403
