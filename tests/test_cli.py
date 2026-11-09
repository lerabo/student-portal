import logging

import pytest

from student_portal import cli, notify
from student_portal.cli import run
from student_portal.decorators import timed
from student_portal.grades import Grade


def test_menu_adds_student(group, answers, capsys):
    answers("4", "Марія", "Шевчук", "0")

    run(group)

    assert "Додано: Шевчук Марія (студент)" in capsys.readouterr().out
    assert group.get(4).full_name == "Шевчук Марія"


def test_menu_adds_grade(group, answers, capsys):
    answers("5", "3", "Python", "74", "0")

    run(group)

    assert "Бойко Ірина: 74 (D)" in capsys.readouterr().out
    assert group.get(3).average() == pytest.approx(74)


@pytest.mark.parametrize(
    ("replies", "message"),
    [
        pytest.param(("5", "1", "Python", "сто"), "Помилка введення", id="text-score"),
        pytest.param(("5", "1", "Python", "105"), "Помилка введення", id="score-105"),
        pytest.param(("6", "42"), "Помилка: студента з id=42 немає", id="unknown-id"),
        pytest.param(("99",), "Невідома команда", id="unknown-command"),
    ],
)
def test_menu_survives_bad_input(group, answers, capsys, replies, message):
    answers(*replies, "0")

    run(group)

    assert message in capsys.readouterr().out
    assert len(group) == 3


def test_menu_lists_commands_in_definition_order():
    assert list(cli.COMMANDS)[:3] == ["1", "2", "3"]
    assert cli.COMMANDS["1"][1] is cli.list_students


@pytest.mark.parametrize("key", ["1", "0"], ids=["taken", "exit-key"])
def test_command_rejects_taken_key(monkeypatch, key):
    monkeypatch.setattr(cli, "COMMANDS", {})

    @cli.command("1", "перший пункт")
    def first(group):
        pass

    with pytest.raises(ValueError, match=f"пункт меню {key} уже зайнято"):

        @cli.command(key, "другий пункт")
        def second(group):
            pass

    assert list(cli.COMMANDS) == ["1"]


def test_timed_logs_duration_and_keeps_name(caplog):
    @timed
    def add(a: int, b: int) -> int:
        return a + b

    with caplog.at_level(logging.INFO):
        assert add(2, 3) == 5

    assert add.__name__ == "add"
    assert "add: " in caplog.text
    assert caplog.text.rstrip().endswith("мс")


def test_timed_logs_even_when_function_fails(caplog):
    @timed
    def fail() -> None:
        raise RuntimeError("збій")

    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError):
        fail()

    assert "fail: " in caplog.text


@pytest.mark.parametrize(
    ("replies", "expected"),
    [
        pytest.param(("1",), "Бойко Ірина", id="1-list"),
        pytest.param(("2",), "  1  Коваль Олена", id="2-ranking"),
        pytest.param(("3", "мельн"), "Мельник Андрій", id="3-found"),
        pytest.param(("3", "Шевч"), "Нікого не знайдено", id="3-not-found"),
        pytest.param(("6", "3"), "Видалено: Бойко Ірина", id="6-remove"),
        pytest.param(("7",), "A  █ 1", id="7-ects"),
        pytest.param(("8",), "Боржників немає", id="8-no-debtors"),
        pytest.param(("10",), "Надіслано: Коваль Олена: середній бал 91.5", id="10"),
        pytest.param(("11",), "Надіслано: Бойко Ірина: оцінок немає", id="11"),
    ],
)
def test_menu_command_output(monkeypatch, group, answers, capsys, replies, expected):
    monkeypatch.setattr(notify, "SEND_DELAY", 0)
    answers(*replies, "0")

    run(group)

    assert expected in capsys.readouterr().out


def test_menu_shows_debtors(group, answers, capsys):
    group.get(3).add_grade(Grade("Python", 40))
    answers("8", "0")

    run(group)

    out = capsys.readouterr().out
    assert "Бойко Ірина" in out
    assert "Коваль Олена" not in out


def test_menu_imports_journal(group, answers, capsys, tmp_path):
    journal = tmp_path / "journal.csv"
    journal.write_text(
        "student_id;course;score;graded_on\n3;Git;77;2026-10-20\n", encoding="utf-8"
    )
    answers("9", str(journal), "0")

    run(group)

    assert "Імпортовано оцінок: 1" in capsys.readouterr().out
    assert group.get(3).average() == 77
