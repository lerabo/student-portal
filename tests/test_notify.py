import asyncio
import inspect

import pytest

from student_portal import notify
from student_portal.notify import (
    chunks,
    notify_all,
    notify_in_batches,
    notify_sequentially,
    send_result,
)


@pytest.fixture(autouse=True)
def no_delay(monkeypatch):
    """Тести не чекають «поштовий сервер»."""
    monkeypatch.setattr(notify, "SEND_DELAY", 0)


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        pytest.param(0, "Коваль Олена: середній бал 91.5", id="with-grades"),
        pytest.param(2, "Бойко Ірина: оцінок немає", id="no-grades"),
    ],
)
def test_send_result_text(group, index, expected):
    student = list(group)[index]

    assert asyncio.run(send_result(student)) == expected


def test_notify_sequentially_keeps_order(group):
    messages = asyncio.run(notify_sequentially(group))

    assert [m.split(":")[0] for m in messages] == [
        "Коваль Олена",
        "Мельник Андрій",
        "Бойко Ірина",
    ]


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_notify_all_respects_limit_and_order(mocker, group, limit):
    active = 0
    peak = 0

    async def fake_send(student):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return student.last_name

    send = mocker.patch("student_portal.notify.send_result", side_effect=fake_send)

    messages = asyncio.run(notify_all(group, limit=limit))

    assert messages == ["Коваль", "Мельник", "Бойко"]
    assert peak == limit
    assert send.await_count == 3


@pytest.mark.parametrize(
    ("items", "size", "expected"),
    [
        pytest.param([1, 2, 3, 4, 5, 6], 3, [[1, 2, 3], [4, 5, 6]], id="divides"),
        pytest.param([1, 2, 3, 4, 5], 2, [[1, 2], [3, 4], [5]], id="remainder"),
        pytest.param([1, 2, 3], 1, [[1], [2], [3]], id="size-1"),
        pytest.param([1, 2], 5, [[1, 2]], id="size-bigger"),
        pytest.param([1, 2, 3], 3, [[1, 2, 3]], id="size-equal"),
        pytest.param([], 3, [], id="empty"),
    ],
)
def test_chunks(items, size, expected):
    assert list(chunks(items, size)) == expected


def test_chunks_is_lazy_generator():
    consumed = []

    def source():
        for n in range(10):
            consumed.append(n)
            yield n

    batches = chunks(source(), 2)

    assert inspect.isgenerator(batches)
    assert next(batches) == [0, 1]
    assert consumed == [0, 1]


@pytest.mark.parametrize("size", [0, -1], ids=["zero", "negative"])
def test_chunks_rejects_non_positive_size(size):
    batches = chunks([1, 2, 3], size)

    with pytest.raises(ValueError, match="не менше 1"):
        next(batches)


@pytest.mark.parametrize("size", [1, 2, 3, 5])
def test_notify_in_batches_keeps_student_order(group, size):
    messages = asyncio.run(notify_in_batches(group, size))

    assert messages == [
        "Коваль Олена: середній бал 91.5",
        "Мельник Андрій: середній бал 61.0",
        "Бойко Ірина: оцінок немає",
    ]


def test_notify_in_batches_matches_notify_all(group):
    batched = asyncio.run(notify_in_batches(group, 2))

    assert batched == asyncio.run(notify_all(group, 2))
