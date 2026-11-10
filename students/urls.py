from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("", views.student_list, name="list"),
    path("<int:student_id>/", views.student_detail, name="detail"),
    path("<int:student_id>.json", views.student_json, name="detail-json"),
    path("ranking/", views.ranking, name="ranking"),
]
