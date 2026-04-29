# PawPal+

**PawPal+** is an AI-powered pet care scheduling assistant that helps busy pet owners stay consistent with daily routines. Enter your pets, assign care tasks with times and priorities, and let the system build an optimized daily plan — complete with conflict resolution, automatic recurrence, and a Gemini-powered AI agent that reasons through scheduling decisions in plain English.

---

## Original Project (Modules 1–3)

PawPal+ was originally built as a rule-based scheduling system across Modules 1–3 of CodePath's Applied AI course. The core goal was to model a realistic pet care scenario using object-oriented design: an `Owner` with a daily time budget manages multiple `Pet` objects, each with a list of `Task` items that vary by priority, category, and frequency. The original system produced a greedy priority-sorted schedule and detected time-slot conflicts, but had no AI reasoning — all decisions were purely algorithmic.

---

## What's New: AI Feature (Module 4)

This module adds a **multi-step Gemini agent** that replaces blind greedy scheduling with genuine reasoning. Instead of just flagging conflicts, the agent inspects the task list, decides which task to move and why, resolves conflicts automatically, then generates and explains the final plan.

### Why it matters

Pet care involves judgment calls a simple sort can't make — medication before exercise, feeding windows, grooming flexibility. An agent that can weigh task categories and priorities produces a schedule that actually reflects how a responsible owner would think.

---

## Loom video walkthrough

