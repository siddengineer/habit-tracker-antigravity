from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse

from .models import Completion, Habit

User = get_user_model()


class StreakCalculationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.habit = Habit.objects.create(
            user=self.user,
            name="Daily Reading",
            target_days_per_week=7,
        )
        self.ref_date = date(2026, 9, 23)

    def test_streak_zero_when_no_completions(self):
        streak = self.habit.calculate_current_streak(self.ref_date)
        self.assertEqual(streak, 0)

    def test_streak_when_completed_today_only(self):
        Completion.objects.create(habit=self.habit, date=self.ref_date)
        streak = self.habit.calculate_current_streak(self.ref_date)
        self.assertEqual(streak, 1)

    def test_streak_active_from_yesterday_when_today_not_yet_done(self):
        # Completed yesterday, but not yet today
        yesterday = self.ref_date - timedelta(days=1)
        two_days_ago = self.ref_date - timedelta(days=2)
        Completion.objects.create(habit=self.habit, date=yesterday)
        Completion.objects.create(habit=self.habit, date=two_days_ago)

        streak = self.habit.calculate_current_streak(self.ref_date)
        self.assertEqual(streak, 2)

    def test_streak_continuous_multi_day_including_today(self):
        # 5 consecutive days ending today
        for i in range(5):
            Completion.objects.create(habit=self.habit, date=self.ref_date - timedelta(days=i))

        streak = self.habit.calculate_current_streak(self.ref_date)
        self.assertEqual(streak, 5)

    def test_streak_resets_after_missed_day(self):
        # Completed: today, [yesterday missed], 2 days ago, 3 days ago
        two_days_ago = self.ref_date - timedelta(days=2)
        three_days_ago = self.ref_date - timedelta(days=3)

        Completion.objects.create(habit=self.habit, date=self.ref_date)
        Completion.objects.create(habit=self.habit, date=two_days_ago)
        Completion.objects.create(habit=self.habit, date=three_days_ago)

        # Because yesterday was missed, streak should reset to 1 (only today)
        streak = self.habit.calculate_current_streak(self.ref_date)
        self.assertEqual(streak, 1)

    def test_streak_broken_when_yesterday_and_today_missed(self):
        # Completed 2 days ago, 3 days ago, but yesterday and today are missed
        two_days_ago = self.ref_date - timedelta(days=2)
        three_days_ago = self.ref_date - timedelta(days=3)
        Completion.objects.create(habit=self.habit, date=two_days_ago)
        Completion.objects.create(habit=self.habit, date=three_days_ago)

        streak = self.habit.calculate_current_streak(self.ref_date)
        self.assertEqual(streak, 0)


class UniqueConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.habit = Habit.objects.create(
            user=self.user,
            name="Morning Yoga",
            target_days_per_week=5,
        )

    def test_cannot_create_duplicate_completion_same_day(self):
        today = date.today()
        Completion.objects.create(habit=self.habit, date=today)

        with self.assertRaises(IntegrityError):
            Completion.objects.create(habit=self.habit, date=today)

    def test_different_habits_can_complete_on_same_day(self):
        second_habit = Habit.objects.create(
            user=self.user,
            name="Evening Walk",
            target_days_per_week=7,
        )
        today = date.today()
        c1 = Completion.objects.create(habit=self.habit, date=today)
        c2 = Completion.objects.create(habit=second_habit, date=today)
        self.assertIsNotNone(c1.pk)
        self.assertIsNotNone(c2.pk)


class UserIsolationTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="alice", password="passwordA")
        self.user_b = User.objects.create_user(username="bob", password="passwordB")

        self.habit_a = Habit.objects.create(
            user=self.user_a,
            name="Alice Secret Journal",
            target_days_per_week=7,
        )
        self.habit_b = Habit.objects.create(
            user=self.user_b,
            name="Bob Guitar Practice",
            target_days_per_week=3,
        )

        self.client_a = Client()
        self.client_a.login(username="alice", password="passwordA")

        self.client_b = Client()
        self.client_b.login(username="bob", password="passwordB")

    def test_user_cannot_see_other_users_habits_in_list(self):
        response_a = self.client_a.get(reverse("habit_list"))
        self.assertEqual(response_a.status_code, 200)
        self.assertContains(response_a, "Alice Secret Journal")
        self.assertNotContains(response_a, "Bob Guitar Practice")

        response_b = self.client_b.get(reverse("habit_list"))
        self.assertEqual(response_b.status_code, 200)
        self.assertContains(response_b, "Bob Guitar Practice")
        self.assertNotContains(response_b, "Alice Secret Journal")

    def test_user_cannot_access_or_edit_another_users_habit(self):
        # Bob tries to access Alice's habit edit page
        edit_url = reverse("habit_update", kwargs={"pk": self.habit_a.pk})
        response = self.client_b.get(edit_url)
        self.assertEqual(response.status_code, 404)

        # Bob tries to submit an edit to Alice's habit
        post_response = self.client_b.post(
            edit_url,
            {"name": "Hacked Name", "target_days_per_week": 1},
        )
        self.assertEqual(post_response.status_code, 404)
        self.habit_a.refresh_from_db()
        self.assertEqual(self.habit_a.name, "Alice Secret Journal")

    def test_user_cannot_delete_another_users_habit(self):
        delete_url = reverse("habit_delete", kwargs={"pk": self.habit_a.pk})
        response = self.client_b.post(delete_url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Habit.objects.filter(pk=self.habit_a.pk).exists())

    def test_user_cannot_toggle_completion_on_another_users_habit(self):
        toggle_url = reverse("toggle_completion", kwargs={"pk": self.habit_a.pk})
        response = self.client_b.post(
            toggle_url,
            {"date": str(date.today())},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Completion.objects.filter(habit=self.habit_a).count(), 0)


class ViewAndAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client = Client()

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse("habit_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_toggle_completion_post_only(self):
        self.client.login(username="testuser", password="password123")
        habit = Habit.objects.create(user=self.user, name="Meditation")
        toggle_url = reverse("toggle_completion", kwargs={"pk": habit.pk})

        get_response = self.client.get(toggle_url)
        self.assertEqual(get_response.status_code, 405)

    def test_toggle_completion_marks_and_unmarks(self):
        self.client.login(username="testuser", password="password123")
        habit = Habit.objects.create(user=self.user, name="Pushups")
        today = date.today()
        toggle_url = reverse("toggle_completion", kwargs={"pk": habit.pk})

        # 1. First toggle -> marks done
        res1 = self.client.post(toggle_url, {"date": today.isoformat()})
        self.assertEqual(res1.status_code, 302)
        self.assertTrue(Completion.objects.filter(habit=habit, date=today).exists())

        # 2. Second toggle -> undoes
        res2 = self.client.post(toggle_url, {"date": today.isoformat()})
        self.assertEqual(res2.status_code, 302)
        self.assertFalse(Completion.objects.filter(habit=habit, date=today).exists())

    def test_create_habit_form_validation(self):
        self.client.login(username="testuser", password="password123")
        # Target days out of range (> 7)
        response = self.client.post(
            reverse("habit_create"),
            {"name": "Invalid Target", "target_days_per_week": 8},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "target_days_per_week", "Target days per week must be between 1 and 7.")
