from datetime import date, datetime, timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import HabitForm
from .models import Completion, Habit


class SignUpView(View):
    template_name = "registration/signup.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("habit_list")
        form = UserCreationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("habit_list")
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect("habit_list")
        return render(request, self.template_name, {"form": form})


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "habits/habit_list.html"
    context_object_name = "habits"

    def get_queryset(self):
        # Strict user isolation
        return (
            Habit.objects.filter(user=self.request.user)
            .prefetch_related("completions")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()

        # Calculate current week (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]

        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        week_headers = [
            {
                "name": day_labels[i],
                "date": d,
                "is_today": d == today,
                "day_number": d.day,
                "iso_date": d.isoformat(),
            }
            for i, d in enumerate(week_days)
        ]

        habits = list(context["habits"])
        habit_cards = []
        today_completed_count = 0

        for habit in habits:
            completed_dates = set(habit.completions.values_list("date", flat=True))
            streak = habit.calculate_current_streak(today)
            is_done_today = today in completed_dates
            if is_done_today:
                today_completed_count += 1

            # Build week grid for this habit
            grid = []
            week_completions = 0
            for d in week_days:
                completed = d in completed_dates
                if completed:
                    week_completions += 1
                grid.append(
                    {
                        "date": d,
                        "iso_date": d.isoformat(),
                        "day_name": day_labels[d.weekday()],
                        "day_num": d.day,
                        "is_today": d == today,
                        "is_future": d > today,
                        "is_completed": completed,
                    }
                )

            progress_pct = (
                min(100, int((week_completions / habit.target_days_per_week) * 100))
                if habit.target_days_per_week > 0
                else 0
            )

            habit_cards.append(
                {
                    "habit": habit,
                    "streak": streak,
                    "is_done_today": is_done_today,
                    "grid": grid,
                    "week_completions": week_completions,
                    "progress_pct": progress_pct,
                }
            )

        context.update(
            {
                "today": today,
                "week_headers": week_headers,
                "habit_cards": habit_cards,
                "total_habits": len(habits),
                "today_completed_count": today_completed_count,
            }
        )
        return context


class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = "habits/habit_form.html"
    success_url = reverse_lazy("habit_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f'Habit "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create New Habit"
        context["submit_label"] = "Create Habit"
        return context


class HabitUpdateView(LoginRequiredMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = "habits/habit_form.html"
    success_url = reverse_lazy("habit_list")

    def get_queryset(self):
        # Strict user isolation
        return Habit.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Habit "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f'Edit "{self.object.name}"'
        context["submit_label"] = "Save Changes"
        return context


class HabitDeleteView(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = "habits/habit_confirm_delete.html"
    success_url = reverse_lazy("habit_list")

    def get_queryset(self):
        # Strict user isolation
        return Habit.objects.filter(user=self.request.user)

    def form_valid(self, form):
        habit_name = self.object.name
        messages.success(self.request, f'Habit "{habit_name}" was deleted.')
        return super().form_valid(form)


class ToggleCompletionView(LoginRequiredMixin, View):
    """
    POST-only endpoint to mark a habit done or undo for a specific date (defaults to today).
    CSRF protected and strictly scoped to request.user.
    """

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])

    def post(self, request, pk, *args, **kwargs):
        habit = get_object_or_404(Habit, pk=pk, user=request.user)

        target_date_str = request.POST.get("date")
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()

        completion = Completion.objects.filter(habit=habit, date=target_date).first()

        if completion:
            completion.delete()
            messages.info(
                request,
                f'Marked "{habit.name}" as not completed for {target_date.strftime("%b %d")}.',
            )
        else:
            Completion.objects.create(habit=habit, date=target_date)
            messages.success(
                request,
                f'Marked "{habit.name}" as completed for {target_date.strftime("%b %d")}!',
            )

        next_url = request.POST.get("next")
        if next_url and next_url.startswith("/"):
            return HttpResponseRedirect(next_url)
        return redirect("habit_list")
