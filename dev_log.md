# PawPal+ Development Log

---

## Session 1 — AI Feature Integration

### Project Exploration

Started by reading the full codebase to understand what PawPal+ does before making any changes.

**What it is:** A Streamlit app for busy pet owners to organize daily pet care routines. Users register pets, assign tasks (walks, feeding, meds, grooming, etc.) with times/priorities/durations, and the app generates an optimized daily schedule.

**Core files:**
- `pawpal_system.py` — domain model: `Task`, `Pet`, `Owner`, `Schedule`, `Scheduler`
- `app.py` — Streamlit UI (4 sections: owner setup, add pets, add tasks, generate schedule)
- `main.py` — CLI demo showing conflict detection + schedule output
- `tests/test_pawpal.py` — 7 pytest tests covering core scheduling behaviors

**Key limitation identified:** The scheduler is purely algorithmic — a greedy priority sort that fits tasks into a time budget. When time conflicts occur (two tasks at the same slot), it just flags them and leaves the user to fix them manually. No reasoning, no negotiation, no intelligence.

---

### Feature Decision: Multi-Step Agent

The assignment offered four options:
- RAG (retrieval-augmented generation)
- Multi-step agent / planning workflow
- Specialized behavior (structured prompting / mini fine-tune)
- Reliability harness (evaluation loop, guardrails, self-checking)

**Decision: Multi-step agent.**

**Reasoning:**
- The app's core weakness is the dumb scheduler. An agent can *reason* about scheduling — understanding that a medication task should precede exercise, or that pushing a feeding 15 minutes later is a safe tradeoff to resolve a conflict.
- RAG was rejected because the domain is narrow enough that structured prompting covers it — there's no external knowledge base that needs retrieval.
- Structured prompting alone would improve explanations but not fix the scheduling logic itself, which is the real gap.
- A reliability harness would be valuable infrastructure but wouldn't visibly improve the user experience at this stage.
- The tradeoff acknowledged: adds API cost and latency. Acceptable because users interact with this once a day to plan their routine, not in a tight loop.

---

### Model Choice: Claude vs. Gemini

Initially defaulted to Claude (Anthropic SDK) because the project runs inside Claude Code. Discussed the tradeoff honestly:
- No strong technical reason to prefer Claude over Gemini for this task — both handle multi-step tool use well
- Gemini 2.0 Flash would be fast and cheap
- Reasons to stay with Claude: CodePath context, single SDK/API key, consistency with the development environment, and the `claude-api` skill available in the session
- User confirmed: stick with Claude (`claude-sonnet-4-6`)

---

### Implementation Plan (pre-coding)

Agreed plan before writing any code:

**Files to create/modify:**
| File | Change |
|---|---|
| `agent.py` | New — agent loop + tool definitions |
| `app.py` | Modified — add "Generate with AI" button in Section 4 |
| `requirements.txt` | Modified — add `anthropic>=0.40.0` |

**Agent tools defined:**
| Tool | Purpose |
|---|---|
| `list_tasks` | Returns all (pet, task) pairs as structured JSON |
| `detect_conflicts` | Returns conflict warning strings |
| `adjust_task_time` | Moves a task to a new HH:MM slot — the key conflict-resolution tool |
| `generate_schedule` | Runs the existing greedy scheduler, returns the result |

**Agent loop design:**
1. Claude calls `list_tasks` + `detect_conflicts` to assess the situation
2. If conflicts exist, Claude reasons about resolution and calls `adjust_task_time`
3. Claude calls `generate_schedule` to finalize
4. Claude returns a natural language explanation of decisions made

---

### Implementation

**`requirements.txt`** — added `anthropic>=0.40.0`

**`agent.py`** (new file):
- `SYSTEM_PROMPT` — instructs Claude to assess, resolve conflicts, generate, then explain. Marked with `cache_control: ephemeral` for prompt caching (avoids re-charging on every call).
- `TOOLS` — 4 tool definitions with JSON schemas
- `_list_tasks`, `_detect_conflicts`, `_adjust_task_time`, `_generate_schedule` — Python implementations that operate directly on the live `Owner` object (mutations to `task.time` persist in session state)
- `_dispatch` — routes tool calls to the right function
- `run_scheduling_agent(owner)` — the agentic loop: sends messages, executes tool calls, continues until `stop_reason == "end_turn"`. Returns `(explanation_text, final_schedule_entries)`.

**`app.py`** — Section 4 refactored:
- Split into two side-by-side columns
- Left: original "Generate schedule" button, unchanged behavior
- Right: "✨ Generate with AI" button — calls `run_scheduling_agent`, shows spinner during agent execution, then renders the AI-negotiated schedule table + Claude's reasoning below it
- Guards for missing API key (`ANTHROPIC_API_KEY` env var) with a clear error message

**Dependency installed:** `anthropic` added to `.venv` via pip. Import check passed.

---

