"""Імпорт оцінок з журналу CSV."""

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from student_portal.exceptions import (
    JournalFormatError,
    StorageError,
)
from student_portal.grades import Grade

FIELDS = ["student_id", "course", "score", "graded_on"]

type Row = tuple[int, dict[str, str]]


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """Оцінка з журналу і номер рядка, з якого її прочитано."""

    line: int
    student_id: int
    grade: Grade


def read_rows(path: Path) -> Iterator[Row]:
    """Видає рядки журналу з їхніми номерами, не читаючи файл повністю."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter=";")
            if reader.fieldnames != FIELDS:
                header = ";".join(FIELDS)
                raise JournalFormatError(f"заголовок має бути: {header}")
            for row in reader:
                yield reader.line_num, row
    except FileNotFoundError as error:
        raise StorageError(f"журнал не знайдено: {path}") from error


def parse_entries(rows: Iterable[Row]) -> Iterator[JournalEntry]:
    """Перетворює рядки журналу на оцінки, зберігаючи номер рядка."""
    for line, row in rows:
        try:
            grade = Grade(
                row["course"].strip(),
                int(row["score"]),
                date.fromisoformat(row["graded_on"]),
            )
            entry = JournalEntry(line, int(row["student_id"]), grade)
        except (AttributeError, TypeError, ValueError) as error:
            raise JournalFormatError(f"рядок {line}: {error}") from error
        yield entry
