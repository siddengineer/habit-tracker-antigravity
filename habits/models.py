from datetime import date, timedelta
from django.conf import settings
from django.db import models


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )
    name = models.CharField(max_length=200)
    target_days_per_week = models.PositiveSmallIntegerField(
        default=7,
        help_text="Target frequency in days per week (1-7)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def calculate_current_streak(self, reference_date=None) -> int:
        """
        Calculates the current streak of consecutive days completed.
        - Consecutive completed days leading up to reference_date (defaults to today).
        - If today is completed, streak includes today and counts backward.
        - If today is not completed, check if yesterday was completed.
          If yes, streak includes yesterday and counts backward.
          If neither today nor yesterday is completed, the streak is 0 (broken/reset).
        """
        if reference_date is None:
            reference_date = date.today()

        # Get set of all completed dates for this habit
        completed_dates = set(
            self.completions.values_list("date", flat=True)
        )

        streak = 0
        current_check = reference_date

        if current_check in completed_dates:
            # Completed today: count backward starting today
            while current_check in completed_dates:
                streak += 1
                current_check -= timedelta(days=1)
        else:
            # Not completed today: check if yesterday was completed
            yesterday = reference_date - timedelta(days=1)
            if yesterday in completed_dates:
                current_check = yesterday
                while current_check in completed_dates:
                    streak += 1
                    current_check -= timedelta(days=1)
            else:
                # Neither today nor yesterday completed -> streak is 0
                return 0

        return streak


class Completion(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    date = models.DateField(default=date.today)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["habit", "date"],
                name="unique_habit_completion_per_day",
            )
        ]

    def __str__(self):
        return f"{self.habit.name} - {self.date}"
