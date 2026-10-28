
import os
from datetime import date

import streamlit as st

st.set_page_config(
    page_title="Intelligent Task Prioritization Agent",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Intelligent Task Prioritization Agent")
st.caption("Plan smarter • Prioritize deadlines • Take the next step")
st.info(
    "Priority scores are calculated using transparent rules. "
    "The optional Groq AI feature explains priorities and suggests an action plan."
)

# Store tasks in the current browser session.
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "next_id" not in st.session_state:
    st.session_state.next_id = 1


def score(task):
    days = (task["deadline"] - date.today()).days

    urgency = (
        50 if days < 0
        else 45 if days == 0
        else 38 if days == 1
        else 30 if days <= 3
        else 20 if days <= 7
        else 10
    )

    effort_bonus = max(0, 10 - min(task["hours"], 10))
    return round(urgency + task["importance"] * 10 + effort_bonus)


def add_task(name, deadline, importance, hours):
    st.session_state.tasks.append({
        "id": st.session_state.next_id,
        "name": name.strip(),
        "deadline": deadline,
        "importance": importance,
        "hours": float(hours),
        "status": "Pending",
    })
    st.session_state.next_id += 1


def get_groq_api_key():
    # Read the key from Streamlit Secrets or an environment variable.
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        key = ""

    return key or os.environ.get("GROQ_API_KEY", "")


def generate_ai_plan(tasks, user_context):
    api_key = get_groq_api_key()

    if not api_key:
        st.warning(
            "Groq AI is not configured yet. Your normal task-prioritization "
            "features still work. Add GROQ_API_KEY in your app's Secrets settings."
        )
        return

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        task_details = []
        for task in tasks:
            days = (task["deadline"] - date.today()).days

            task_details.append({
                "task": task["name"],
                "deadline": task["deadline"].isoformat(),
                "days_until_deadline": days,
                "importance": {
                    1: "Low",
                    2: "Medium",
                    3: "High",
                }[task["importance"]],
                "estimated_hours": task["hours"],
                "rule_based_priority_score": score(task),
            })

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful student task-planning assistant. "
                        "Use the supplied task information to recommend a "
                        "realistic action plan. Respect deadlines, importance, "
                        "priority scores and estimated effort. Explain why "
                        "each task should be done when recommended. Suggest "
                        "manageable work sessions and breaks. Do not invent "
                        "tasks or change the supplied priority scores. "
                        "Keep the answer clear and student-friendly. "
                        "The user makes the final decisions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Today's date: {date.today().isoformat()}\n"
                        f"Pending tasks: {task_details}\n"
                        f"Additional context from the student: "
                        f"{user_context or 'No additional context provided.'}\n\n"
                        "Create a prioritized action plan with reasons, "
                        "suggested first steps and a realistic schedule."
                    ),
                },
            ],
            temperature=0.3,
            max_completion_tokens=900,
        )

        plan = response.choices[0].message.content

        if plan:
            st.markdown(plan)
        else:
            st.warning("The AI returned an empty response. Please try again.")
        
        except Exception as e:
    import traceback
    print("GROQ AI ERROR:", traceback.format_exc())
    st.error(f"Groq AI error: {type(e).__name__}: {e}")


with st.sidebar:
    st.header("➕ Add a task")

    with st.form("add_task_form", clear_on_submit=True):
        name = st.text_input(
            "Task name",
            placeholder="e.g., Complete OS assignment",
        )
        deadline = st.date_input("Deadline", value=date.today())
        importance_label = st.selectbox(
            "Importance",
            ["Low", "Medium", "High"],
            index=2,
        )
        hours = st.number_input(
            "Estimated hours",
            min_value=0.5,
            max_value=200.0,
            value=2.0,
            step=0.5,
        )
        submitted = st.form_submit_button(
            "Add task",
            use_container_width=True,
        )

    if submitted:
        if not name.strip():
            st.error("Please enter a task name.")
        else:
            add_task(
                name,
                deadline,
                {"Low": 1, "Medium": 2, "High": 3}[importance_label],
                hours,
            )
            st.success("Task added.")
            st.rerun()

    st.divider()

    if st.button("Load demo tasks", use_container_width=True):
        for item in [
            ("Complete OS assignment", date.today(), 3, 2.5),
            ("Prepare for DSA test", date.today(), 3, 3),
            ("Finish Java lab record", date.today(), 2, 1.5),
            ("Read AI symposium notes", date.today(), 1, 1),
        ]:
            add_task(*item)
        st.rerun()

    if st.button("Clear all tasks", use_container_width=True):
        st.session_state.tasks = []
        st.rerun()


