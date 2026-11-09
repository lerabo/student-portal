import json

import pytest

from student_portal import cli
from student_portal.cli import main
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import load_group, save_group

URL = "http://127.0.0.1:8001/group.json"


@pytest.fixture
def data_file(monkeypatch, tmp_path):
    """Підміняє файл даних застосунку тимчасовим."""
    path = tmp_path / "group.json"
    monkeypatch.setattr(cli, "DATA_FILE", path)
    return path


def test_main_loads_group_and_saves_changes(data_file, group, answers, capsys):
    save_group(group, data_file)
    answers("4", "Марія", "Шевчук", "0")

    main()

    out = capsys.readouterr().out
    assert "Група КН-11: студентів - 3, середній бал - 76.2" in out
    assert f"Дані збережено у {data_file}" in out
    assert load_group(data_file).get(4).full_name == "Шевчук Марія"


def test_main_creates_new_group_when_file_missing(data_file, answers, capsys):
    answers("КН-12", "0")

    main()

    assert "Група КН-12: студентів - 0, середній бал - -" in capsys.readouterr().out
    assert load_group(data_file).name == "КН-12"


def test_main_exits_on_broken_file(data_file):
    data_file.write_text("{не json", encoding="utf-8")

    with pytest.raises(SystemExit, match="Не вдалося завантажити дані"):
        main()

    assert data_file.read_text(encoding="utf-8") == "{не json"


@pytest.fixture
def server_group():
    remote = Group("КН-21")
    remote.add(Student(1, "Тарас", "Гнатюк"))
    return remote


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [pytest.param("т", "КН-21", id="replace"), pytest.param("н", "КН-11", id="keep")],
)
def test_download_group_from_dekanat(
    mocker, monkeypatch, data_file, group, server_group, answers, reply, expected_name
):
    save_group(group, data_file)
    monkeypatch.setenv("DEKANAT_URL", URL)
    fetch = mocker.patch(
        "student_portal.cli.fetch_group", autospec=True, return_value=server_group
    )
    answers("11", reply, "0")

    main()

    fetch.assert_called_once_with(URL)
    saved = json.loads(data_file.read_text(encoding="utf-8"))
    assert saved["name"] == expected_name


def test_download_group_uses_default_url(mocker, monkeypatch, group, answers):
    monkeypatch.delenv("DEKANAT_URL", raising=False)
    fetch = mocker.patch(
        "student_portal.cli.fetch_group", autospec=True, return_value=group
    )
    answers("11", "н", "0")

    cli.run(group)

    fetch.assert_called_once_with(cli.DEFAULT_DEKANAT_URL)
