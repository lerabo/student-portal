from django.conf import settings
from django.shortcuts import render

from student_portal.storage import load_group


def ranking(request):
    group = load_group(settings.STUDENT_PORTAL_DATA)
    return render(request, "students/ranking.html", {"group": group})
