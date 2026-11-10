"""Django-частина: сторінка рейтингу, команди group_stats і debtors, налаштування."""

import io

import pytest
from django.conf import settings as django_settings
from django.core.management import CommandError, call_command
from django.core.management.color import color_style
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from student_portal.grades import Grade
from student_portal.storage import save_group
from students.management.commands.group_stats import students_word


def test_ranking_page_lists_best_student_first(client, data_file):
    response = client.get(reverse("students:ranking"))

    assertTemplateUsed(response, "students/ranking.html")
    assert response.context["group"].name == "КН-11"
    assertContains(response, "<li>Коваль Олена: 91,5</li>", html=True)


def test_ranking_page_shows_student_without_grades_last(client, data_file):
    response = client.get(reverse("students:ranking"))

    assert response.context["ranking"][-1].last_name == "Бойко"
    assertContains(response, "<li>Бойко Ірина: немає оцінок</li>", html=True)


def test_unknown_url_returns_404(client, data_file):
    assert client.get("/no-such-page/").status_code == 404


def test_group_stats_prints_name_and_distribution(data_file, capsys):
    call_command("group_stats", str(data_file))

    out = capsys.readouterr().out
    assert "Група КН-11: 3 студенти" in out
    assert "  A: 1\n  B: 1\n  E: 1\n" in out
    assert out.rstrip().endswith("Готово")


@pytest.mark.parametrize(
    ("count", "word"),
    [
        pytest.param(1, "студент", id="1"),
        pytest.param(3, "студенти", id="3"),
        pytest.param(5, "студентів", id="5"),
        pytest.param(11, "студентів", id="11"),
        pytest.param(12, "студентів", id="12"),
        pytest.param(14, "студентів", id="14"),
        pytest.param(21, "студент", id="21"),
        pytest.param(22, "студенти", id="22"),
    ],
)
def test_students_word_agrees_with_number(count, word):
    assert students_word(count) == word


def test_group_stats_missing_file_raises_command_error(tmp_path):
    with pytest.raises(CommandError, match="не знайдено"):
        call_command("group_stats", str(tmp_path / "nope.json"))


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("LANGUAGE_CODE", "uk", id="language"),
        pytest.param("TIME_ZONE", "Europe/Kyiv", id="time-zone"),
    ],
)
def test_settings_values(name, expected):
    assert getattr(django_settings, name) == expected


def test_students_app_is_installed():
    assert "students" in django_settings.INSTALLED_APPS


def test_data_file_setting_points_to_project_data():
    assert django_settings.STUDENT_PORTAL_DATA == (
        django_settings.BASE_DIR / "data" / "group.json"
    )


@pytest.fixture
def debtors_file(tmp_path, settings, group):
    """Група з трьох студентів, у Бойко - Fx з Python і Git."""
    student = group.get(3)
    for course, score in (("Python", 40), ("Git", 55), ("Бази даних", 70)):
        student.add_grade(Grade(course, score))
    path = tmp_path / "group.json"
    save_group(group, path)
    settings.STUDENT_PORTAL_DATA = path
    return path


def test_debtors_lists_students_and_failed_courses(debtors_file, capsys):
    call_command("debtors")

    out = capsys.readouterr().out
    assert out == "Боржники групи КН-11:\n  Бойко Ірина: Git, Python\n"


@pytest.mark.parametrize(
    ("course", "expected"),
    [
        pytest.param(
            "Python",
            "Боржники групи КН-11 з дисципліни Python:\n  Бойко Ірина: Python\n",
            id="debtor",
        ),
        pytest.param("Бази даних", "Боржників немає\n", id="no-debtors"),
    ],
)
def test_debtors_by_course(debtors_file, capsys, course, expected):
    call_command("debtors", str(debtors_file), course=course)

    assert capsys.readouterr().out == expected


def test_debtors_group_without_fx_prints_success(data_file):
    out = io.StringIO()

    call_command("debtors", stdout=out, force_color=True)

    styled = color_style(force_color=True).SUCCESS("Боржників немає")
    assert out.getvalue() == styled + "\n"


def test_debtors_missing_file_raises_command_error(tmp_path):
    with pytest.raises(CommandError, match="не знайдено"):
        call_command("debtors", str(tmp_path / "nope.json"))
