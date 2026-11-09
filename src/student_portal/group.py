"""Академічна група."""

import copy
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from statistics import fmean
from types import TracebackType

from student_portal.exceptions import DuplicateStudentError, StudentNotFoundError
from student_portal.grades import ECTS_LETTERS, Grade
from student_portal.people import Student


@dataclass
class Group:
    """Група студентів, доступних за ідентифікатором."""

    name: str
    students: dict[int, Student] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.students)

    def __iter__(self) -> Iterator[Student]:
        return iter(self.students.values())

    def add(self, student: Student) -> None:
        if student.id in self.students:
            raise DuplicateStudentError(f"студент з id={student.id} уже є в групі")
        self.students[student.id] = student

    def get(self, student_id: int) -> Student:
        try:
            return self.students[student_id]
        except KeyError:
            raise StudentNotFoundError(f"студента з id={student_id} немає") from None

    def remove(self, student_id: int) -> Student:
        student = self.get(student_id)
        del self.students[student_id]
        return student

    def next_id(self) -> int:
        return max(self.students, default=0) + 1

    def find(self, query: str) -> list[Student]:
        needle = query.strip().casefold()
        return [s for s in self if needle in s.last_name.casefold()]

    def ranking(self) -> list[Student]:
        return sorted(
            self,
            key=lambda s: (
                (avg := s.average()) is None,
                -(avg or 0),
                s.last_name,
            ),
        )

    def average(self) -> float | None:
        averages = [avg for s in self if (avg := s.average()) is not None]
        return fmean(averages) if averages else None

    def iter_grades(self) -> Iterator[tuple[Student, Grade]]:
        """Видає пари «студент - оцінка» для всіх оцінок групи."""
        for student in self:
            for grade in student.grades:
                yield student, grade

    def courses(self) -> set[str]:
        return {grade.course for _, grade in self.iter_grades()}

    def ects_distribution(self) -> dict[str, int]:
        counts = Counter(grade.ects for _, grade in self.iter_grades())
        return {letter: counts[letter] for letter in ECTS_LETTERS if counts[letter]}

    def transaction(self) -> Transaction:
        """Повертає контекстний менеджер, що скасовує зміни в разі помилки."""
        return Transaction(self)

    def debtors(self) -> list[Student]:
        """Студенти з хоча б однією оцінкою Fx (варіант 2)."""
        return [s for s in self if s.is_debtor()]


class Transaction:
    """Відновлює студентів групи, якщо блок with завершився винятком."""

    def __init__(self, group: Group) -> None:
        self._group = group
        self._snapshot: dict[int, Student] = {}

    def __enter__(self) -> Group:
        self._snapshot = copy.deepcopy(self._group.students)
        return self._group

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self._group.students = self._snapshot
