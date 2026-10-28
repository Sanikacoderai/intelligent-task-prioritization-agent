
import os
from datetime import date, timedelta

import streamlit as st


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Intelligent Task Prioritization Agent",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Intelligent Task Prioritization Agent")
st.caption("Plan smarter • Prioritize deadlines • Take the next step")

st.info(
    "This app uses transparent rules to prioritize your tasks "
    "and optional Groq AI to generate a personalized action plan."
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "next_id" not in st.session_state:
    st.session_state.next_id = 1


# --------------------------------------------------
# PRIORITY CALCULATION
# --------------------------------------------------

def score(task):
    """Calculate a transparent rule-based priority score."""

    days_left = (task["deadline"] - date.today()).days

    if days_left < 0:
        urgency = 50
    elif days_left == 0:
        urgency = 45
    elif days_left == 1:
        urgency = 38
    elif days_left <= 3:
        urgency = 30
    elif days_left <= 7:
        urgency = 20
    else:
        urgency = 10

    importance_bonus = task["importance"] * 10
    effort_bonus = max(0, 10 - min(task["hours"], 10))

    return round(urgency + importance_bonus + effort_bonus)


def days_remaining(task):
    return (task["deadline"] - date.today()).days


def get_pending_tasks():
    return [
        task
        for task in st.session_state.tasks
        if task["status"] == "Pending"
    ]


# --------------------------------------------------
# TASK MANAGEMENT
# --------------------------------------------------

def add_task(name, deadline, importance, hours):
    task = {
        "id": st.session_state.next_id,
        "name": name.strip(),
        "deadline": deadline,
        "importance": importance,
        "hours": float(hours),
        "status": "Pending",
    }

    st.session_state.tasks.append(task)
    st.session_state.next_id += 1


def load_demo_tasks():
    today = date.today()

    demo_tasks = [
        {
            "name": "Complete DSA assignment",
            "deadline": today + timedelta(days=1),
            "importance": 3,
            "hours": 2.0,
        },
        {
            "name": "Prepare for OS test",
            "deadline": today + timedelta(days=3),
            "importance": 3,
            "hours": 4.0,
        },
        {
            "name": "Revise Python concepts",
            "deadline": today + timedelta(days=5),
            "importance": 2,
            "hours": 2.0,
        },
    ]

    for item in demo_tasks:
        add_task(
            item["name"],
            item["deadline"],
            item["importance"],
            item["hours"],
        )


# --------------------------------------------------
# GROQ API KEY
# --------------------------------------------------

def get_groq_api_key():
    """Read the API key from Streamlit Secrets or environment."""

    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        key = ""

    if not key:
        key = os.environ.get("GROQ_API_KEY", "")

    return key.strip() if key else ""


# --------------------------------------------------
# GROQ AI ACTION PLAN
# --------------------------------------------------

def generate_ai_plan(tasks, user_context):
    api_key = get_groq_api_key()

    if not api_key:
        st.warning(
            "Groq AI is not configured. Add GROQ_API_KEY "
            "to this test app's Streamlit Secrets. "
            "Your normal task features will continue to work."
        )
        return

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        task_details = []

        for task in tasks:
            task_details.append({
                "task": task["name"],
                "deadline": task["deadline"].isoformat(),
                "days_until_deadline": days_remaining(task),
                "importance": {
                    1: "Low",
                    2: "Medium",
                    3: "High",
                }[task["importance"]],
                "estimated_hours": task["hours"],
                "rule_based_priority_score": score(task),
            })

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful student task-planning assistant. "
                        "Create a realistic, student-friendly action plan "
                        "using only the supplied tasks. Prioritize urgent "
                        "deadlines, importance, and estimated effort. "
                        "Explain why tasks should be done in that order. "
                        "Suggest manageable work sessions and short breaks. "
                        "Include practical first steps and a suggested "
                        "schedule. Do not invent tasks or change the "
                        "provided priority scores. If a deadline has passed, "
                        "identify it as overdue. The student makes the "
                        "final decisions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Today's date: {date.today().isoformat()}\n\n"
                        f"Pending tasks: {task_details}\n\n"
                        f"Additional student context: "
                        f"{user_context or 'None provided.'}\n\n"
                        "Generate a prioritized action plan with clear "
                        "reasons, first steps, and a realistic schedule."
                    ),
                },
            ],
            temperature=0.3,
            max_completion_tokens=900,
        )

        plan = response.choices[0].message.content

        if plan and plan.strip():
            st.markdown(plan)
        else:
            st.warning(
                "The AI returned an empty response. Please try again."
            )

    except Exception as error:
        # Avoid accidentally displaying the API key in error output.
        error_message = str(error).replace(api_key, "[REDACTED]")

        # Print diagnostic details to the test app's Cloud logs.
        print(
            f"GROQ AI ERROR: {type(error).__name__}: {error_message}"
        )

        st.error(
            f"Groq AI error ({type(error).__name__}): "
            f"{error_message}"
        )

        st.caption(
            "Your existing task features remain available. "
            "Check the Cloud logs for diagnostic details."
        )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.header("➕ Add a Task")

    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input(
            "Task name",
            placeholder="e.g. Complete DSA assignment",
        )

        deadline = st.date_input(
            "Deadline",
            value=date.today() + timedelta(days=1),
        )

        importance = st.select_slider(
            "Importance",
            options=[1, 2, 3],
            value=2,
            format_func=lambda value: {
                1: "Low",
                2: "Medium",
                3: "High",
            }[value],
        )

        hours = st.number_input(
            "Estimated hours",
            min_value=0.5,
            max_value=100.0,
            value=2.0,
            step=0.5,
        )

        submitted = st.form_submit_button(
            "Add Task",
            width="stretch",
        )

        if submitted:
            if task_name.strip():
                add_task(
                    task_name,
                    deadline,
                    importance,
                    hours,
                )
                st.success("Task added successfully!")
            else:
                st.warning("Please enter a task name.")

    st.divider()

    st.subheader("🧪 Testing")

    if st.button("Load Demo Tasks", width="stretch"):
        load_demo_tasks()
        st.success("Demo tasks added!")

    if st.button("Clear All Tasks", width="stretch"):
        st.session_state.tasks = []
        st.success("All tasks cleared!")


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------

