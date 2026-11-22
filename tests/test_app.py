"""Сторінка /app/ з клієнтом Vue і GET /api/me/ з правами користувача."""

import pytest


def test_app_requires_login(anonymous, db):
    response = anonymous.get("/app/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/app/"


def test_app_page_has_client_and_csrf_cookie(client, role_user):
    client.force_login(role_user("teacher", "Викладачі"))

    response = client.get("/app/")

    assert response.status_code == 200
    html = response.content.decode()
    assert '<div id="app"></div>' in html
    assert 'src="/static/frontend/app.js"' in html
    assert 'href="/static/frontend/app.css"' in html
    assert "csrftoken" in response.cookies


def test_menu_links_to_app(client, role_user):
    client.force_login(role_user("teacher", "Викладачі"))

    assert 'href="/app/"' in client.get("/students/").content.decode()


@pytest.mark.parametrize(
    ("role", "permissions"),
    [
        ("Викладачі", ["add_grade", "view_grade", "view_student"]),
        (
            "Деканат",
            ["add_student", "change_student", "delete_student", "view_student"],
        ),
    ],
)
def test_me_returns_username_and_permissions(client, role_user, role, permissions):
    client.force_login(role_user("user", role))

    response = client.get("/api/me/")

    assert response.status_code == 200
    assert response.json() == {"username": "user", "permissions": permissions}


def test_me_requires_login(anonymous, db):
    assert anonymous.get("/api/me/").status_code == 403
