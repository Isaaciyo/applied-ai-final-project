import os
import json
import re
import logging
from google import genai
from google.genai import types
from pawpal_system import Owner, Scheduler

logging.basicConfig(
    filename="agent_runs.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are PawPal+, an intelligent pet care scheduling assistant.

Your job is to build an optimized daily care schedule for a pet owner. You will:
1. Call list_tasks to see all pets and tasks.
2. Call detect_conflicts to check for time-slot collisions.
3. If conflicts exist, resolve them by calling adjust_task_time to move one of the conflicting tasks to a nearby free slot. Use your judgment — consider the task category and priority when deciding which task to move and where.
4. Call generate_schedule to produce the final schedule.
5. Reply with a concise, friendly explanation of what you scheduled, what conflicts (if any) you resolved, and why you made the choices you did.

Be practical and brief. The owner is busy."""

TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="list_tasks",
        description="Returns all (pet, task) pairs registered with the owner, including time, duration, priority, and required status.",
        parameters={"type": "object", "properties": {}},
    ),
    types.FunctionDeclaration(
        name="detect_conflicts",
        description="Returns a list of warning strings for any time slots shared by two or more tasks. Empty list means no conflicts.",
        parameters={"type": "object", "properties": {}},
    ),
    types.FunctionDeclaration(
        name="adjust_task_time",
        description="Move a specific task to a new HH:MM time slot to resolve a scheduling conflict.",
        parameters={
            "type": "object",
            "properties": {
                "pet_name": {"type": "string", "description": "Name of the pet the task belongs to."},
                "task_title": {"type": "string", "description": "Exact title of the task to move."},
                "new_time": {"type": "string", "description": "New time in HH:MM format."},
            },
            "required": ["pet_name", "task_title", "new_time"],
        },
    ),
    types.FunctionDeclaration(
        name="generate_schedule",
        description="Run the priority-based greedy scheduler and return the final schedule entries and total time used.",
        parameters={"type": "object", "properties": {}},
    ),
])


def _list_tasks(owner: Owner) -> str:
    rows = []
    for pet, task in owner.get_all_tasks():
        rows.append({
            "pet": pet.name,
            "task": task.title,
            "time": task.time,
            "duration_min": task.duration_minutes,
            "priority": task.priority,
            "required": task.is_required,
            "category": task.category,
        })
    return json.dumps(rows)


def _detect_conflicts(owner: Owner) -> str:
    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()
    return json.dumps(warnings if warnings else [])


def _adjust_task_time(owner: Owner, pet_name: str, task_title: str, new_time: str) -> str:
    for pet in owner.pets:
        if pet.name.lower() == pet_name.lower():
            for task in pet.tasks:
                if task.title.lower() == task_title.lower():
                    old_time = task.time
                    task.time = new_time
                    return json.dumps({"status": "ok", "moved": f"{task_title} from {old_time} to {new_time}"})
    return json.dumps({"status": "error", "message": f"Task '{task_title}' for pet '{pet_name}' not found."})


def _generate_schedule(owner: Owner) -> str:
    scheduler = Scheduler(owner)
    schedule = scheduler.generate()
    entries = [
        {
            "pet": pet.name,
            "task": task.title,
            "time": task.time,
            "duration_min": task.duration_minutes,
            "priority": task.priority,
            "required": task.is_required,
        }
        for pet, task in scheduler.sort_by_time(schedule.entries)
    ]
    return json.dumps({
        "entries": entries,
        "total_minutes": schedule.total_time(),
        "available_minutes": owner.available_minutes,
        "remaining_minutes": owner.available_minutes - schedule.total_time(),
    })


def _dispatch(tool_name: str, tool_input: dict, owner: Owner) -> str:
    if tool_name == "list_tasks":
        return _list_tasks(owner)
    if tool_name == "detect_conflicts":
        return _detect_conflicts(owner)
    if tool_name == "adjust_task_time":
        return _adjust_task_time(owner, **tool_input)
    if tool_name == "generate_schedule":
        return _generate_schedule(owner)
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def validate_schedule(entries: list[dict], owner: Owner, pre_conflict_count: int) -> list[dict]:
    """Run four deterministic checks on the agent's output. Returns a list of pass/fail results."""
    checks = []

    # 1. Conflicts resolved
    remaining = Scheduler(owner).detect_conflicts()
    checks.append({
        "check": "Conflicts resolved",
        "passed": len(remaining) == 0,
        "detail": f"{pre_conflict_count} found before agent, {len(remaining)} remaining after",
    })

    # 2. Time budget respected
    total = sum(e["duration_min"] for e in entries)
    checks.append({
        "check": "Time budget respected",
        "passed": total <= owner.available_minutes,
        "detail": f"{total} min used of {owner.available_minutes} available",
    })

    # 3. All required tasks scheduled
    required = [
        (pet.name, task.title)
        for pet in owner.pets
        for task in pet.tasks
        if task.is_required
    ]
    scheduled = {(e["pet"], e["task"]) for e in entries}
    missing = [(p, t) for p, t in required if (p, t) not in scheduled]
    checks.append({
        "check": "Required tasks included",
        "passed": len(missing) == 0,
        "detail": (
            "All required tasks scheduled"
            if not missing
            else f"Missing: {', '.join(f'[{p}] {t}' for p, t in missing)}"
        ),
    })

    # 4. Valid HH:MM times
    invalid_times = [e["time"] for e in entries if not re.match(r"^\d{2}:\d{2}$", e["time"])]
    checks.append({
        "check": "Valid HH:MM times",
        "passed": len(invalid_times) == 0,
        "detail": "All times valid" if not invalid_times else f"Invalid: {invalid_times}",
    })

    return checks


def run_scheduling_agent(owner: Owner) -> tuple[str, list[dict], list[dict]]:
    """
    Run the multi-step scheduling agent for the given owner.
    Returns (explanation_text, final_schedule_entries, validation_results).
    """
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    pre_conflicts = Scheduler(owner).detect_conflicts()
    adjustments = []

    logger.info(
        f"Agent run started | owner={owner.name!r} | "
        f"pets={[p.name for p in owner.pets]} | "
        f"conflicts_before={len(pre_conflicts)}"
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOLS],
    )
    chat = client.chats.create(model="gemini-2.5-flash", config=config)
    response = chat.send_message("Please build today's schedule for my pets.")

    final_schedule = []
    explanation = ""

    try:
        while True:
            if not response.candidates:
                break

            parts = response.candidates[0].content.parts
            function_calls = [p.function_call for p in parts if p.function_call]
            text_parts = [p.text for p in parts if p.text]

            if text_parts:
                explanation = "".join(text_parts)

            if not function_calls:
                break

            response_parts = []
            for fc in function_calls:
                result_str = _dispatch(fc.name, dict(fc.args), owner)

                if fc.name == "generate_schedule":
                    data = json.loads(result_str)
                    final_schedule = data.get("entries", [])

                if fc.name == "adjust_task_time":
                    result_data = json.loads(result_str)
                    if result_data.get("status") == "ok":
                        adjustments.append(result_data["moved"])
                    else:
                        logger.warning(f"adjust_task_time failed: {result_data.get('message')}")

                response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": result_str},
                        )
                    )
                )

            response = chat.send_message(response_parts)

    except Exception as e:
        logger.error(f"Agent error | owner={owner.name!r} | error={e}")
        raise

    validation = validate_schedule(final_schedule, owner, len(pre_conflicts))
    passed = sum(1 for c in validation if c["passed"])

    logger.info(
        f"Agent run complete | owner={owner.name!r} | "
        f"adjustments={adjustments} | tasks_scheduled={len(final_schedule)} | "
        f"validation={passed}/{len(validation)} checks passed"
    )
    for check in validation:
        status = "PASS" if check["passed"] else "FAIL"
        logger.info(f"  [{status}] {check['check']}: {check['detail']}")

    return explanation, final_schedule, validation
