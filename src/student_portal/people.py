"""Учасники навчального процесу."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics import fmean

from student_portal.grades import Grade


@dataclass
class Person(ABC):
    """Абстрактна особа: спільні дані студента і викладача."""

    id: int
    first_name: str
    last_name: str

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

    @property
    @abstractmethod
    def role(self) -> str:
        """Назва ролі в системі."""

    def __str__(self) -> str:
        return f"{self.full_name} ({self.role})"


@dataclass
class Student(Person):
    """Студент зі списком оцінок."""

    grades: list[Grade] = field(default_factory=list)

    @property
    def role(self) -> str:
        return "студент"

    def add_grade(self, grade: Grade) -> None:
        self.grades.append(grade)

    def grades_for(self, course: str) -> list[Grade]:
        return [g for g in self.grades if g.course == course]

    def average(self) -> float | None:
        return fmean(g.score for g in self.grades) if self.grades else None

    def is_debtor(self) -> bool:
        """Чи має студент хоча б одну оцінку Fx (варіант 2)."""
        return any(g.ects == "Fx" for g in self.grades)

    def failed_courses(self) -> list[str]:
        """Дисципліни з оцінкою Fx за абеткою, кожна один раз (варіант 2)."""
        return sorted({g.course for g in self.grades if g.ects == "Fx"})


@dataclass
class Teacher(Person):
    """Викладач зі списком дисциплін."""

    courses: list[str] = field(default_factory=list)

    @property
    def role(self) -> str:
        return "викладач"
