from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView, TemplateView

from student_portal.grades import ects_grade

from .services import get_group, get_student_or_404


def student_list(request):
    group = get_group()
    query = request.GET.get("q", "").strip()
    students = group.find(query) if query else list(group)
    context = {"group": group, "students": students, "query": query}
    return render(request, "students/student_list.html", context)


def student_detail(request, student_id):
    student = get_student_or_404(get_group(), student_id)
    return render(request, "students/student_detail.html", {"student": student})


def student_json(request, student_id):
    student = get_student_or_404(get_group(), student_id)
    return JsonResponse(
        {
            "id": student.id,
            "full_name": student.full_name,
            "average": student.average(),
        },
        json_dumps_params={"ensure_ascii": False},
    )


def by_ects(request, letter):
    """Студенти, чий середній бал відповідає літері ECTS."""
    group = get_group()
    students = [
        s
        for s in group
        if (average := s.average()) is not None and ects_grade(average) == letter
    ]
    context = {"group": group, "letter": letter, "students": students}
    return render(request, "students/by_ects.html", context)


def legacy_student(request, student_id):
    """Стара адреса /students/st/0003/ назавжди переїхала на /students/3/."""
    return redirect("students:detail", student_id=int(student_id), permanent=True)


class RankingView(TemplateView):
    template_name = "students/ranking.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_group()
        context["group"] = group
        context["ranking"] = group.ranking()
        return context


class StudentListView(ListView):
    template_name = "students/student_pages.html"
    context_object_name = "students"
    paginate_by = 2

    def get_queryset(self):
        return get_group().ranking()
