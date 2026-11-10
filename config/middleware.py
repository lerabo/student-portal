"""Проміжні компоненти проєкту: час обробки і недоступне сховище."""

import logging
import time

from django.conf import settings
from django.db import DatabaseError
from django.shortcuts import render

from student_portal.exceptions import StorageError

logger = logging.getLogger(__name__)


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
