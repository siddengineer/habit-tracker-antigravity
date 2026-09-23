from django import forms
from django.core.exceptions import ValidationError
from .models import Habit


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ["name", "target_days_per_week"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Drink 2L water, Morning Run, Read 20 mins",
                    "autofocus": True,
                }
            ),
            "target_days_per_week": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 7,
                }
            ),
        }
        labels = {
            "name": "Habit Name",
            "target_days_per_week": "Target Frequency (days per week)",
        }
        help_texts = {
            "target_days_per_week": "How many days a week do you aim to complete this? (1 - 7)",
        }

    def clean_target_days_per_week(self):
        target = self.cleaned_data.get("target_days_per_week")
        if target is None or target < 1 or target > 7:
            raise ValidationError("Target days per week must be between 1 and 7.")
        return target