all_tasks = st.session_state.tasks
pending_tasks = get_pending_tasks()
completed_tasks = [
    task for task in all_tasks
    if task["status"] == "Completed"
]

overdue_tasks = [
    task for task in pending_tasks
    if days_remaining(task) < 0
]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tasks", len(all_tasks))
col2.metric("Pending", len(pending_tasks))
col3.metric("Completed", len(completed_tasks))
col4.metric("Overdue", len(overdue_tasks))

st.divider()


# --------------------------------------------------
# TASK LIST
# --------------------------------------------------

st.subheader("📋 Your Tasks")

if not all_tasks:
    st.info(
        "No tasks yet. Add a task using the sidebar "
        "or click 'Load Demo Tasks' to try the app."
    )

else:
    sorted_tasks = sorted(
        all_tasks,
        key=lambda task: (
            task["status"] == "Completed",
            -score(task),
        ),
    )

    for task in sorted_tasks:
        task_col1, task_col2, task_col3 = st.columns(
            [5, 2, 1]
        )

        days = days_remaining(task)

        with task_col1:
            st.markdown(f"**{task['name']}**")

            if days < 0:
                deadline_text = f"Overdue by {abs(days)} day(s)"
            elif days == 0:
                deadline_text = "Due today"
            elif days == 1:
                deadline_text = "Due tomorrow"
            else:
                deadline_text = f"Due in {days} days"

            st.caption(
                f"Deadline: {task['deadline'].isoformat()} · "
                f"{deadline_text} · "
                f"Importance: {task['importance']}/3 · "
                f"Effort: {task['hours']:g} hour(s)"
            )

        with task_col2:
            st.metric(
                "Priority score",
                score(task),
            )

        with task_col3:
            if task["status"] == "Pending":
                if st.button(
                    "Complete",
                    key=f"complete_{task['id']}",
                ):
                    task["status"] = "Completed"
                    st.rerun()
            else:
                if st.button(
                    "Reopen",
                    key=f"reopen_{task['id']}",
                ):
                    task["status"] = "Pending"
                    st.rerun()

        st.divider()


# --------------------------------------------------
# RULE-BASED RECOMMENDATIONS
# --------------------------------------------------

st.subheader("🧠 Rule-Based Recommendations")

if pending_tasks:
    ranked_tasks = sorted(
        pending_tasks,
        key=lambda task: score(task),
        reverse=True,
    )

    st.write(
        "Based on deadline, importance, and estimated effort, "
        "here is your recommended task order:"
    )

    for index, task in enumerate(ranked_tasks, start=1):
        days = days_remaining(task)

        if days < 0:
            deadline_label = f"Overdue by {abs(days)} day(s)"
        elif days == 0:
            deadline_label = "Due today"
        else:
            deadline_label = f"{days} day(s) remaining"

        st.markdown(
            f"**{index}. {task['name']}** — "
            f"Score: {score(task)} · {deadline_label}"
        )

else:
    st.info("No pending tasks to prioritize.")


# --------------------------------------------------
# AI ACTION PLAN
# --------------------------------------------------

st.divider()
st.subheader("✨ AI-Powered Action Plan")

st.write(
    "Generate a personalized schedule using Groq AI "
    "and your current pending tasks."
)

user_context = st.text_area(
    "Additional context (optional)",
    placeholder=(
        "Example: I have a college exam tomorrow, "
        "and I can study for 3 hours today."
    ),
)

if st.button(
    "✨ Generate AI action plan",
    type="primary",
    width="stretch",
):
    if not pending_tasks:
        st.warning(
            "Add at least one pending task before generating an AI plan."
        )
    else:
        with st.spinner("Creating your personalized action plan..."):
            generate_ai_plan(
                sorted(
                    pending_tasks,
                    key=lambda task: score(task),
                    reverse=True,
                ),
                user_context.strip(),
            )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Priority scores are rule-based estimates. "
    "AI suggestions may need adjustment. "
    "Review the plan and make decisions that fit your schedule."
)
