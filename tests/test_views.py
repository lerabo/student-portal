"""Представлення і шаблони застосунку students."""

from datetime import date

import pytest
from django.template.loader import render_to_string
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertTemplateUsed,
)

from student_portal.grades import Grade
from student_portal.people import Student
from student_portal.storage import save_group
from students.templatetags.grades import ects


def test_list_shows_students_in_group_order(client, data_file):
    response = client.get(reverse("students:list"))

    assertTemplateUsed(response, "students/student_list.html")
    assertTemplateUsed(response, "base.html")
    assert [s.last_name for s in response.context["students"]] == [
        "Коваль",
        "Мельник",
        "Бойко",
    ]
    assertContains(response, "Усього: 3")


def test_search_uses_query_string(client, data_file):
    response = client.get(reverse("students:list"), {"q": "кова"})

    assert [s.last_name for s in response.context["students"]] == ["Коваль"]
    assertContains(response, 'value="кова"')


def test_search_without_results_shows_query(client, data_file):
    response = client.get(reverse("students:list"), {"q": "zzz"})

    assert response.context["students"] == []
    assertContains(response, "Нікого не знайдено за запитом «zzz»")
    assertContains(response, "Усього: 0")


def test_detail_shows_grades_and_average(client, data_file):
    response = client.get(reverse("students:detail", args=[1]))

    assertTemplateUsed(response, "students/student_detail.html")
    assertContains(response, "<td>B</td>", html=True)
    assertContains(response, "Середній бал: 91,5 A")


def test_detail_of_student_without_grades(client, data_file):
    response = client.get(reverse("students:detail", args=[3]))

    assertContains(response, "Оцінок ще немає")
    assertContains(response, "Середній бал: -")


def test_detail_formats_date_in_ukrainian(client, tmp_path, settings, group):
    group.get(2).grades[0] = Grade("Python", 61, date(2026, 10, 1))
    settings.STUDENT_PORTAL_DATA = tmp_path / "group.json"
    save_group(group, settings.STUDENT_PORTAL_DATA)

    response = client.get(reverse("students:detail", args=[2]))

    assertContains(response, "01 жовтня 2026")


def test_unknown_student_is_404(client, data_file):
    assert client.get(reverse("students:detail", args=[42])).status_code == 404


def test_detail_json(client, data_file):
    response = client.get(reverse("students:detail-json", args=[1]))

    assert response.json() == {"id": 1, "full_name": "Коваль Олена", "average": 91.5}
    assert "Коваль" in response.content.decode()


def test_detail_json_of_unknown_student_is_404(client, data_file):
    assert client.get(reverse("students:detail-json", args=[42])).status_code == 404


def test_ranking_includes_student_line_for_each_student(client, data_file):
    response = client.get(reverse("students:ranking"))

    assertTemplateUsed(response, "students/_student_line.html", count=3)
    assertContains(response, "<li>Бойко Ірина: немає оцінок</li>", html=True)


def test_post_to_ranking_is_405(client, data_file):
    assert client.post(reverse("students:ranking")).status_code == 405


@pytest.mark.parametrize(
    ("page", "first"),
    [pytest.param(1, "Коваль", id="page-1"), pytest.param(2, "Бойко", id="page-2")],
)
def test_pages_paginate_by_two(client, data_file, page, first):
    response = client.get(reverse("students:pages"), {"page": page})

    assert response.context["page_obj"].number == page
    assert response.context["students"][0].last_name == first


def test_missing_page_is_404(client, data_file):
    assert client.get(reverse("students:pages"), {"page": 9}).status_code == 404


@pytest.mark.parametrize(
    "name", ["students:list", "students:ranking", "students:pages"]
)
def test_pages_link_stylesheet(client, data_file, name):
    assertContains(
        response=client.get(reverse(name)), text="/static/students/style.css"
    )


def test_student_row_partial_renders_alone(group):
    html = render_to_string(
        "students/student_list.html#student-row", {"student": group.get(3)}
    )

    assert '<a href="/students/3/">Бойко Ірина</a>' in html
    assert "<td>-</td>" in html


def test_names_are_escaped(client, tmp_path, settings, group):
    group.add(Student(4, "Марко", "<script>alert(1)</script>"))
    settings.STUDENT_PORTAL_DATA = tmp_path / "group.json"
    save_group(group, settings.STUDENT_PORTAL_DATA)

    response = client.get(reverse("students:list"))

    assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt; Марко")
    assertNotContains(response, "<script>")


@pytest.mark.parametrize(
    ("score", "letter"),
    [
        pytest.param(95, "A", id="95"),
        pytest.param(89.9, "B", id="89.9"),
        pytest.param(60, "E", id="60"),
        pytest.param(59.5, "Fx", id="59.5"),
        pytest.param(None, "", id="none"),
    ],
)
def test_ects_filter(score, letter):
    assert ects(score) == letter
