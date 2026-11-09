import pytest

from student_portal.grades import Grade
from student_portal.people import Person, Student, Teacher


def test_full_name_starts_with_last_name():
    student = Student(1, "Олена", "Коваль")

    assert student.full_name == "Коваль Олена"


@pytest.mark.parametrize(
    ("person", "expected"),
    [
        pytest.param(
            Student(1, "Олена", "Коваль"), "Коваль Олена (студент)", id="student"
        ),
        pytest.param(
            Teacher(2, "Ірина", "Шевчук", ["Python"]),
            "Шевчук Ірина (викладач)",
            id="teacher",
        ),
    ],
)
def test_str_contains_role(person, expected):
    assert str(person) == expected


def test_person_is_abstract():
    with pytest.raises(TypeError, match="abstract"):
        Person(1, "Олена", "Коваль")  # type: ignore[abstract]


def test_student_without_grades_has_no_average(make_student):
    student = make_student()

    assert student.average() is None


def test_average_of_grades(make_student):
    student = make_student("Коваль", 95, 88)

    assert student.average() == pytest.approx(91.5)


def test_add_grade_changes_average(make_student):
    student = make_student("Коваль", 90)

    student.add_grade(Grade("Python", 70))

    assert student.average() == pytest.approx(80)


def test_grades_for_returns_only_one_course():
    student = Student(1, "Олена", "Коваль", [Grade("Python", 95), Grade("Git", 88)])

    grades = student.grades_for("Git")

    assert [g.score for g in grades] == [88]


def test_grades_for_unknown_course_is_empty(make_student):
    student = make_student("Коваль", 95)

    assert student.grades_for("Бази даних") == []
