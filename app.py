import os
import streamlit as st
from dotenv import load_dotenv
from pawpal_system import Owner, Pet, Task, Scheduler
from agent import run_scheduling_agent

load_dotenv()

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state init ────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None

# ── Section 1: Owner setup ────────────────────────────────────────────────────
st.subheader("1. Owner Info")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value="Jordan")
with col2:
    available_minutes = st.number_input("Time available today (min)", min_value=10, max_value=480, value=90)

if st.button("Save owner"):
    if st.session_state.owner is None:
        # Owner.set_availability() and __init__ handle initial creation
        st.session_state.owner = Owner(name=owner_name, available_minutes=available_minutes)
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.set_availability(available_minutes)   # <-- Owner.set_availability()
    st.success(f"Owner '{owner_name}' saved with {available_minutes} min available.")

st.divider()

# ── Section 2: Add a Pet ──────────────────────────────────────────────────────
# Answers the question: owner.add_pet(pet) handles the data.
# The UI updates because st.session_state.owner.pets grows, and Streamlit
# reruns the script — the pet selector below reflects the new list immediately.
st.subheader("2. Add a Pet")
if st.session_state.owner is None:
    st.info("Save an owner first.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

    if st.button("Add pet"):
        pet = Pet(name=pet_name, species=species, age=pet_age)
        st.session_state.owner.add_pet(pet)          # <-- Owner.add_pet()
        st.success(f"Added {pet_name} the {species}!")

    # Show all pets registered so far
    if st.session_state.owner.pets:
        st.markdown("**Registered pets:**")
        st.table([
            {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
            for p in st.session_state.owner.pets
        ])

st.divider()

# ── Section 3: Add a Task ─────────────────────────────────────────────────────
st.subheader("3. Add a Task")
if not st.session_state.owner or not st.session_state.owner.pets:
    st.info("Add at least one pet first.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)
    selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        task_time = st.text_input("Time (HH:MM)", value="08:00")

    is_required = st.checkbox("Required task?")

    if st.button("Add task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category="general",
            is_required=is_required,
            time=task_time,
        )
        selected_pet.add_task(task)                  # <-- Pet.add_task()
        st.success(f"Added '{task_title}' to {selected_pet.name}.")

    # Show tasks for the selected pet, sorted chronologically via Scheduler.sort_by_time()
    if selected_pet.tasks:
        scheduler = Scheduler(st.session_state.owner)
        sorted_pairs = scheduler.sort_by_time(
            [(selected_pet, t) for t in selected_pet.tasks]
        )
        st.markdown(f"**{selected_pet.name}'s tasks (sorted by time):**")
        st.table([
            {
                "Time": t.time,
                "Task": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Required": "Yes" if t.is_required else "No",
                "Done": "✓" if t.completed else "—",
            }
            for _, t in sorted_pairs
        ])

st.divider()

# ── Section 4: Generate Schedule ─────────────────────────────────────────────
st.subheader("4. Today's Schedule")

def _has_tasks():
    return (
        st.session_state.owner is not None
        and st.session_state.owner.pets
        and any(p.tasks for p in st.session_state.owner.pets)
    )

col_basic, col_ai = st.columns(2)

with col_basic:
    if st.button("Generate schedule", use_container_width=True):
        if st.session_state.owner is None:
            st.warning("Save an owner first.")
        elif not _has_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(st.session_state.owner)

            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.markdown("#### Scheduling Conflicts Detected")
                for warning in conflicts:
                    st.warning(f"**Time conflict** — {warning.replace('WARNING: Scheduling conflict at ', '').replace(' — ', ': ')}\n\nTwo or more tasks are scheduled at the same time. Edit a task's time above to resolve this.")
            else:
                st.success("No scheduling conflicts found.")

            schedule = scheduler.generate()

            if not schedule.entries:
                st.warning("No tasks could fit within your available time budget.")
            else:
                st.markdown(f"#### Plan for {st.session_state.owner.name} — {schedule.date}")
                sorted_entries = scheduler.sort_by_time(schedule.entries)
                st.table([
                    {
                        "Time": task.time,
                        "Pet": pet.name,
                        "Task": task.title,
                        "Duration (min)": task.duration_minutes,
                        "Priority": task.priority,
                        "Required": "Yes" if task.is_required else "No",
                    }
                    for pet, task in sorted_entries
                ])
                total = schedule.total_time()
                budget = st.session_state.owner.available_minutes
                st.info(f"**Total:** {total} min used of {budget} min available ({budget - total} min remaining)\n\n{schedule.explanation}")

with col_ai:
    if st.button("✨ Generate with AI", use_container_width=True):
        if st.session_state.owner is None:
            st.warning("Save an owner first.")
        elif not _has_tasks():
            st.warning("Add at least one task before generating a schedule.")
        elif not os.environ.get("GEMINI_API_KEY"):
            st.error("Set the GEMINI_API_KEY environment variable to use AI scheduling.")
        else:
            with st.spinner("AI is building your schedule..."):
                try:
                    explanation, entries, validation = run_scheduling_agent(st.session_state.owner)
                except Exception as e:
                    st.error(f"Agent error: {e}")
                    entries = []
                    explanation = ""
                    validation = []

            if entries:
                from datetime import date
                st.markdown(f"#### AI Plan for {st.session_state.owner.name} — {date.today()}")
                st.table([
                    {
                        "Time": e["time"],
                        "Pet": e["pet"],
                        "Task": e["task"],
                        "Duration (min)": e["duration_min"],
                        "Priority": e["priority"],
                        "Required": "Yes" if e["required"] else "No",
                    }
                    for e in entries
                ])
                total = sum(e["duration_min"] for e in entries)
                budget = st.session_state.owner.available_minutes
                st.info(f"**Total:** {total} min used of {budget} min available ({budget - total} min remaining)")
                if explanation:
                    st.markdown("#### AI Reasoning")
                    st.write(explanation)

            if validation:
                passed = sum(1 for c in validation if c["passed"])
                st.markdown("#### Reliability Checks")
                st.caption(f"{passed}/{len(validation)} checks passed")
                for check in validation:
                    icon = "✅" if check["passed"] else "❌"
                    st.markdown(f"{icon} **{check['check']}** — {check['detail']}")

            if not entries and explanation:
                st.warning(explanation)
