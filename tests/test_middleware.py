"""Проміжні компоненти: час обробки, сторінка 503, CSP, режим лише для читання."""

import logging

import pytest
from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from pytest_django.asserts import assertContains, assertTemplateUsed

from config.middleware import (
    StorageErrorMiddleware,
    TimingMiddleware,
    read_only_middleware,
)


def ok_view(request):
    return HttpResponse("ok")


def test_timing_adds_server_timing_header(rf: RequestFactory):
    response = TimingMiddleware(ok_view)(rf.get("/students/"))

    assert response["Server-Timing"].startswith("app;dur=")
    assert float(response["Server-Timing"].removeprefix("app;dur=")) >= 0


@override_settings(SLOW_REQUEST_MS=-1)
def test_timing_logs_slow_request(rf, caplog):
    with caplog.at_level(logging.WARNING, logger="config.middleware"):
        TimingMiddleware(ok_view)(rf.get("/students/"))

    assert "Повільний запит GET /students/" in caplog.text


def test_timing_does_not_log_fast_request(rf, caplog):
    with caplog.at_level(logging.WARNING, logger="config.middleware"):
        TimingMiddleware(ok_view)(rf.get("/students/"))

    assert caplog.text == ""


def test_storage_error_middleware_passes_other_exceptions(rf):
    middleware = StorageErrorMiddleware(ok_view)

    assert middleware(rf.get("/")).content == b"ok"
    assert middleware.process_exception(rf.get("/"), ValueError("x")) is None


def test_empty_database_shows_503_page(client, db, caplog):
    response = client.get("/students/")

    assert response.status_code == 503
    assertTemplateUsed(response, "503.html")
    assertContains(response, "Сервіс тимчасово недоступний", status_code=503)
    assert "у базі даних немає групи" in caplog.text


def test_database_error_shows_503_page(client, monkeypatch):
    def broken():
        raise OperationalError("database is locked")

    monkeypatch.setattr("students.views.get_group", broken)

    assert client.get("/students/").status_code == 503


def test_every_page_has_timing_and_csp_headers(client, db_group):
    response = client.get("/students/")

    assert "Server-Timing" in response
    assert response["Content-Security-Policy"] == (
        "default-src 'self'; img-src 'self' data:"
    )


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@override_settings(PORTAL_READ_ONLY=True)
def test_read_only_blocks_changing_methods(rf, method):
    response = read_only_middleware(ok_view)(getattr(rf, method)("/students/"))

    assert response.status_code == 503
    assert response["Retry-After"] == "3600"
    assert "лише для читання" in response.content.decode()


@pytest.mark.parametrize("method", ["get", "head", "options"])
@override_settings(PORTAL_READ_ONLY=True)
def test_read_only_lets_safe_methods_through(rf, method):
    response = read_only_middleware(ok_view)(getattr(rf, method)("/students/"))

    assert response.status_code == 200


@override_settings(PORTAL_READ_ONLY=False)
def test_without_read_only_post_passes(rf):
    assert read_only_middleware(ok_view)(rf.post("/students/")).status_code == 200


@override_settings(PORTAL_READ_ONLY=True)
def test_read_only_answers_before_csrf_check(client):
    response = client.post("/students/ranking/")

    assert response.status_code == 503
    assert response["Retry-After"] == "3600"
