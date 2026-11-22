"""Спільні фікстури тестів."""

import io
import os
from collections.abc import Callable

import pytest
from django.contrib.auth.models import Group as Role
from django.core.management import call_command
from django.test import Client
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import save_group
from students.services import store_group

API_KEY = "test-key-0123456789"
# portal_api.main створює застосунок під час імпорту: тести не залежать від .env
os.environ.setdefault("PORTAL_API_KEY", API_KEY)

from portal_api import orm  # noqa: E402
from portal_api.main import create_app  # noqa: E402
from portal_api.settings import Settings  # noqa: E402

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


def _api_database(path, group: Group | None) -> str:
    """Окрема база SQLite для API: таблиці з моделей SQLAlchemy і, за потреби, група."""
    engine = create_engine(f"sqlite:///{path}")
    orm.Base.metadata.create_all(engine)
    if group is not None:
        with Session(engine) as session, session.begin():
            record = orm.Group(name=group.name)
            session.add(record)
            session.flush()
            for s in group:
                session.add(
                    orm.Student(
                        id=s.id,
                        group_id=record.id,
                        first_name=s.first_name,
                        last_name=s.last_name,
                        grades=[
                            orm.Grade(
                                course=g.course, score=g.score, graded_on=g.graded_on
                            )
                            for g in s.grades
                        ],
                    )
                )
    engine.dispose()
    return f"sqlite+aiosqlite:///{path}"


def _client(database_url: str):
    settings = Settings(database_url=database_url, api_key=API_KEY)
    with TestClient(create_app(settings), headers={"X-API-Key": API_KEY}) as client:
        yield client


@pytest.fixture
def api_db(tmp_path, group) -> str:
    """URL окремої бази даних з тією самою групою з трьох студентів."""
    return _api_database(tmp_path / "api.sqlite3", group)


@pytest.fixture
def api(api_db):
    """Клієнт API з правильним ключем у заголовку X-API-Key."""
    yield from _client(api_db)


@pytest.fixture
def empty_api(tmp_path):
    """Клієнт API з порожньою базою даних."""
    yield from _client(_api_database(tmp_path / "empty.sqlite3", None))
