"""Тести асинхронного API на FastAPI (portal_api)."""

from datetime import date, timedelta

import pytest
from django.apps import apps
from fastapi.testclient import TestClient
from pydantic import ValidationError

from portal_api import orm
from portal_api.main import create_app
from portal_api.settings import Settings

API_KEY = "test-key-0123456789"  # той самий ключ, що у фікстурі api

TODAY = date.today().isoformat()


def test_orm_matches_django():
    """Моделі SQLAlchemy описують ті самі таблиці й стовпці, що й моделі Django."""
    for model in (orm.Group, orm.Student, orm.Grade):
        table = model.__table__
        django_model = next(
            m
            for m in apps.get_app_config("students").get_models()
            if m._meta.db_table == table.name
        )
        django_columns = {f.column for f in django_model._meta.concrete_fields}
        assert set(table.columns.keys()) == django_columns


# --- ключ API і документація ---


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong-key-0123456789"}])
def test_requires_api_key(api, headers):
    api.headers.clear()
    response = api.get("/students", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Неправильний ключ API"}


def test_docs_are_open(api):
    api.headers.clear()
    assert api.get("/docs").status_code == 200
    schema = api.get("/openapi.json").json()
    assert set(schema["paths"]) == {
        "/students",
        "/students/{student_id}",
        "/students/{student_id}/grades",
        "/ranking",
        "/stats/ects",
    }
    scheme = schema["components"]["securitySchemes"]["APIKeyHeader"]
    assert scheme == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Ключ з PORTAL_API_KEY",
    }


# --- читання студентів ---


def test_students_list(api):
    data = api.get("/students").json()
    assert data["count"] == 3
    assert [s["last_name"] for s in data["items"]] == ["Коваль", "Мельник", "Бойко"]
    first = data["items"][0]
    assert first["average"] == 91.5
    assert [g["ects"] for g in first["grades"]] == ["A", "B"]
    assert data["items"][2]["average"] is None
    assert data["items"][2]["grades"] == []


@pytest.mark.parametrize(
    ("query", "ids"),
    [("limit=2", [1, 2]), ("limit=2&offset=2", [3]), ("offset=5", [])],
)
def test_students_pagination(api, query, ids):
    data = api.get(f"/students?{query}").json()
    assert data["count"] == 3
    assert [s["id"] for s in data["items"]] == ids


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("limit=0", "limit"),
        ("limit=101", "limit"),
        ("limit=abc", "limit"),
        ("offset=-1", "offset"),
    ],
)
def test_students_bad_query(api, query, field):
    response = api.get(f"/students?{query}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", field]


def test_student_card(api):
    data = api.get("/students/2").json()
    assert data["first_name"] == "Андрій"
    assert data["average"] == 61
    assert data["grades"][0]["ects"] == "E"


def test_student_not_found(api):
    response = api.get("/students/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Студента з id=999 немає"}


def test_student_id_must_be_int(api):
    response = api.get("/students/abc")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "student_id"]


# --- нова оцінка ---


def test_add_grade(api):
    payload = {"course": "  Git  ", "score": 74, "graded_on": TODAY}
    response = api.post("/students/2/grades", json=payload)
    assert response.status_code == 201
    grade = response.json()
    assert grade["course"] == "Git"
    assert grade["student_id"] == 2
    assert grade["ects"] == "D"
    assert api.get("/students/2").json()["average"] == 67.5


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"score": 101}, "score"),
        ({"score": -1}, "score"),
        ({"score": "abc"}, "score"),
        ({"course": "   "}, "course"),
        ({"course": "x" * 101}, "course"),
        ({"graded_on": (date.today() + timedelta(days=1)).isoformat()}, "graded_on"),
        ({"graded_on": "20.11.2026"}, "graded_on"),
    ],
)
def test_add_grade_invalid(api, change, field):
    payload = {"course": "Git", "score": 74, "graded_on": TODAY} | change
    response = api.post("/students/2/grades", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]
    assert api.get("/students/2").json()["grades"][-1]["course"] == "Python"


def test_add_grade_future_message(api):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {"course": "Git", "score": 74, "graded_on": tomorrow}
    detail = api.post("/students/2/grades", json=payload).json()["detail"]
    assert "дата оцінки не може бути в майбутньому" in detail[0]["msg"]


def test_add_grade_missing_fields(api):
    response = api.post("/students/2/grades", json={"course": "Git"})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert [(e["type"], e["loc"]) for e in errors] == [
        ("missing", ["body", "score"]),
        ("missing", ["body", "graded_on"]),
    ]


def test_add_grade_unknown_student(api):
    payload = {"course": "Git", "score": 74, "graded_on": TODAY}
    response = api.post("/students/999/grades", json=payload)
    assert response.status_code == 404


# --- рейтинг і статистика ---


def test_ranking(api):
    data = api.get("/ranking").json()
    assert data == [
        {"place": 1, "id": 1, "full_name": "Коваль Олена", "average": 91.5},
        {"place": 2, "id": 2, "full_name": "Мельник Андрій", "average": 61.0},
        {"place": 3, "id": 3, "full_name": "Бойко Ірина", "average": None},
    ]


def test_ranking_limit(api):
    assert [r["id"] for r in api.get("/ranking?limit=1").json()] == [1]


def test_ects_stats(api):
    """Варіант 2: розподіл оцінок за літерами ECTS з ядра."""
    assert api.get("/stats/ects").json() == {"A": 1, "B": 1, "E": 1}
    api.post(
        "/students/3/grades", json={"course": "Git", "score": 97, "graded_on": TODAY}
    )
    assert api.get("/stats/ects").json() == {"A": 2, "B": 1, "E": 1}


def test_ects_stats_empty(empty_api):
    assert empty_api.get("/stats/ects").json() == {}


# --- налаштування ---


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("PORTAL_API_KEY", API_KEY)
    monkeypatch.setenv("PORTAL_DATABASE_URL", "sqlite+aiosqlite:///other.sqlite3")
    monkeypatch.setenv("PORTAL_ECHO_SQL", "1")
    settings = Settings(_env_file=None)
    assert settings.api_key.get_secret_value() == API_KEY
    assert settings.database_url == "sqlite+aiosqlite:///other.sqlite3"
    assert settings.echo_sql is True
    assert API_KEY not in repr(settings)


@pytest.mark.parametrize("key", [None, "", "short-key"])
def test_settings_bad_key(monkeypatch, key):
    if key is None:
        monkeypatch.delenv("PORTAL_API_KEY", raising=False)
    else:
        monkeypatch.setenv("PORTAL_API_KEY", key)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_create_app_reads_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PORTAL_API_KEY", "env-key-0123456789")
    app = create_app()
    assert app.state.settings.api_key.get_secret_value() == "env-key-0123456789"
    with TestClient(app) as client:
        assert client.get("/students").status_code == 401
