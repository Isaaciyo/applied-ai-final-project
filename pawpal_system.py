class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: dict = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or {}
        self.pets = []

    def add_pet(self, pet):
        pass

    def set_availability(self, minutes: int):
        pass


class Pet:
    def __init__(self, name: str, species: str, age: int = None, special_needs: list = None):
        self.name = name
        self.species = species
        self.age = age
        self.special_needs = special_needs or []

    def get_required_tasks(self) -> list:
        pass


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: str, category: str, is_required: bool = False):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category
        self.is_required = is_required

    def is_feasible(self, available_minutes: int) -> bool:
        pass


class Schedule:
    def __init__(self, date: str):
        self.date = date
        self.tasks = []
        self.total_duration = 0
        self.explanation = ""

    def add_task(self, task: Task):
        pass

    def total_time(self) -> int:
        pass

    def to_display(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, available_tasks: list):
        self.owner = owner
        self.pet = pet
        self.available_tasks = available_tasks

    def generate(self, available_minutes: int) -> Schedule:
        pass

    def explain(self, schedule: Schedule) -> str:
        pass
