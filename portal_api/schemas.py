"""Схеми Pydantic: що API приймає і що повертає."""

from datetime import date
from statistics import fmean
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
)

from student_portal.grades import MAX_SCORE, MIN_SCORE, ects_grade


def not_in_future(value: date) -> date:
    if value > date.today():
        raise ValueError("дата оцінки не може бути в майбутньому")
    return value


class GradeIn(BaseModel):
    """Нова оцінка від іншої системи."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {"course": "Python", "score": 92, "graded_on": "2026-11-20"},
            ]
        },
    )

    course: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=MIN_SCORE, le=MAX_SCORE)
    graded_on: Annotated[date, AfterValidator(not_in_future)]


class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course: str
    score: int
    graded_on: date

    @computed_field
    @property
    def ects(self) -> str:
        return ects_grade(self.score)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    grades: list[GradeOut]

    @computed_field
    @property
    def average(self) -> float | None:
        return fmean(g.score for g in self.grades) if self.grades else None


class StudentPage(BaseModel):
    count: int
    items: list[StudentOut]


class RankingItem(BaseModel):
    place: int
    id: int
    full_name: str
    average: float | None
