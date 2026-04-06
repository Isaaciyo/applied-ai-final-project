from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# --- Mochi's tasks ---
mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high",   category="exercise",   frequency="daily",    time="07:00", is_required=True))
mochi.add_task(Task("Breakfast",    duration_minutes=10, priority="high",   category="feeding",    frequency="daily",    time="08:00", is_required=True))  # conflict
mochi.add_task(Task("Fetch in yard",duration_minutes=20, priority="medium", category="enrichment", frequency="daily",    time="15:00"))

# --- Luna's tasks ---
mochi.add_task(Task("Medication",   duration_minutes=5,  priority="high",   category="health",     frequency="as_needed",time="07:30", is_required=True))
luna.add_task(Task("Feeding",       duration_minutes=10, priority="high",   category="feeding",    frequency="daily",    time="08:00", is_required=True))  # conflict — same slot as Mochi's Breakfast
luna.add_task(Task("Brush coat",    duration_minutes=15, priority="low",    category="grooming",   frequency="weekly",   time="17:00"))
luna.add_task(Task("Evening play",  duration_minutes=15, priority="medium", category="enrichment", frequency="daily",    time="17:00"))  # second conflict — same pet, same slot

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

# ── 1. Conflict detection BEFORE generating the schedule ────────────────────
print("=" * 56)
print("  CONFLICT DETECTION")
print("=" * 56)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

# ── 2. Generate and display schedule ────────────────────────────────────────
schedule = scheduler.generate()
print("\n" + "=" * 56)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 56)
print(schedule.to_display())

# ── 3. All tasks sorted by time (shows the clashes visually) ────────────────
print("\n" + "=" * 56)
print("  SORT_BY_TIME — Full Task List")
print("=" * 56)
for pet, task in scheduler.sort_by_time(scheduler.owner.get_all_tasks()):
    print(f"  {task.time}  [{pet.name}]  {task.title}")

print("=" * 56)
