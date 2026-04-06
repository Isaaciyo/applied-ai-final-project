from datetime import timedelta, date as today_date

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task(
        "Morning walk", duration_minutes=30, priority="high", category="exercise"
    )
    assert not task.completed
    task.mark_complete()
    assert task.completed


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(
        Task("Breakfast", duration_minutes=10, priority="high", category="feeding")
    )
    assert len(pet.tasks) == 1
    pet.add_task(
        Task(
            "Fetch in yard",
            duration_minutes=20,
            priority="medium",
            category="enrichment",
        )
    )
    assert len(pet.tasks) == 2


# --- Sorting correctness ---

def test_sort_by_time_returns_chronological_order():
    """Tasks should come back sorted by HH:MM, earliest first."""
    owner = Owner("Ada", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    late = Task("Dinner", duration_minutes=10, time="18:00")
    early = Task("Breakfast", duration_minutes=10, time="07:00")
    mid = Task("Lunch", duration_minutes=10, time="12:00")
    pet.add_task(late)
    pet.add_task(early)
    pet.add_task(mid)

    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(scheduler.owner.get_all_tasks())
    times = [task.time for _, task in sorted_tasks]
    assert times == ["07:00", "12:00", "18:00"]


# --- Recurrence logic ---

def test_marking_daily_task_complete_adds_next_day_occurrence():
    """After completing a daily task, the pet should gain a new task due tomorrow."""
    owner = Owner("Ada", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    task = Task("Morning walk", duration_minutes=30, frequency="daily")
    task.due_date = today_date.today()
    pet.add_task(task)

    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Morning walk")

    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].due_date == today_date.today() + timedelta(days=1)


def test_marking_as_needed_task_complete_adds_no_recurrence():
    """Completing an as_needed task should not add a follow-up task."""
    owner = Owner("Ada", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    task = Task("Vet visit", duration_minutes=60, frequency="as_needed")
    pet.add_task(task)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_task_complete("Vet visit")

    assert next_task is None
    assert len(pet.get_pending_tasks()) == 0


# --- Conflict detection ---

def test_detect_conflicts_flags_duplicate_time_slots():
    """Two tasks scheduled at the same time should produce a conflict warning."""
    owner = Owner("Ada", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    pet.add_task(Task("Breakfast", duration_minutes=10, time="08:00"))
    pet.add_task(Task("Meds", duration_minutes=5, time="08:00"))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_no_warning_for_distinct_times():
    """Tasks at different times should produce no conflicts."""
    owner = Owner("Ada", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    pet.add_task(Task("Breakfast", duration_minutes=10, time="08:00"))
    pet.add_task(Task("Dinner", duration_minutes=10, time="18:00"))

    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []
