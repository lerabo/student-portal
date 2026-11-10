from django.contrib import admin

from .models import Grade, Group, Student


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "group"]
    list_filter = ["group"]
    search_fields = ["last_name", "first_name"]
    ordering = ["last_name", "first_name"]
    inlines = [GradeInline]


admin.site.register(Group)
