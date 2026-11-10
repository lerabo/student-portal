"""Форма нової оцінки: поля, обмеження моделі і перевірка всієї форми."""

from datetime import timedelta

import pytest
from django.utils import timezone

from students.forms import GradeForm

pytestmark = pytest.mark.django_db

YESTERDAY = timezone.localdate() - timedelta(days=1)


def form(**changes):
    data = {"course": "Git", "score": 74, "graded_on": YESTERDAY} | changes
    return GradeForm(data)


def test_valid_data_strips_course():
    grade_form = form(course="  Git  ")

    assert grade_form.is_valid()
    assert grade_form.cleaned_data == {
        "course": "Git",
        "score": 74,
        "graded_on": YESTERDAY,
    }


@pytest.mark.parametrize(
    ("score", "message"),
    [
        pytest.param(
            101, "Переконайтеся, що це значення менше чи дорівнює 100.", id="101"
        ),
        pytest.param(
            -1, "Переконайтеся, що це значення більше чи дорівнює 0.", id="-1"
        ),
        pytest.param("abc", "Введіть ціле число.", id="abc"),
    ],
)
def test_wrong_score_has_exact_message(score, message):
    grade_form = form(score=score)

    assert not grade_form.is_valid()
    assert grade_form.errors == {"score": [message]}


@pytest.mark.parametrize("score", [0, 100])
def test_score_limits_are_valid(score):
    assert form(score=score).is_valid()


def test_future_date_is_rejected_by_form_clean():
    grade_form = form(graded_on=timezone.localdate() + timedelta(days=1))

    assert not grade_form.is_valid()
    assert grade_form.errors == {
        "graded_on": ["Дата оцінки не може бути в майбутньому"]
    }


def test_today_is_valid():
    assert form(graded_on=timezone.localdate()).is_valid()


def test_three_fields_are_required():
    grade_form = GradeForm({})

    assert not grade_form.is_valid()
    assert set(grade_form.errors) == {"course", "score", "graded_on"}
