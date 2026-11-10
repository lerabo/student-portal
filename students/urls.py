from django.urls import path, re_path, register_converter

from . import converters, views

register_converter(converters.EctsConverter, "ects")

app_name = "students"
urlpatterns = [
    path("", views.student_list, name="list"),
    path("<int:student_id>/", views.student_detail, name="detail"),
    path("<int:student_id>/grades/new/", views.add_grade, name="add-grade"),
    path("<int:student_id>.json", views.student_json, name="detail-json"),
    path("ranking/", views.RankingView.as_view(), name="ranking"),
    path("pages/", views.StudentListView.as_view(), name="pages"),
    path("ects/<ects:letter>/", views.by_ects, name="by-ects"),
    re_path(r"^st/(?P<student_id>[0-9]{4})/$", views.legacy_student),
]
