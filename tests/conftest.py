"""Спільні фікстури тестів."""

import io
from collections.abc import Callable

import pytest
from django.contrib.auth.models import Group as Role
from django.core.management import call_command
from django.test import Client

from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import save_group
from students.services import store_group

type StudentFactory = Callable[..., Student]


@pytest.fixture
def group() -> Group:
    """Група з трьох студентів: відмінниця, студент з оцінкою E і без оцінок."""
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95), Grade("Git", 88)]))
    group.add(Student(2, "Андрій", "Мельник", [Grade("Python", 61)]))
    group.add(Student(3, "Ірина", "Бойко"))
    return group


@pytest.fixture
def make_student() -> StudentFactory:
    """Фабрика студентів з оцінками з Python і унікальними ідентифікаторами."""
    next_id = 100

    def make(last_name: str = "Тестовий", *scores: int) -> Student:
        nonlocal next_id
        next_id += 1
        grades = [Grade("Python", score) for score in scores]
        return Student(next_id, "Студент", last_name, grades)

    return make


@pytest.fixture
def answers(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Підміняє input(): кожен виклик повертає наступну відповідь зі списку."""

    def set_answers(*values: str) -> None:
        replies = iter(values)
        monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    return set_answers


@pytest.fixture
def data_file(tmp_path, settings, group):
    """Файл групи з трьох студентів замість data/group.json."""
    path = tmp_path / "group.json"
    save_group(group, path)
    settings.STUDENT_PORTAL_DATA = path
    return path


@pytest.fixture
def db_group(db, group):
    """Та сама група з трьох студентів, збережена в тестовій базі даних."""
    store_group(group)
    return group


@pytest.fixture
def client(client, django_user_model):
    """Тестовий клієнт Django від імені користувача, що увійшов (без особливих прав)."""
    user = django_user_model.objects.create_user("viewer", password="pass-12345")
    client.force_login(user)
    return client


@pytest.fixture
def anonymous():
    """Клієнт без входу: для перевірки LoginRequiredMiddleware."""
    return Client()


@pytest.fixture
def role_user(db, django_user_model):
    """Фабрика користувачів у групі-ролі; ролі створює команда setup_roles."""

    def make(username, role):
        call_command("setup_roles", stdout=io.StringIO())
        user = django_user_model.objects.create_user(username, password="pass-12345")
        user.groups.add(Role.objects.get(name=role))
        return user

    return make
