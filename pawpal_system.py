from datetime import date as today_date


class Task:
    VALID_PRIORITIES = ("low", "medium", "high")
    VALID_FREQUENCIES = ("daily", "weekly", "as_needed")

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str = "medium",
        category: str = "general",
        frequency: str = "daily",
        is_required: bool = False,
    ):
        """Create a new care task with a title, duration, priority, category, and frequency."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category
        self.frequency = frequency
        self.is_required = is_required
        self.completed = False

    def is_feasible(self, available_minutes: int) -> bool:
        """Return True if this task fits within the remaining time budget."""
        return self.duration_minutes <= available_minutes

    def mark_complete(self):
        """Mark this task as done for the day."""
        self.completed = True

    def reset(self):
        """Clear completion status (e.g. at the start of a new day)."""
        self.completed = False

    def __repr__(self):
        """Return a concise string representation of the task."""
        status = "done" if self.completed else "pending"
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority}, {status})"


class Pet:
    def __init__(
        self,
        name: str,
        species: str,
        age: int = None,
    ):
        """Create a new pet with a name, species, and optional age."""
        self.name = name
        self.species = species
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str):
        """Remove a task by title. Does nothing if title not found."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_required_tasks(self) -> list[Task]:
        """Return only tasks marked as required."""
        return [t for t in self.tasks if t.is_required]

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been completed today."""
        return [t for t in self.tasks if not t.completed]

    def __repr__(self):
        """Return a concise string representation of the pet."""
        return f"Pet({self.name!r}, {self.species}, {len(self.tasks)} tasks)"


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: dict = None):
        """Create an owner with a name, daily time budget, and optional preferences."""
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet):
        """Register a pet under this owner."""
        self.pets.append(pet)

    def set_availability(self, minutes: int):
        """Update the owner's daily time budget."""
        self.available_minutes = minutes

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs for tasks not yet completed today."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]

    def __repr__(self):
        """Return a concise string representation of the owner."""
        return f"Owner({self.name!r}, {len(self.pets)} pets, {self.available_minutes}min available)"


class Schedule:
    def __init__(self, owner_name: str):
        """Create an empty schedule for today tied to the given owner."""
        self.date = str(today_date.today())
        self.owner_name = owner_name
        self.entries: list[tuple[Pet, Task]] = []
        self.explanation = ""

    def add_entry(self, pet: Pet, task: Task):
        """Add a (pet, task) pair to this schedule."""
        self.entries.append((pet, task))

    def total_time(self) -> int:
        """Total minutes across all scheduled tasks."""
        return sum(task.duration_minutes for _, task in self.entries)

    def to_display(self) -> str:
        """Format the schedule as a readable string."""
        if not self.entries:
            return "No tasks scheduled."
        lines = [f"Schedule for {self.owner_name} — {self.date}", ""]
        for i, (pet, task) in enumerate(self.entries, 1):
            lines.append(
                f"{i}. [{pet.name}] {task.title} "
                f"({task.duration_minutes} min, {task.priority} priority)"
            )
        lines.append(f"\nTotal time: {self.total_time()} minutes")
        if self.explanation:
            lines.append(f"\nReasoning: {self.explanation}")
        return "\n".join(lines)


class Scheduler:
    PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner):
        """Create a scheduler for the given owner and all their pets."""
        self.owner = owner

    def get_tasks_by_priority(self, priority: str) -> list[tuple[Pet, Task]]:
        """Return all pending (pet, task) pairs that match a given priority."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_pending_tasks()
            if task.priority == priority
        ]

    def get_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all pending (pet, task) pairs across all pets, sorted by priority."""
        return sorted(
            self.owner.get_all_pending_tasks(),
            key=lambda pt: (not pt[1].is_required, self.PRIORITY_RANK.get(pt[1].priority, 99)),
        )

    def mark_task_complete(self, title: str):
        """Mark the first pending task with the given title as complete."""
        for _, task in self.owner.get_all_pending_tasks():
            if task.title == title:
                task.mark_complete()
                return

    def generate(self) -> Schedule:
        """
        Build a Schedule by greedily fitting pending tasks into the owner's
        time budget. Required tasks are prioritized first, then high → medium → low.
        """
        schedule = Schedule(owner_name=self.owner.name)
        remaining = self.owner.available_minutes

        for pet, task in self.get_pending_tasks():
            if task.is_feasible(remaining):
                schedule.add_entry(pet, task)
                remaining -= task.duration_minutes

        schedule.explanation = self._explain(schedule, remaining)
        return schedule

    def _explain(self, schedule: Schedule, remaining_minutes: int) -> str:
        """Build a natural language summary of why the schedule was constructed this way."""
        if not schedule.entries:
            return "No tasks could fit within the available time."
        pet_names = sorted({pet.name for pet, _ in schedule.entries})
        return (
            f"Scheduled {len(schedule.entries)} task(s) across "
            f"{', '.join(pet_names)} using {schedule.total_time()} of "
            f"{self.owner.available_minutes} available minutes "
            f"({remaining_minutes} min remaining). "
            "Required tasks were prioritized first, then ordered high → medium → low."
        )
