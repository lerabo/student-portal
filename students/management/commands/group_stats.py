from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

from student_portal.exceptions import StorageError
from student_portal.storage import load_group


def students_word(count: int) -> str:
    """Узгоджує слово «студент» з числом: 1 студент, 3 студенти, 5 студентів."""
    if count % 10 == 1 and count % 100 != 11:
        return "студент"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return "студенти"
    return "студентів"


class Command(BaseCommand):
    help = "Друкує кількість студентів групи і розподіл оцінок за шкалою ECTS."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=Path, help="файл групи у форматі JSON")

    def handle(self, *args: object, **options: object) -> None:
        path = options["path"]
        assert isinstance(path, Path)
        try:
            group = load_group(path)
        except StorageError as error:
            raise CommandError(str(error)) from error

        count = len(group)
        self.stdout.write(f"Група {group.name}: {count} {students_word(count)}")
        self.stdout.write("Розподіл оцінок за шкалою ECTS:")
        for letter, count in group.ects_distribution().items():
            self.stdout.write(f"  {letter}: {count}")
        self.stdout.write(self.style.SUCCESS("Готово"))
