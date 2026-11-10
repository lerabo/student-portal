from django import template

from student_portal.grades import ects_grade

register = template.Library()


@register.filter
def ects(score):
    """{{ student.average|ects }} → літера шкали ECTS; для None - порожній рядок."""
    if score is None:
        return ""
    return ects_grade(score)


@register.filter
def grade_class(score):
    """{{ grade.score|grade_class }} → CSS-клас grade-a … grade-fx; для None - ""."""
    letter = ects(score)
    return f"grade-{letter.lower()}" if letter else ""
