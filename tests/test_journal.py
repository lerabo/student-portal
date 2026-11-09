from collections.abc import Callable
from pathlib import Path

import pytest

from student_portal.exceptions import JournalFormatError, StorageError
from student_portal.journal import import_journal, parse_entries, read_rows

HEADER = "student_id;course;score;graded_on"

type JournalWriter = Callable[..., Path]


@pytest.fixture
def write_journal(tmp_path: Path) -> JournalWriter:
    """Фабрика файлів журналу: рядки даних додаються після заголовка."""

    def write(*rows: str, header: str = HEADER, encoding: str = "utf-8") -> Path:
        path = tmp_path / "journal.csv"
        path.write_text("\n".join([header, *rows]) + "\n", encoding=encoding)
        return path

    return write


def grade_counts(group):
    return {s.id: len(s.grades) for s in group}


def test_import_adds_grades_and_returns_count(group, write_journal):
    path = write_journal(
        "1;Вебтехнології;91;2026-10-20",
        "3;  Вебтехнології  ;74;2026-10-20",
    )

    count = import_journal(group, path)

    assert count == 2
    assert [g.score for g in group.get(3).grades] == [74]
    assert group.get(3).grades[0].course == "Вебтехнології"


def test_import_accepts_bom_from_excel(group, write_journal):
    path = write_journal("2;Вебтехнології;67;2026-10-20", encoding="utf-8-sig")

    assert import_journal(group, path) == 1


@pytest.mark.parametrize(
    ("bad_row", "message"),
    [
        pytest.param("3;Python;105;2026-10-20", "від 0 до 100", id="score"),
        pytest.param("3;Python;abc;2026-10-20", "invalid literal", id="text"),
        pytest.param("3;Python;74;20.10.2026", "Invalid isoformat", id="date"),
        pytest.param("3;Python;74", "must be str", id="missing-column"),
        pytest.param("x;Python;74;2026-10-20", "invalid literal", id="id"),
        pytest.param("42;Python;74;2026-10-20", "id=42", id="unknown-id"),
    ],
)
def test_bad_row_is_reported_with_line_number(group, write_journal, bad_row, message):
    path = write_journal("1;Python;90;2026-10-20", bad_row)

    with pytest.raises(JournalFormatError, match=f"^рядок 3: .*{message}"):
        import_journal(group, path)


def test_failed_import_changes_nothing(group, write_journal):
    before = grade_counts(group)
    path = write_journal(
        "1;Python;90;2026-10-20",
        "2;Python;80;2026-10-20",
        "3;Python;105;2026-10-20",
    )

    with pytest.raises(JournalFormatError):
        import_journal(group, path)

    assert grade_counts(group) == before


def test_wrong_header_is_rejected(group, write_journal):
    path = write_journal("1;Python;90;2026-10-20", header="id;course;score;date")

    with pytest.raises(JournalFormatError, match="заголовок"):
        import_journal(group, path)


def test_read_rows_is_lazy(tmp_path):
    rows = read_rows(tmp_path / "missing.csv")

    with pytest.raises(StorageError, match="не знайдено"):
        next(rows)


def test_parse_entries_keeps_file_line_numbers(write_journal):
    path = write_journal(
        "1;Python;90;2026-10-20",
        "2;Python;80;2026-10-20",
        "3;Python;70;2026-10-20",
    )

    lines = [entry.line for entry in parse_entries(read_rows(path))]

    assert lines == [2, 3, 4]