### To run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
source .venv/bin/activate
streamlit run app.py
```

---

---

## Session 2 — Switched from Claude to Gemini

### Decision

Switched the AI backend from Claude (`claude-sonnet-4-6`) to Gemini (`gemini-2.5-flash`) to use the free tier and avoid API costs during development.

### Tradeoffs discussed

| | Claude (before) | Gemini (after) |
|---|---|---|
| Cost | Paid per token | Free tier via Google AI Studio |
| Prompt caching | Explicit (`cache_control: ephemeral`) | N/A — dropped, irrelevant on free tier |
| Tool use quality | Strong | Comparable for this task |
| SDK | `anthropic` | `google-genai` |
| API key env var | `ANTHROPIC_API_KEY` | `GEMINI_API_KEY` |

### What changed

**`requirements.txt`** — swapped `anthropic>=0.40.0` for `google-genai>=1.0.0`

**`agent.py`** — full rewrite of the API layer:
- Client: `genai.Client` from `google.genai`
- Tool definitions: `types.Tool` + `types.FunctionDeclaration` with OpenAPI-style parameter dicts
- Response parsing: check `part.function_call` instead of `block.type == "tool_use"`
- Tool results: sent back as `types.Part(function_response=types.FunctionResponse(...))`
- Client init moved inside `run_scheduling_agent()` (lazy init) so the module loads cleanly when `GEMINI_API_KEY` is not set
- Dropped `cache_control` on system prompt — no longer applicable
- The 4 tool implementations (`_list_tasks`, `_detect_conflicts`, `_adjust_task_time`, `_generate_schedule`) were **unchanged** — they operate on `pawpal_system` objects, not the AI API

**`app.py`** — one line: env var guard changed from `ANTHROPIC_API_KEY` to `GEMINI_API_KEY`

### To run

```bash
export GEMINI_API_KEY=<your-key-from-aistudio.google.com>
source .venv/bin/activate
streamlit run app.py
```

---

---

## Session 3 — README rewrite + .env setup

### .env / API key hygiene
- Updated `.env` to use `GEMINI_API_KEY` (replacing old `ANTHROPIC_API_KEY` placeholder)
- Added `.env` to `.gitignore` to prevent accidental key exposure
- Added `python-dotenv` to `requirements.txt` and `load_dotenv()` to `app.py` so the key is loaded automatically on startup

### README rewrite
Rewrote `README.md` from a course worksheet into a portfolio-quality document covering:
- Original project summary (Modules 1–3 goals and capabilities)
- Title, summary, and why it matters
- Architecture diagram with agent tool flow
- Step-by-step setup instructions
- 3 sample interactions with example AI outputs
- Design decisions section (agent choice, Gemini vs. Claude, mutation tradeoffs, conflict detection approach)
- Testing summary with test table, gaps, and lessons learned
- Reflection on trust boundaries, AI judgment, and thin AI / thick domain layer principle

---

## Session 4 — Reliability harness: output validation + logging

### Problem
The AI agent produced schedules but there was no proof it was doing the right thing — it just *seemed* to work. The goal was to add at least one way to measure reliability objectively.

### Approach chosen: logged output validation
Four options were discussed (automated tests, confidence scoring, logging/error handling, human evaluation). Output validation + logging was chosen because:
- The AI's responses are non-deterministic — mocking Gemini would only test a fake model
- Confidence scoring is self-reported and unreliable
- Human evaluation doesn't scale and leaves no record
- Output validation checks the agent's *results* against known-correct constraints deterministically, every run

### What was added

**`agent.py`**
- `validate_schedule(entries, owner, pre_conflict_count)` — runs 4 deterministic checks on the agent's output:
  1. Conflicts resolved (pre vs. post conflict count)
  2. Time budget respected (total scheduled minutes ≤ available)
  3. Required tasks included (all `is_required` tasks present in output)
  4. Valid HH:MM times (regex check on all time strings)
- File logger (`agent_runs.log`) records every run: owner, conflicts before, adjustments made, tasks scheduled, validation pass/fail for each check
- `run_scheduling_agent` now returns a 3-tuple: `(explanation, entries, validation)`
- Adjustment tracking: when `adjust_task_time` succeeds, the moved task is recorded and included in the log

**`app.py`**
- Unpacks the new 3-tuple return value
- Renders a "Reliability Checks" section below the schedule showing ✅/❌ for each check with detail text
- Pass count shown as `N/4 checks passed`

**`.gitignore`** — added `agent_runs.log` (runtime file, not source)

**`README.md`** — Testing Summary section rewritten into two layers:
- Layer 1: unit tests (7/7, domain logic, no API)
- Layer 2: AI output validation (4 checks, live every agent run), with example log output

---

## Session 5 — Responsible AI reflection (model_card.md)

Created `model_card.md` with four short, natural-language answers:
- **Limitations/biases** — agent reasons from task labels not real veterinary knowledge; conflict detection misses duration-based overlaps; required tasks can have their times moved even if time-sensitive
- **Misuse** — low risk for a pet app, but the agent can shift health task times without knowing the stakes; key prevention is `.env` / git-ignore for the API key, and a future time-lock for medication tasks
- **Testing surprise** — the "required tasks included" validation check caught a task silently dropped when the time budget ran out, which would have been invisible otherwise
- **AI collaboration** — helpful: lazy client init fix caught at import time; flawed: numbered step prompts caused Gemini to skip conflict-checking steps, fixed by rewriting the prompt more directively

Added a "Responsible AI" section to `README.md` pointing to `model_card.md`, and added `model_card.md` to the project structure table.

*Log will be updated as work continues.*
