# HabitFlow - Django Habit Tracker Web App

A clean, responsive, full-stack Habit Tracker web application built from scratch with Python, Django 5.x, SQLite, and modern vanilla CSS.

---

## Features

- **Habit Management**: Create, edit, and delete daily habits with target frequencies (days per week).
- **Weekly Grid View**: Visual Monday-to-Sunday matrix highlighting current day status, completed days, and day-by-day progress.
- **One-Click Toggle & Undo**: Quickly mark habits as completed or undo completions for today or any day of the current week (POST-only, CSRF-protected).
- **Intelligent Streak Counter**: Robust streak tracking that calculates consecutive days completed, keeps the streak alive if yesterday was completed, and properly resets if a day is missed.
- **Strict User Isolation**: Complete data privacy ensuring each user sees, edits, and manages only their own habits and completions.
- **Responsive Mobile Layout**: Specially tailored CSS designed for smooth usability on desktop, tablet, and mobile screens.
- **Django Admin Panel**: Full model registration for `Habit` and `Completion` with inline editing, search fields, and streak display.

---

## Tech Stack

- **Backend**: Python 3.12, Django 5.2 (LTS compatible)
- **Database**: SQLite
- **Frontend**: Django Templates, vanilla modern CSS (responsive flexbox/grid), minimal vanilla JS
- **Testing**: Django's built-in `TestCase` test suite (16 comprehensive tests)

---

## Data Models

1. **`Habit`**
   - `user`: ForeignKey to `auth.User` (on_delete=CASCADE)
   - `name`: CharField (max_length=200)
   - `target_days_per_week`: PositiveSmallIntegerField (1–7)
   - `created_at`: DateTimeField (auto_now_add=True)
   - Method: `calculate_current_streak(reference_date=None) -> int`

2. **`Completion`**
   - `habit`: ForeignKey to `Habit` (related_name="completions", on_delete=CASCADE)
   - `date`: DateField (defaults to `date.today`)
   - Unique Constraint: `UniqueConstraint(fields=["habit", "date"], name="unique_habit_completion_per_day")`

---

## Setup & Running Instructions

### 1. Prerequisites
- Python 3.11+ (Python 3.12 recommended)

### 2. Virtual Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1
# (or in Command Prompt / cmd.exe):
# .venv\Scripts\activate.bat
# (or on macOS/Linux):
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Run the Test Suite

```bash
python manage.py test
```
All 16 unit tests cover:
- Streak calculation (consecutive days, yesterday continuity, missed day streak reset)
- Database unique constraints
- Strict user isolation (unauthorized reads, edits, deletes, toggles)
- View responses and authentication guards

### 5. Start the Development Server

```bash
python manage.py runserver
```

Open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## Pre-configured Demo Accounts

- **Admin Account**:
  - **URL**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  - **Username**: `admin`
  - **Password**: `admin12345`

- **Self Registration**:
  - You can also click **Sign Up** on the navbar to create any new user account.
