from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("", views.student_list, name="list"),
    path("ranking/", views.ranking, name="ranking"),
]
