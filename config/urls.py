"""Маршрути проєкту: сторінки, вхід, адмінпанель і REST API."""

from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView, TemplateView
from rest_framework.routers import DefaultRouter

from students import api

router = DefaultRouter()
router.register("students", api.StudentViewSet, basename="student")
router.register("grades", api.GradeViewSet, basename="grade")

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="students:list"), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("students/", include("students.urls")),
    path("api/me/", api.me, name="api-me"),
    path("api/", include(router.urls)),
    # Клієнт Vue (ЛР 11): зібрані файли - у frontend/dist, cookie csrftoken - для fetch
    path(
        "app/",
        ensure_csrf_cookie(TemplateView.as_view(template_name="app.html")),
        name="app",
    ),
]
