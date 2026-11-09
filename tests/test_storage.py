import json

import pytest

from student_portal.exceptions import StorageError
from student_portal.storage import atomic_write, load_group, save_group


def test_save_and_load_return_equal_group(group, tmp_path):
    path = tmp_path / "nested" / "group.json"

    save_group(group, path)

    assert load_group(path) == group


def test_saved_file_keeps_cyrillic(group, tmp_path):
    path = tmp_path / "group.json"

    save_group(group, path)

    text = path.read_text(encoding="utf-8")
    assert "Коваль" in text
    assert "\\u" not in text


def test_load_missing_file_raises_storage_error(tmp_path):
    with pytest.raises(StorageError, match="не знайдено"):
        load_group(tmp_path / "missing.json")


VALID_STUDENT = {
    "id": 1,
    "first_name": "Олена",
    "last_name": "Коваль",
    "grades": [{"course": "Python", "score": 95, "graded_on": "2026-10-01"}],
}


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("{не json", id="invalid-json"),
        pytest.param(json.dumps({"name": "КН-11"}), id="no-students"),
        pytest.param(
            json.dumps(
                {
                    "name": "КН-11",
                    "students": [
                        {
                            **VALID_STUDENT,
                            "grades": [
                                {
                                    "course": "Python",
                                    "score": 105,
                                    "graded_on": "2026-10-01",
                                }
                            ],
                        }
                    ],
                }
            ),
            id="score-105",
        ),
        pytest.param(
            json.dumps(
                {
                    "name": "КН-11",
                    "students": [
                        {
                            **VALID_STUDENT,
                            "grades": [
                                {
                                    "course": "Python",
                                    "score": 95,
                                    "graded_on": "01.10.2026",
                                }
                            ],
                        }
                    ],
                }
            ),
            id="date-format",
        ),
        pytest.param(
            json.dumps({"name": "КН-11", "students": [VALID_STUDENT, VALID_STUDENT]}),
            id="duplicate-id",
        ),
    ],
)
def test_load_broken_file_raises_storage_error(tmp_path, content):
    path = tmp_path / "group.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(StorageError, match="неправильний формат"):
        load_group(path)


def test_atomic_write_replaces_content(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("старий вміст", encoding="utf-8")

    with atomic_write(path) as file:
        file.write("новий вміст")

    assert path.read_text(encoding="utf-8") == "новий вміст"
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_keeps_old_content_after_error(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("старий вміст", encoding="utf-8")

    with pytest.raises(RuntimeError), atomic_write(path) as file:
        file.write("обрізаний")
        raise RuntimeError("збій посеред запису")

    assert path.read_text(encoding="utf-8") == "старий вміст"
    assert list(tmp_path.iterdir()) == [path]
