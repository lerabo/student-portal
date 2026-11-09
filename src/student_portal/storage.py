"""Збереження групи у файлі JSON."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from student_portal.decorators import timed
from student_portal.exceptions import StorageError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


def group_to_dict(group: Group) -> dict[str, Any]:
    return {
        "name": group.name,
        "students": [
            {
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "grades": [
                    {
                        "course": g.course,
                        "score": g.score,
                        "graded_on": g.graded_on.isoformat(),
                    }
                    for g in s.grades
                ],
            }
            for s in group
        ],
    }


def group_from_dict(data: dict[str, Any]) -> Group:
    group = Group(data["name"])
    for item in data["students"]:
        grades = [
            Grade(g["course"], g["score"], date.fromisoformat(g["graded_on"]))
            for g in item.get("grades", [])
        ]
        group.add(Student(item["id"], item["first_name"], item["last_name"], grades))
    return group


@timed
def save_group(group: Group, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(group_to_dict(group), file, ensure_ascii=False, indent=2)


def load_group(path: Path) -> Group:
    try:
        with path.open(encoding="utf-8") as file:
            return group_from_dict(json.load(file))
    except FileNotFoundError as error:
        raise StorageError(f"файл даних не знайдено: {path.as_posix()}") from error
    except (KeyError, TypeError, ValueError) as error:
        raise StorageError(
            f"файл {path.as_posix()} має неправильний формат: {error}"
        ) from error
