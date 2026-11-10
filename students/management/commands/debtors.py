from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from student_portal.exceptions import StorageError
from student_portal.storage import load_group


class Command(BaseCommand):
    help = "Друкує боржників групи (оцінки Fx) і дисципліни, з яких заборгованість."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            help="файл групи у форматі JSON (за замовчуванням STUDENT_PORTAL_DATA)",
        )
        parser.add_argument("--course", help="лише боржники з цієї дисципліни")

    def handle(self, *args: object, **options: object) -> None:
        path = options["path"] or settings.STUDENT_PORTAL_DATA
        course = options["course"]
        assert isinstance(path, Path)
        assert course is None or isinstance(course, str)
        try:
            group = load_group(path)
        except StorageError as error:
            raise CommandError(str(error)) from error

        debtors = group.debtors(course)
        if not debtors:
            self.stdout.write(self.style.SUCCESS("Боржників немає"))
            return
        scope = f" з дисципліни {course}" if course else ""
        self.stdout.write(f"Боржники групи {group.name}{scope}:")
        for student in debtors:
            courses = [course] if course else student.failed_courses()
            self.stdout.write(f"  {student.full_name}: {', '.join(courses)}")
