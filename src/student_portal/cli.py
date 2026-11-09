"""Консольний інтерфейс."""

import asyncio
import logging
import os
from collections.abc import Callable, Iterable
from pathlib import Path

from student_portal.decorators import timed
from student_portal.exceptions import PortalError, StorageError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.journal import import_journal
from student_portal.notify import notify_all, notify_in_batches
from student_portal.people import Student
from student_portal.remote import fetch_group
from student_portal.storage import load_group, save_group

DATA_FILE = Path("data/group.json")
DEFAULT_DEKANAT_URL = "https://dekanat.example.edu/api/groups/kn-11"

type Handler = Callable[[Group], None]

COMMANDS: dict[str, tuple[str, Handler]] = {}


def command(key: str, title: str) -> Callable[[Handler], Handler]:
    """Реєструє функцію як пункт меню з номером key."""

    def register(handler: Handler) -> Handler:
        if key in COMMANDS or key == "0":
            raise ValueError(f"пункт меню {key} уже зайнято")
        COMMANDS[key] = (title, handler)
        return handler

    return register


def menu() -> str:
    items = [f"{key:>2} - {title}" for key, (title, _) in COMMANDS.items()]
    return "\n" + "\n".join([*items, " 0 - зберегти і вийти"])


def format_average(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def print_students(students: Iterable[Student]) -> None:
    for s in students:
        print(f"{s.id:>3}  {s.full_name:<30} {format_average(s.average()):>6}")


@command("1", "список студентів")
def list_students(group: Group) -> None:
    print_students(group)


@command("2", "рейтинг")
def show_ranking(group: Group) -> None:
    print_students(group.ranking())


@command("3", "пошук за прізвищем")
def find_students(group: Group) -> None:
    found = group.find(input("Фрагмент прізвища: ").strip())
    if found:
        print_students(found)
    else:
        print("Нікого не знайдено")


@command("4", "додати студента")
def add_student(group: Group) -> None:
    first_name = input("Ім’я: ").strip()
    last_name = input("Прізвище: ").strip()
    student = Student(group.next_id(), first_name, last_name)
    group.add(student)
    print(f"Додано: {student}")


@command("5", "додати оцінку")
def add_grade(group: Group) -> None:
    student = group.get(int(input("ID студента: ")))
    course = input("Дисципліна: ").strip()
    grade = Grade(course, int(input("Бали (0–100): ")))
    student.add_grade(grade)
    print(f"{student.full_name}: {grade.score} ({grade.ects})")


@command("6", "видалити студента")
def remove_student(group: Group) -> None:
    student = group.remove(int(input("ID студента: ")))
    print(f"Видалено: {student}")


@command("7", "розподіл оцінок ECTS")
def show_ects(group: Group) -> None:
    for letter, count in group.ects_distribution().items():
        print(f"{letter:<2} {'█' * count} {count}")


@command("8", "список боржників")
def show_debtors(group: Group) -> None:
    debtors = group.debtors()
    if debtors:
        print_students(debtors)
    else:
        print("Боржників немає: усі оцінки не нижче E")


@command("9", "імпорт оцінок з журналу CSV")
def import_grades(group: Group) -> None:
    path = Path(input("Шлях до журналу: ").strip())
    count = import_journal(group, path)
    print(f"Імпортовано оцінок: {count}")


@command("10", "розіслати результати")
@timed
def send_results(group: Group) -> None:
    for message in asyncio.run(notify_all(group)):
        print(f"Надіслано: {message}")


@command("11", "завантажити групу з сервера деканату")
def download_group(group: Group) -> None:
    url = os.environ.get("DEKANAT_URL", DEFAULT_DEKANAT_URL)
    remote = fetch_group(url)
    print(f"На сервері: група {remote.name}, студентів - {len(remote)}")
    if input("Замінити поточну групу? (т/н) ").strip().lower() == "т":
        group.name, group.students = remote.name, remote.students
        print("Групу замінено")


@command("12", "розіслати результати пакетами")
@timed
def send_results_in_batches(group: Group) -> None:
    for message in asyncio.run(notify_in_batches(group)):
        print(f"Надіслано: {message}")


def run(group: Group) -> None:
    while True:
        print(menu())
        choice = input("> ").strip()
        if choice == "0":
            return
        if choice not in COMMANDS:
            print("Невідома команда")
            continue
        _, handler = COMMANDS[choice]
        try:
            handler(group)
        except ValueError as error:
            print(f"Помилка введення: {error}")
        except PortalError as error:
            print(f"Помилка: {error}")


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "WARNING").upper(),
        format="%(levelname)s %(name)s: %(message)s",
    )
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
