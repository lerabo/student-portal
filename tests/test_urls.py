"""Маршрути: конвертер ECTS, сторінка за літерою, перенаправлення."""

import pytest
from django.urls import NoReverseMatch, resolve, reverse
from pytest_django.asserts import assertContains, assertNotContains

from students import views
from students.converters import EctsConverter


def test_resolve_ects_page_gives_view_and_letter():
    match = resolve("/students/ects/Fx/")

    assert match.func is views.by_ects
    assert match.kwargs == {"letter": "Fx"}
    assert match.view_name == "students:by-ects"


@pytest.mark.parametrize("letter", ["A", "B", "C", "D", "E", "Fx"])
def test_reverse_builds_url_for_every_letter(letter):
    assert reverse("students:by-ects", args=[letter]) == f"/students/ects/{letter}/"


@pytest.mark.parametrize("path", ["/students/ects/F/", "/students/ects/a/"])
def test_not_a_letter_is_404(client, path):
    assert client.get(path).status_code == 404


def test_reverse_with_wrong_letter_raises():
    with pytest.raises(NoReverseMatch):
        reverse("students:by-ects", args=["F"])


def test_converter_to_url_rejects_unknown_letter():
    with pytest.raises(ValueError, match="не є літерою"):
        EctsConverter().to_url("F")


def test_ects_page_shows_only_students_with_letter(client, db_group):
    response = client.get(reverse("students:by-ects", args=["A"]))

    assert [s.last_name for s in response.context["students"]] == ["Коваль"]
    assertContains(response, "Середній бал за шкалою ECTS: A")
    assertContains(response, '<a href="/students/1/">Коваль Олена</a>', html=True)
    assertNotContains(response, "Мельник")


def test_ects_page_without_students(client, db_group):
    response = client.get(reverse("students:by-ects", args=["Fx"]))

    assertContains(response, "Таких студентів немає")


def test_legacy_address_redirects_permanently(client):
    response = client.get("/students/st/0003/")

    assert response.status_code == 301
    assert response["Location"] == "/students/3/"


def test_legacy_address_needs_four_digits(client):
    assert client.get("/students/st/3/").status_code == 404


def test_site_root_redirects_to_list(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == reverse("students:list")


def test_detail_links_to_letter_page(client, db_group):
    response = client.get(reverse("students:detail", args=[2]))

    assertContains(response, 'href="/students/ects/E/"')


def test_detail_without_grades_has_no_letter_link(client, db_group):
    response = client.get(reverse("students:detail", args=[3]))

    assertNotContains(response, "/students/ects/")
