from collections import defaultdict
from datetime import date as today_date, timedelta


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
        time: str = "00:00",
    ):
        """Create a new care task with a title, duration, priority, category, frequency, and scheduled time (HH:MM)."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category
        self.frequency = frequency
        self.is_required = is_required
        self.completed = False
        self.time = time
        self.due_date: today_date = today_date.today()

    def next_occurrence(self) -> "Task | None":
        """Return a new Task due tomorrow (daily) or in 7 days (weekly), or None if as_needed."""
        if self.frequency == "daily":
            delta = timedelta(days=1)
        elif self.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None  # as_needed tasks do not recur automatically

        next_task = Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            is_required=self.is_required,
            time=self.time,
        )
        next_task.due_date = self.due_date + delta
        return next_task

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

    def sort_by_time(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return the given (pet, task) pairs sorted chronologically by task.time (HH:MM)."""
        return sorted(tasks, key=lambda pt: pt[1].time)

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs optionally filtered by completion status and/or pet name."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if (completed is None or task.completed == completed)
            and (pet_name is None or pet.name == pet_name)
        ]

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

    def mark_task_complete(self, title: str) -> "Task | None":
        """Mark the first pending task matching title complete and schedule its next occurrence if recurring."""
        for pet, task in self.owner.get_all_pending_tasks():
            if task.title == title:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                return next_task
        return None

    def detect_conflicts(self) -> list[str]:
        """Return a list of warning strings for any time slots shared by two or more tasks."""
        slots: dict[str, list[tuple[str, str]]] = defaultdict(list)

        for pet, task in self.owner.get_all_tasks():
            slots[task.time].append((pet.name, task.title))

        warnings = []
        for time_slot, entries in sorted(slots.items()):
            if len(entries) > 1:
                details = ", ".join(f"[{pet}] {title}" for pet, title in entries)
                warnings.append(
                    f"WARNING: Scheduling conflict at {time_slot} — {details}"
                )

        return warnings

    def generate(self) -> Schedule:
        """Greedily fit pending tasks into the owner's time budget, required and high-priority first."""
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
