"""Власні конвертери шляхів застосунку students."""

from student_portal.grades import ECTS_LETTERS


class EctsConverter:
    """Літера шкали ECTS у шляху: A, B, C, D, E або Fx (лише великими)."""

    regex = "|".join(ECTS_LETTERS)

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        if value not in ECTS_LETTERS:
            raise ValueError(f"{value!r} не є літерою шкали ECTS")
        return value
