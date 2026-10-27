import streamlit as st
from datetime import date

st.set_page_config(page_title="Intelligent Task Prioritization Agent", page_icon="🎯", layout="wide")
st.title("🎯 Intelligent Task Prioritization Agent")
st.caption("Plan smarter • Prioritize deadlines • Take the next step")
st.info("This prototype uses transparent rule-based scoring based on deadline urgency, importance and estimated effort. It is not a trained machine-learning model.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "next_id" not in st.session_state:
    st.session_state.next_id = 1

def score(task):
    days = (task["deadline"] - date.today()).days
    urgency = 50 if days < 0 else 45 if days == 0 else 38 if days == 1 else 30 if days <= 3 else 20 if days <= 7 else 10
    return round(urgency + task["importance"] * 10 + max(0, 10 - min(task["hours"], 10)))

def add_task(name, deadline, importance, hours):
    st.session_state.tasks.append({"id": st.session_state.next_id, "name": name.strip(), "deadline": deadline,
                                   "importance": importance, "hours": float(hours), "status": "Pending"})
    st.session_state.next_id += 1

with st.sidebar:
    st.header("➕ Add a task")
    with st.form("add_task_form", clear_on_submit=True):
        name = st.text_input("Task name", placeholder="e.g., Complete OS assignment")
        deadline = st.date_input("Deadline", value=date.today())
        importance_label = st.selectbox("Importance", ["Low", "Medium", "High"], index=2)
        hours = st.number_input("Estimated hours", min_value=0.5, max_value=200.0, value=2.0, step=0.5)
        submitted = st.form_submit_button("Add task", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Please enter a task name.")
        else:
            add_task(name, deadline, {"Low": 1, "Medium": 2, "High": 3}[importance_label], hours)
            st.success("Task added.")
            st.rerun()
    st.divider()
    if st.button("Load demo tasks", use_container_width=True):
        for item in [("Complete OS assignment", date.today(), 3, 2.5),
                     ("Prepare for DSA test", date.today(), 3, 3),
                     ("Finish Java lab record", date.today(), 2, 1.5),
                     ("Read AI symposium notes", date.today(), 1, 1)]:
            add_task(*item)
        st.rerun()
    if st.button("Clear all tasks", use_container_width=True):
        st.session_state.tasks = []
        st.rerun()

st.subheader("📋 Your task list")
if not st.session_state.tasks:
    st.write("Add a task in the sidebar or click **Load demo tasks**.")
else:
    tasks = sorted(st.session_state.tasks, key=lambda t: (t["status"] == "Completed", -score(t)))
    names = {1: "Low", 2: "Medium", 3: "High"}
    st.dataframe([{"Task": t["name"], "Deadline": t["deadline"].isoformat(), "Importance": names[t["importance"]],
                   "Estimated hours": t["hours"], "Priority score": score(t), "Status": t["status"]} for t in tasks],
                 use_container_width=True, hide_index=True)
    pending = sorted([t for t in st.session_state.tasks if t["status"] == "Pending"], key=lambda t: -score(t))
    completed = [t for t in st.session_state.tasks if t["status"] == "Completed"]
    a, b, c = st.columns(3)
    a.metric("Total tasks", len(st.session_state.tasks))
    b.metric("Pending", len(pending))
    c.metric("Completed", len(completed))
    st.subheader("🧭 Recommended action plan")
    if pending:
        for i, t in enumerate(pending, 1):
            days = (t["deadline"] - date.today()).days
            due = f"Overdue by {abs(days)} day(s)" if days < 0 else "Due today" if days == 0 else "Due tomorrow" if days == 1 else f"Due in {days} day(s)"
            st.markdown(f"**{i}. {t['name']}** — score `{score(t)}` · {due} · about {t['hours']:g} hour(s)")
        st.caption(f"Total estimated pending work: {sum(t['hours'] for t in pending):g} hours.")
    else:
        st.success("All tasks are completed!")
    st.subheader("✅ Update task status")
    pending_options = {f'{t["name"]} (ID {t["id"]})': t["id"] for t in st.session_state.tasks if t["status"] == "Pending"}
    completed_options = {f'{t["name"]} (ID {t["id"]})': t["id"] for t in st.session_state.tasks if t["status"] == "Completed"}
    left, right = st.columns(2)
    with left:
        if pending_options:
            choice = st.selectbox("Select a pending task", list(pending_options), key="pending")
            if st.button("Mark as completed"):
                for t in st.session_state.tasks:
                    if t["id"] == pending_options[choice]: t["status"] = "Completed"
                st.rerun()
    with right:
        if completed_options:
            choice2 = st.selectbox("Select a completed task", list(completed_options), key="completed")
            if st.button("Mark as pending"):
                for t in st.session_state.tasks:
                    if t["id"] == completed_options[choice2]: t["status"] = "Pending"
                st.rerun()

st.divider()
st.caption("Symposium prototype. Tasks are kept in the current browser session and may reset when the session restarts.")
