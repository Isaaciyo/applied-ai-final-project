from pawpal_system import Pet, Task


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
