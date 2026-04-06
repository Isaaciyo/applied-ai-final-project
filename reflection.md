# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- add a pet
- schedule a walk
- see today's tasks


- Owner: This holds the pet owner's name, daily time budget, and preferences. It is responsible for managing the list of associated pets and updating availability.
- Pet: This stores the animal's name, species, age, and any special needs. It is responsible for identifying which tasks are required based on those needs.
- Task: This represents a single care activity (e.g., walk, feeding, medication). It holds the title, duration, priority level, category, and whether it is required. It is responsible for determining whether it can fit within a given time budget.
- Schedule: This is the output of the planning process. It holds an ordered list of chosen tasks, the total time used, and an explanation of the plan. It is responsible for formatting the plan for display.
- Scheduler: This is the logic engine. It takes an Owner, a Pet, and a list of Tasks, and is responsible for selecting and ordering tasks into a Schedule based on priority and available time.

**b. Design changes**

Yes, three changes were made after reviewing the initial skeleton:

1. Removed `Schedule.total_duration` attribute. The original design had both a `total_duration` attribute (updated by `add_task`) and a `total_time()` method (recalculated from `self.tasks`). These were redundant and could drift out of sync if `add_task` was ever called inconsistently. The attribute was removed so `total_time()` is the single source of truth.

2. Removed `available_minutes` parameter from `Scheduler.generate()`. The scheduler already holds a reference to `Owner`, which stores `available_minutes`. Passing it again as a parameter meant two values could conflict. The parameter was dropped so `generate()` always reads from `self.owner.available_minutes`.

3. Tightened `Pet.special_needs` type hint to `list[str]`. The original `list` type was ambiguous, and it was unclear whether the list held strings or `Task` objects. Clarifying it as `list[str]` makes the intent explicit: `special_needs` stores task name labels, and the `Scheduler` is responsible for matching those labels against `available_tasks` when building the plan.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
