"""Форми застосунку students: дані користувача перевіряються до збереження."""

from django import forms
from django.utils import timezone

from . import models


class GradeForm(forms.ModelForm):
    """Нова оцінка: поля й обмеження моделі Grade плюс власні перевірки."""

    class Meta:
        model = models.Grade
        fields = ["course", "score", "graded_on"]
        widgets = {"graded_on": forms.DateInput(attrs={"type": "date"})}

    def clean_course(self):
        """Дисципліна без пробілів на початку і в кінці."""
        return self.cleaned_data["course"].strip()

    def clean(self):
        """Перевірка всієї форми: дата оцінки не може бути в майбутньому."""
        cleaned_data = super().clean()
        graded_on = cleaned_data.get("graded_on")
        if graded_on is not None and graded_on > timezone.localdate():
            self.add_error("graded_on", "Дата оцінки не може бути в майбутньому")
        return cleaned_data
