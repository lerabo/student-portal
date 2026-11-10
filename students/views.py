from django.shortcuts import render

from .services import get_group


def student_list(request):
    group = get_group()
    query = request.GET.get("q", "").strip()
    students = group.find(query) if query else list(group)
    context = {"group": group, "students": students, "query": query}
    return render(request, "students/student_list.html", context)


def ranking(request):
    group = get_group()
    return render(request, "students/ranking.html", {"group": group})
