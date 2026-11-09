"""Асинхронна розсилка результатів студентам."""

import asyncio
from collections.abc import Iterable, Iterator

from student_portal.people import Student

SEND_DELAY = 0.5  # імітація відповіді поштового сервера, с
MAX_CONCURRENT = 3


async def send_result(student: Student) -> str:
    """Імітує надсилання студентові листа з середнім балом."""
    await asyncio.sleep(SEND_DELAY)
    average = student.average()
    if average is None:
        return f"{student.full_name}: оцінок немає"
    return f"{student.full_name}: середній бал {average:.1f}"


async def notify_sequentially(students: Iterable[Student]) -> list[str]:
    """Надсилає листи по черзі."""
    return [await send_result(student) for student in students]


async def notify_all(
    students: Iterable[Student], limit: int = MAX_CONCURRENT
) -> list[str]:
    """Надсилає листи всім одночасно, але не більше limit водночас."""
    semaphore = asyncio.Semaphore(limit)

    async def send(student: Student) -> str:
        async with semaphore:
            return await send_result(student)

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(send(student)) for student in students]
    return [task.result() for task in tasks]


def chunks[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Видає елементи пакетами по size штук; останній пакет може бути меншим."""
    if size < 1:
        raise ValueError("розмір пакета має бути не менше 1")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


async def notify_in_batches(
    students: Iterable[Student], size: int = MAX_CONCURRENT
) -> list[str]:
    """Надсилає листи пакетами: наступний пакет стартує після всього попереднього."""
    messages: list[str] = []
    for batch in chunks(students, size):
        messages.extend(await asyncio.gather(*(send_result(s) for s in batch)))
    return messages
