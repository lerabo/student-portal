"""Моделі SQLAlchemy для таблиць, які створюють міграції Django.

Схемою бази даних володіє Django: тут лише опис наявних таблиць, без міграцій.
"""

from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from student_portal import grades, people


class Base(DeclarativeBase):
    pass


class Group(Base):
    __tablename__ = "students_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)


class Grade(Base):
    __tablename__ = "students_grade"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students_student.id"))
    course: Mapped[str] = mapped_column(String(100))
    score: Mapped[int]
    graded_on: Mapped[date]


class Student(Base):
    __tablename__ = "students_student"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("students_group.id"))
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))

    # lazy="raise": неявне завантаження в асинхронному коді - помилка, а не
    # прихований запит; зв'язки завантажуються явно через selectinload.
    group: Mapped[Group] = relationship(lazy="raise")
    grades: Mapped[list[Grade]] = relationship(
        lazy="raise", order_by=lambda: (Grade.graded_on, Grade.id)
    )


def to_core(student: Student) -> people.Student:
    """Студент бази даних як об'єкт ядра: рейтинг і ECTS лишаються в ядрі."""
    return people.Student(
        student.id,
        student.first_name,
        student.last_name,
        [grades.Grade(g.course, g.score, g.graded_on) for g in student.grades],
    )
