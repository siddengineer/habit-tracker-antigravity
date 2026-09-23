from django.contrib import admin
from .models import Habit, Completion


class CompletionInline(admin.TabularInline):
    model = Completion
    extra = 1


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "target_days_per_week", "created_at", "current_streak_display")
    list_filter = ("target_days_per_week", "created_at")
    search_fields = ("name", "user__username")
    inlines = [CompletionInline]

    @admin.display(description="Current Streak")
    def current_streak_display(self, obj):
        return f"{obj.calculate_current_streak()} days"


@admin.register(Completion)
class CompletionAdmin(admin.ModelAdmin):
    list_display = ("habit", "get_user", "date")
    list_filter = ("date",)
    search_fields = ("habit__name", "habit__user__username")

    @admin.display(description="User", ordering="habit__user")
    def get_user(self, obj):
        return obj.habit.user
