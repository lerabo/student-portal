from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from student_portal.grades import ects_grade

from . import models
from .forms import GradeForm
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


@permission_required("students.add_grade", raise_exception=True)
def add_grade(request, student_id):
    """Нова оцінка студента: POST - перенаправлення - GET з повідомленням."""
    student = get_object_or_404(models.Student, pk=student_id)
    if request.method == "POST":
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.student = student
            grade.save()
            messages.success(
                request, f"Оцінку {grade.score} з {grade.course} збережено"
            )
            return redirect("students:detail", student_id=student.pk)
    else:
        form = GradeForm()
    context = {"form": form, "student": student}
    return render(request, "students/grade_form.html", context)


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


class StudentCreateView(PermissionRequiredMixin, CreateView):
    model = models.Student
    fields = ["first_name", "last_name", "group"]
    permission_required = "students.add_student"
    success_url = reverse_lazy("students:list")


class StudentUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.Student
    fields = ["first_name", "last_name", "group"]
    permission_required = "students.change_student"
    pk_url_kwarg = "student_id"

    def get_success_url(self):
        return reverse_lazy("students:detail", args=[self.object.pk])
