import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

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

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    is_required = st.checkbox("Required task?")

    if st.button("Add task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category="general",
            is_required=is_required,
        )
        selected_pet.add_task(task)                  # <-- Pet.add_task()
        st.success(f"Added '{task_title}' to {selected_pet.name}.")

    # Show tasks for the selected pet
    if selected_pet.tasks:
        st.markdown(f"**{selected_pet.name}'s tasks:**")
        st.table([
            {
                "Task": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Required": t.is_required,
                "Done": t.completed,
            }
            for t in selected_pet.tasks
        ])

st.divider()

# ── Section 4: Generate Schedule ─────────────────────────────────────────────
st.subheader("4. Today's Schedule")
if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Save an owner first.")
    elif not st.session_state.owner.pets or not any(p.tasks for p in st.session_state.owner.pets):
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)   # <-- Scheduler.generate()
        schedule = scheduler.generate()
        st.success("Schedule generated!")
        st.text(schedule.to_display())
