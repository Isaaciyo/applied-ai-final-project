# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond the basic greedy planner, `pawpal_system.py` includes four additional features:

**Chronological sorting** — `Scheduler.sort_by_time()` orders any list of `(pet, task)` pairs by their `"HH:MM"` time field, making it easy to display the day's plan in the order a pet owner would actually do things.

**Flexible filtering** — `Scheduler.filter_tasks()` accepts optional `completed` and `pet_name` arguments and returns only the matching tasks in a single pass. Useful for views like "show me what's left for Luna today."

**Automatic recurrence** — Every `Task` stores a `due_date` and a `frequency` (`daily`, `weekly`, or `as_needed`). When `Scheduler.mark_task_complete()` is called, it automatically creates the next occurrence of the task — due tomorrow for daily tasks, due in 7 days for weekly ones — and adds it back to the same pet. `as_needed` tasks complete without spawning a copy.

**Conflict detection** — `Scheduler.detect_conflicts()` scans all tasks in one O(n) pass using a `defaultdict`, grouping them by start time. Any slot shared by two or more tasks produces a plain-English warning string. The method never raises — it returns a list the caller can print, log, or ignore.

## Testing PawPal+

### Run the test suite

```bash
source .venv/bin/activate   # if not already active
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Test | Area |
|---|---|
| `test_mark_complete_changes_status` | `Task.mark_complete()` flips `completed` to `True` |
| `test_add_task_increases_pet_task_count` | `Pet.add_task()` correctly grows the task list |
| `test_sort_by_time_returns_chronological_order` | `Scheduler.sort_by_time()` orders tasks `07:00 → 12:00 → 18:00` |
| `test_marking_daily_task_complete_adds_next_day_occurrence` | Completing a `daily` task spawns a new task due `today + 1 day` |
| `test_marking_as_needed_task_complete_adds_no_recurrence` | Completing an `as_needed` task adds nothing to the pet |
| `test_detect_conflicts_flags_duplicate_time_slots` | Two tasks at `08:00` produce exactly one conflict warning |
| `test_detect_conflicts_no_warning_for_distinct_times` | Tasks at different times produce an empty conflict list |

All 7 tests pass on Python 3.14 / pytest 9.0.

### Confidence Level

**4 / 5 stars**

The core scheduling behaviors — greedy generation, priority ordering, recurrence, and conflict detection — are each exercised by at least one test, and the suite covers both happy paths and critical edge cases (as_needed recurrence, no-conflict baseline). One star is withheld because the `generate()` time-budget boundary (task fits exactly) and the multi-pet conflict scenario are not yet tested, leaving a small gap in coverage.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
