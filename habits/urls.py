from django.urls import path
from . import views

urlpatterns = [
    path("", views.HabitListView.as_view(), name="habit_list"),
    path("habits/new/", views.HabitCreateView.as_view(), name="habit_create"),
    path("habits/<int:pk>/edit/", views.HabitUpdateView.as_view(), name="habit_update"),
    path("habits/<int:pk>/delete/", views.HabitDeleteView.as_view(), name="habit_delete"),
    path("habits/<int:pk>/toggle/", views.ToggleCompletionView.as_view(), name="toggle_completion"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
]
