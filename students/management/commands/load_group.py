from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

from student_portal.exceptions import StorageError
from student_portal.storage import load_group
from students.services import store_group


class Command(BaseCommand):
    help = "Переносить групу з файлу JSON у базу даних; повторний запуск оновлює її."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=Path, help="файл групи у форматі JSON")

    def handle(self, *args: object, **options: object) -> None:
        path = options["path"]
        assert isinstance(path, Path)
        try:
            group = load_group(path)
        except StorageError as error:
            raise CommandError(str(error)) from error

        students, grades = store_group(group)
        self.stdout.write(
            self.style.SUCCESS(
                f"Група {group.name}: студентів - {students}, оцінок - {grades}"
            )
        )
