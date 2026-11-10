"""Проміжні компоненти проєкту: час обробки, недоступне сховище, режим читання."""

import logging
import time

from django.conf import settings
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import render

from student_portal.exceptions import StorageError

logger = logging.getLogger(__name__)

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class TimingMiddleware:
    """Вимірює час обробки запиту: заголовок Server-Timing і журнал повільних."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response["Server-Timing"] = f"app;dur={duration_ms:.1f}"
        if duration_ms > settings.SLOW_REQUEST_MS:
            logger.warning(
                "Повільний запит %s %s: %.1f мс",
                request.method,
                request.path,
                duration_ms,
            )
        return response


class StorageErrorMiddleware:
    """Помилка сховища або бази даних перетворюється на сторінку 503."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, StorageError | DatabaseError):
            logger.error("Сховище недоступне: %s", exception)
            return render(request, "503.html", status=503)
        return None  # інші винятки обробить Django


def read_only_middleware(get_response):
    """Варіант 2: у режимі PORTAL_READ_ONLY запити, що змінюють дані, отримують 503."""

    def middleware(request):
        if settings.PORTAL_READ_ONLY and request.method not in SAFE_METHODS:
            response = HttpResponse(
                "Портал працює лише для читання, спробуйте пізніше.",
                status=503,
                content_type="text/plain; charset=utf-8",
            )
            response["Retry-After"] = "3600"
            return response
        return get_response(request)

    return middleware
