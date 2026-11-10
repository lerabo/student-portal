import inspect

import pytest

from student_portal.exceptions import (
    DuplicateStudentError,
    InvalidGradeError,
    StudentNotFoundError,
)
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


def test_len_counts_students(group):
    assert len(group) == 3


def test_iter_keeps_insertion_order(group):
    assert [s.id for s in group] == [1, 2, 3]


def test_add_rejects_duplicate_id(group):
    duplicate = Student(1, "Інша", "Студентка")

    with pytest.raises(DuplicateStudentError, match="id=1"):
        group.add(duplicate)

    assert len(group) == 3
    assert group.get(1).last_name == "Коваль"


def test_get_returns_student_by_id(group):
    assert group.get(2).full_name == "Мельник Андрій"


@pytest.mark.parametrize("method", ["get", "remove"])
def test_unknown_id_raises_not_found(group, method):
    with pytest.raises(StudentNotFoundError, match="id=42"):
        getattr(group, method)(42)


def test_remove_returns_removed_student(group):
    removed = group.remove(2)

    assert removed.last_name == "Мельник"
    assert [s.id for s in group] == [1, 3]


@pytest.mark.parametrize(
    ("ids", "expected"),
    [
        pytest.param([], 1, id="empty"),
        pytest.param([1, 2, 3], 4, id="sequential"),
        pytest.param([1, 7], 8, id="gap"),
    ],
)
def test_next_id(ids, expected):
    group = Group("КН-11")
    for student_id in ids:
        group.add(Student(student_id, "Студент", f"Прізвище{student_id}"))

    assert group.next_id() == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param("Коваль", ["Коваль"], id="exact"),
        pytest.param("коваль", ["Коваль"], id="lowercase"),
        pytest.param("  Мельник ", ["Мельник"], id="spaces"),
        pytest.param("ко", ["Коваль", "Бойко"], id="substring"),
        pytest.param("Шевчук", [], id="not-found"),
    ],
)
def test_find_by_last_name(group, query, expected):
    assert [s.last_name for s in group.find(query)] == expected


def test_ranking_puts_best_first_and_ungraded_last(group):
    assert [s.id for s in group.ranking()] == [1, 2, 3]


def test_ranking_breaks_ties_by_last_name(make_student):
    group = Group("КН-11")
    for student in (
        make_student("Шевчук", 80),
        make_student("Андрієнко", 80),
        make_student("Бондар"),
        make_student("Коваль", 90),
    ):
        group.add(student)

    ranking = [s.last_name for s in group.ranking()]

    assert ranking == ["Коваль", "Андрієнко", "Шевчук", "Бондар"]


def test_average_skips_students_without_grades(group):
    assert group.average() == pytest.approx((91.5 + 61) / 2)


def test_average_of_empty_group_is_none():
    assert Group("КН-11").average() is None


def test_iter_grades_is_generator(group):
    assert inspect.isgenerator(group.iter_grades())


def test_iter_grades_yields_pairs_in_order(group):
    pairs = [(s.id, g.course, g.score) for s, g in group.iter_grades()]

    assert pairs == [(1, "Python", 95), (1, "Git", 88), (2, "Python", 61)]


def test_courses(group):
    assert group.courses() == {"Python", "Git"}


def test_ects_distribution_in_scale_order(group):
    distribution = group.ects_distribution()

    assert distribution == {"A": 1, "B": 1, "E": 1}
    assert list(distribution) == ["A", "B", "E"]


def test_ects_distribution_of_empty_group():
    assert Group("КН-11").ects_distribution() == {}


def test_add_grade_through_group(group):
    group.get(3).add_grade(Grade("Python", 74))

    assert group.average() == pytest.approx((91.5 + 61 + 74) / 3)


def test_transaction_keeps_changes_without_error(group):
    with group.transaction():
        group.remove(2)
        group.get(3).add_grade(Grade("Python", 70))

    assert [s.id for s in group] == [1, 3]
    assert group.get(3).average() == pytest.approx(70)


def test_transaction_restores_group_after_error(group):
    before = [(s.id, s.average()) for s in group]

    with pytest.raises(InvalidGradeError), group.transaction():
        group.remove(2)
        group.get(3).add_grade(Grade("Python", 70))
        group.get(1).add_grade(Grade("Python", 105))

    assert [(s.id, s.average()) for s in group] == before


@pytest.mark.parametrize(
    ("score", "is_debtor"),
    [
        pytest.param(59, True, id="59-fx"),
        pytest.param(60, False, id="60-e"),
        pytest.param(0, True, id="zero"),
    ],
)
def test_debtor_boundary(make_student, score, is_debtor):
    student = make_student("Коваль", 90, score)

    assert student.is_debtor() is is_debtor


def test_student_without_grades_is_not_debtor(make_student):
    assert make_student("Бойко").is_debtor() is False


def test_debtors_lists_each_student_once_in_group_order(make_student):
    group = Group("КН-11")
    for student in (
        make_student("Коваль", 95),
        make_student("Мельник", 30, 45, 50),
        make_student("Бойко"),
        make_student("Шевчук", 59, 90),
    ):
        group.add(student)

    assert [s.last_name for s in group.debtors()] == ["Мельник", "Шевчук"]


def test_group_without_debtors(group):
    assert group.debtors() == []


def test_failed_courses_sorted_and_unique():
    student = Student(
        1,
        "Максим",
        "Бондар",
        [
            Grade("Python", 45),
            Grade("Бази даних", 30),
            Grade("Python", 20),
            Grade("Git", 90),
        ],
    )

    assert student.failed_courses() == ["Python", "Бази даних"]


def test_debtors_by_course():
    group = Group("КН-11")
    group.add(Student(1, "Максим", "Бондар", [Grade("Python", 45)]))
    group.add(Student(2, "Ірина", "Шевчук", [Grade("Бази даних", 50)]))
    group.add(Student(3, "Олена", "Коваль", [Grade("Python", 95)]))

    assert [s.last_name for s in group.debtors("Python")] == ["Бондар"]
    assert [s.last_name for s in group.debtors("Бази даних")] == ["Шевчук"]
    assert group.debtors("Git") == []