[Video Walkthrough](https://www.loom.com/share/83ff8194b6f4450bacba2866e1679ece "Video Walkthrough")

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    app.py (Streamlit UI)             │
│  ┌──────────────────┐   ┌──────────────────────────┐│
│  │ Generate Schedule│   │   ✨ Generate with AI    ││
│  │ (greedy, instant)│   │   (Gemini agent loop)    ││
│  └──────────────────┘   └──────────┬───────────────┘│
└─────────────────────────────────────┼───────────────┘
                                      │
                          ┌───────────▼──────────────┐
                          │       agent.py            │
                          │  ┌────────────────────┐   │
                          │  │  Gemini 2.5 Flash  │   │
                          │  │  (tool use loop)   │   │
                          │  └─────────┬──────────┘   │
                          │   Tools:   │               │
                          │  • list_tasks              │
                          │  • detect_conflicts        │
                          │  • adjust_task_time  ◄─── mutates task.time
                          │  • generate_schedule       │
                          └───────────┬──────────────┘
                                      │
                          ┌───────────▼──────────────┐
                          │     pawpal_system.py      │
                          │  Task · Pet · Owner       │
                          │  Schedule · Scheduler     │
                          └──────────────────────────┘
```

**Flow:** The UI collects owner/pet/task data and stores it in Streamlit session state. Clicking "Generate with AI" passes the live `Owner` object to `run_scheduling_agent()`, which starts a chat session with Gemini. The model calls tools in sequence — inspecting tasks, finding conflicts, moving task times directly on the Python objects, then scheduling — before returning a natural language explanation and the final schedule entries.

---

## Setup Instructions

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd applied-ai-final-project
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file in the project root (it is already git-ignored):

```
GEMINI_API_KEY=your-key-here
```

Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 5. Run the app

```bash
streamlit run app.py
```

### 6. (Optional) Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

---

## Sample Interactions

### Example 1 — No conflicts, clean schedule

**Input:**
- Owner: Jordan, 90 min available
- Mochi (dog): Morning walk 07:00 (30 min, high, required), Breakfast 08:00 (10 min, high, required), Fetch 15:00 (20 min, medium)
- Luna (cat): Feeding 12:00 (10 min, high, required), Brush coat 17:00 (15 min, low)

**AI output:**
> No conflicts found. I've scheduled all 5 tasks in chronological order, covering both Mochi and Luna within your 90-minute budget. Required tasks were placed first, then medium and low priority filled the remaining time. You have 5 minutes to spare.

| Time  | Pet   | Task         | Duration | Priority |
|-------|-------|--------------|----------|----------|
| 07:00 | Mochi | Morning walk | 30 min   | high     |
| 08:00 | Mochi | Breakfast    | 10 min   | high     |
| 12:00 | Luna  | Feeding      | 10 min   | high     |
| 15:00 | Mochi | Fetch        | 20 min   | medium   |
| 17:00 | Luna  | Brush coat   | 15 min   | low      |

---

### Example 2 — Conflict detected and resolved

**Input:**
- Mochi (dog): Breakfast 08:00 (10 min, high, required)
- Luna (cat): Feeding 08:00 (10 min, high, required) ← same slot

**AI output:**
> I found a conflict at 08:00 — both Mochi's Breakfast and Luna's Feeding were scheduled at the same time. Since both are high-priority required tasks, I moved Luna's Feeding to 08:15 to give Mochi's task the original slot and preserve a natural feeding window for Luna. Here's the resolved schedule:

| Time  | Pet   | Task      | Duration | Priority |
|-------|-------|-----------|----------|----------|
| 08:00 | Mochi | Breakfast | 10 min   | high     |
| 08:15 | Luna  | Feeding   | 10 min   | high     |

---

### Example 3 — Time budget exceeded, tasks skipped

**Input:**
- Owner: Sam, 30 min available
- Mochi (dog): Morning walk 07:00 (30 min, high, required), Fetch 15:00 (20 min, medium), Brush coat 17:00 (15 min, low)

**AI output:**
> With only 30 minutes available, I could only fit the Morning walk — it's required and uses your full budget. Fetch and Brush coat were skipped. Consider increasing your available time or marking lower-priority tasks as optional if you'd like more flexibility.

| Time  | Pet   | Task         | Duration | Priority |
|-------|-------|--------------|----------|----------|
| 07:00 | Mochi | Morning walk | 30 min   | high     |

---

## Design Decisions

### Why a multi-step agent over the other AI options

Four options were considered: RAG, a multi-step agent, structured prompting, and a reliability harness. The agent was chosen because the app's real weakness was the dumb scheduler — it couldn't reason about *why* to move a conflicting task or weigh task categories. A RAG system would have required an external knowledge base that doesn't exist here. Structured prompting alone would have improved explanations without fixing the core logic gap.

### Why Gemini 2.5 Flash

Originally implemented with Claude Sonnet 4.6. Switched to Gemini 2.5 Flash to use the free tier for development and academic use. The task — multi-step tool use with a small, stable schema — is well within Gemini 2.5 Flash's capabilities, and the API shape is nearly identical. The only meaningful loss was explicit prompt caching (a Claude feature), which doesn't matter at free-tier scale.

### Why tools mutate the live Owner object directly

The `adjust_task_time` tool doesn't create a copy of the schedule — it modifies `task.time` on the actual `Pet` object in Streamlit session state. This means the AI's conflict resolution is reflected immediately in the task list the user sees. The tradeoff is that the agent's changes are permanent within that session. A future improvement could stage changes and let the user confirm before applying.

### Conflict detection: exact match vs. overlap

`detect_conflicts()` flags tasks that share the exact same `HH:MM` start time. It does not check whether a task's duration runs into the next task's start (e.g., a 30-minute walk at 07:00 overlapping a task at 07:15). A full overlap check would require O(n²) interval comparisons. The exact-match approach is O(n) using a `defaultdict`, simple to understand and test, and appropriate for pet care where times are approximate anchors rather than hard deadlines. Duration-based overlap can be added later without restructuring the method.

### Greedy scheduler preserved

The original "Generate schedule" button is kept alongside the AI path. This gives users an instant, free fallback and makes it easy to compare the greedy output against the AI's reasoning. It also means the app is fully functional without an API key.

---

## Testing Summary

### Layer 1 — Unit tests (7 tests, all passing)

These tests cover the core domain logic in `pawpal_system.py` and run instantly with no API calls.

```bash
python -m pytest tests/test_pawpal.py -v
```

| Test | What it covers |
|---|---|
| `test_mark_complete_changes_status` | `Task.mark_complete()` sets `completed = True` |
| `test_add_task_increases_pet_task_count` | `Pet.add_task()` grows the task list correctly |
| `test_sort_by_time_returns_chronological_order` | Tasks sort `07:00 → 12:00 → 18:00` |
| `test_marking_daily_task_complete_adds_next_day_occurrence` | Daily task recurrence creates a task due tomorrow |
| `test_marking_as_needed_task_complete_adds_no_recurrence` | `as_needed` tasks complete without spawning a copy |
| `test_detect_conflicts_flags_duplicate_time_slots` | Two tasks at `08:00` produce exactly one warning |
| `test_detect_conflicts_no_warning_for_distinct_times` | Tasks at different times produce an empty list |

**7/7 tests passing.**

---

### Layer 2 — AI output validation (4 checks, run after every agent call)

Because the AI's responses are non-deterministic, traditional unit tests can't prove it works — mocking Gemini would only test a fake version of the model. Instead, `validate_schedule()` in `agent.py` checks the agent's *output* against constraints we know are correct, deterministically, every time the agent runs.

| Check | What it verifies |
|---|---|
| **Conflicts resolved** | Time-slot conflicts dropped to 0 after agent ran |
| **Time budget respected** | Total scheduled minutes ≤ owner's available minutes |
| **Required tasks included** | Every `is_required` task appears in the final schedule |
| **Valid HH:MM times** | All task times match `^\d{2}:\d{2}$` |

Results are displayed in the UI below the schedule and written to `agent_runs.log` for every run.

**Example log output:**

```
2026-04-26 14:32:01 INFO Agent run started | owner='Jordan' | pets=['Mochi', 'Luna'] | conflicts_before=2
2026-04-26 14:32:04 INFO Agent run complete | owner='Jordan' | adjustments=['Feeding from 08:00 to 08:15'] | tasks_scheduled=5 | validation=4/4 checks passed
2026-04-26 14:32:04 INFO   [PASS] Conflicts resolved: 2 found before agent, 0 remaining after
2026-04-26 14:32:04 INFO   [PASS] Time budget respected: 85 min used of 90 available
2026-04-26 14:32:04 INFO   [PASS] Required tasks included: All required tasks scheduled
2026-04-26 14:32:04 INFO   [PASS] Valid HH:MM times: All times valid
```

---

### What worked

The domain logic tests proved stable across all development. The output validation layer caught a real edge case during development: when the owner's time budget was exactly met, the "required tasks included" check revealed a required task that the greedy scheduler had silently dropped because it processed tasks in priority order and ran out of time before reaching it.

### What didn't / gaps

The `generate()` time-budget boundary case and multi-pet conflict scenarios are not covered by unit tests. The AI validation layer cannot catch *reasoning quality* — it verifies that the schedule is structurally correct, not that the agent's explanation was accurate or that it moved the right task.

### What I learned

Writing tests before finalizing logic forced cleaner method signatures — the decision to remove `available_minutes` as a parameter from `Scheduler.generate()` came directly from noticing that a test would need to pass conflicting values to trigger a bug. For the AI layer, the key insight was that you can't unit-test a non-deterministic model, but you *can* unit-test its outputs against known invariants. That distinction — testing what the AI *did* vs. testing the AI itself — is the foundation of a reliable AI system.

---

## Reflection

Building PawPal+ taught me that AI is most useful when it handles decisions that are genuinely ambiguous — not just computation. The original greedy scheduler was fast and correct, but it couldn't exercise judgment: it didn't know that medication matters more than grooming, or that two high-priority tasks both deserve to run rather than having one silently dropped. Adding the Gemini agent filled that gap, but it also introduced new complexity: the agent can make changes the user didn't explicitly approve, which is a real product risk.

The most important thing I learned is that designing for AI integration requires thinking about trust boundaries early. Which decisions should the AI make autonomously? Which should it surface for human review? In this project, the agent mutates task times directly — that's convenient but opaque. A better design would show the user "I'm planning to move Luna's Feeding from 08:00 to 08:15 — confirm?" before applying the change. That's the next iteration.

On the engineering side: the cleanest AI systems are the ones where the AI layer is thin and the domain logic underneath it is solid. Because `pawpal_system.py` had clean, well-tested methods, wiring up four tool functions took less than an hour. The AI doesn't reimplement scheduling — it orchestrates code that already works. That separation made the system easier to build, test, and debug.

---

## Responsible AI

See [model_card.md](model_card.md) for a full reflection on limitations, misuse potential, testing surprises, and AI collaboration during this project.

---

## Project Structure

```
applied-ai-final-project/
├── app.py                  # Streamlit UI
├── agent.py                # Gemini multi-step agent + tool definitions
├── pawpal_system.py        # Core domain model (Task, Pet, Owner, Scheduler)
├── main.py                 # CLI demo script
├── tests/
│   └── test_pawpal.py      # Pytest test suite (7 tests)
├── requirements.txt
├── .env                    # API key (git-ignored)
├── dev_log.md              # Development log
├── reflection.md           # Course reflection questions
└── model_card.md           # Responsible AI reflection
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `google-genai` | Gemini API client (agent) |
| `python-dotenv` | Load `.env` into environment |
| `pytest` | Test runner |