st.subheader("📋 Your task list")

if not st.session_state.tasks:
    st.write("Add a task in the sidebar or click **Load demo tasks**.")
else:
    tasks = sorted(
        st.session_state.tasks,
        key=lambda task: (
            task["status"] == "Completed",
            -score(task),
        ),
    )

    importance_names = {1: "Low", 2: "Medium", 3: "High"}

    st.dataframe(
        [
            {
                "Task": task["name"],
                "Deadline": task["deadline"].isoformat(),
                "Importance": importance_names[task["importance"]],
                "Estimated hours": task["hours"],
                "Priority score": score(task),
                "Status": task["status"],
            }
            for task in tasks
        ],
        use_container_width=True,
        hide_index=True,
    )

    pending = sorted(
        [
            task for task in st.session_state.tasks
            if task["status"] == "Pending"
        ],
        key=lambda task: -score(task),
    )

    completed = [
        task for task in st.session_state.tasks
        if task["status"] == "Completed"
    ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total tasks", len(st.session_state.tasks))
    col2.metric("Pending", len(pending))
    col3.metric("Completed", len(completed))

    st.subheader("🧭 Recommended action plan")

    if pending:
        for index, task in enumerate(pending, 1):
            days = (task["deadline"] - date.today()).days

            due = (
                f"Overdue by {abs(days)} day(s)" if days < 0
                else "Due today" if days == 0
                else "Due tomorrow" if days == 1
                else f"Due in {days} day(s)"
            )

            st.markdown(
                f"**{index}. {task['name']}** — "
                f"score `{score(task)}` · {due} · "
                f"about {task['hours']:g} hour(s)"
            )

        st.caption(
            f"Total estimated pending work: "
            f"{sum(task['hours'] for task in pending):g} hours."
        )
    else:
        st.success("All tasks are completed!")

    # Optional AI-enhanced plan.
    st.divider()
    st.subheader("🤖 Groq AI action plan")
    st.write(
        "Get an AI-generated explanation and a practical plan based "
        "on your pending tasks. Your rule-based scores remain unchanged."
    )

    user_context = st.text_area(
        "Your available study time or other preferences (optional)",
        placeholder="e.g., I have 3 hours free today and a DSA test tomorrow.",
    )

    if st.button(
        "✨ Generate AI action plan",
        type="primary",
        disabled=not pending,
    ):
        with st.spinner("Groq AI is preparing your plan..."):
            generate_ai_plan(pending, user_context)

    st.subheader("✅ Update task status")

    pending_options = {
        f'{task["name"]} (ID {task["id"]})': task["id"]
        for task in st.session_state.tasks
        if task["status"] == "Pending"
    }

    completed_options = {
        f'{task["name"]} (ID {task["id"]})': task["id"]
        for task in st.session_state.tasks
        if task["status"] == "Completed"
    }

    left, right = st.columns(2)

    with left:
        if pending_options:
            choice = st.selectbox(
                "Select a pending task",
                list(pending_options),
                key="pending",
            )

            if st.button("Mark as completed"):
                for task in st.session_state.tasks:
                    if task["id"] == pending_options[choice]:
                        task["status"] = "Completed"
                st.rerun()

    with right:
        if completed_options:
            choice2 = st.selectbox(
                "Select a completed task",
                list(completed_options),
                key="completed",
            )

            if st.button("Mark as pending"):
                for task in st.session_state.tasks:
                    if task["id"] == completed_options[choice2]:
                        task["status"] = "Pending"
                st.rerun()


st.divider()
st.caption(
    "Symposium prototype. Tasks are kept in the current browser session "
    "and may reset when the session restarts."
)
