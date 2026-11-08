"""Консольний інтерфейс."""

from collections.abc import Iterable
from pathlib import Path

from student_portal.exceptions import PortalError, StorageError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import load_group, save_group

DATA_FILE = Path("data/group.json")

MENU = """
1 - список студентів        5 - додати оцінку
2 - рейтинг                 6 - видалити студента
3 - пошук за прізвищем      7 - розподіл оцінок ECTS
4 - додати студента         8 - список боржників
                            0 - зберегти і вийти"""


def format_average(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def print_students(students: Iterable[Student]) -> None:
    for s in students:
        print(f"{s.id:>3}  {s.full_name:<30} {format_average(s.average()):>6}")


def run(group: Group) -> None:
    while True:
        print(MENU)
        choice = input("> ").strip()
        try:
            match choice:
                case "1":
                    print_students(group)
                case "2":
                    print_students(group.ranking())
                case "3":
                    found = group.find(input("Фрагмент прізвища: ").strip())
                    if found:
                        print_students(found)
                    else:
                        print("Нікого не знайдено")
                case "4":
                    first_name = input("Ім’я: ").strip()
                    last_name = input("Прізвище: ").strip()
                    student = Student(group.next_id(), first_name, last_name)
                    group.add(student)
                    print(f"Додано: {student}")
                case "5":
                    student = group.get(int(input("ID студента: ")))
                    course = input("Дисципліна: ").strip()
                    grade = Grade(course, int(input("Бали (0–100): ")))
                    student.add_grade(grade)
                    print(f"{student.full_name}: {grade.score} ({grade.ects})")
                case "6":
                    student = group.remove(int(input("ID студента: ")))
                    print(f"Видалено: {student}")
                case "7":
                    for letter, count in group.ects_distribution().items():
                        print(f"{letter:<2} {'█' * count} {count}")
                case "8":
                    debtors = group.debtors()
                    if debtors:
                        print_students(debtors)
                    else:
                        print("Боржників немає: усі оцінки не нижче E")
                case "0":
                    return
                case _:
                    print("Невідома команда")
        except ValueError as error:
            print(f"Помилка введення: {error}")
        except PortalError as error:
            print(f"Помилка: {error}")


def main() -> None:
    if DATA_FILE.exists():
        try:
            group = load_group(DATA_FILE)
        except StorageError as error:
            raise SystemExit(f"Не вдалося завантажити дані: {error}") from error
    else:
        group = Group(input("Назва нової групи: ").strip() or "КН-11")
    print(
        f"Група {group.name}: студентів - {len(group)}, "
        f"середній бал - {format_average(group.average())}"
    )
    run(group)
    save_group(group, DATA_FILE)
    print(f"Дані збережено у {DATA_FILE}")
