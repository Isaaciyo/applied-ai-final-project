from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# --- Tasks for Mochi (dog) ---
mochi.add_task(
    Task(
        "Morning walk",
        duration_minutes=30,
        priority="high",
        category="exercise",
        frequency="daily",
        is_required=True,
    )
)
mochi.add_task(
    Task(
        "Breakfast",
        duration_minutes=10,
        priority="high",
        category="feeding",
        frequency="daily",
        is_required=True,
    )
)
mochi.add_task(
    Task(
        "Fetch in yard",
        duration_minutes=20,
        priority="medium",
        category="enrichment",
        frequency="daily",
    )
)

# --- Tasks for Luna (cat) ---
luna.add_task(
    Task(
        "Medication",
        duration_minutes=5,
        priority="high",
        category="health",
        frequency="daily",
        is_required=True,
    )
)
luna.add_task(
    Task(
        "Feeding",
        duration_minutes=10,
        priority="high",
        category="feeding",
        frequency="daily",
        is_required=True,
    )
)
luna.add_task(
    Task(
        "Brush coat",
        duration_minutes=15,
        priority="low",
        category="grooming",
        frequency="weekly",
    )
)

# --- Register pets with owner ---
owner.add_pet(mochi)
owner.add_pet(luna)

# --- Generate schedule ---
scheduler = Scheduler(owner)
schedule = scheduler.generate()

# --- Print results ---
print("=" * 50)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(schedule.to_display())
print("=" * 50)
