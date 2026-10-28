
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
    "Manage your tasks, track deadlines, receive in-app reminders, "
    "and generate personalized study plans using Groq AI."
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
    """Calculate a priority score using urgency, importance, and effort."""

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
        task for task in st.session_state.tasks
        if task["status"] == "Pending"
    ]


# --------------------------------------------------
# TASK MANAGEMENT
# --------------------------------------------------

def add_task(name, deadline, importance, hours):
    st.session_state.tasks.append({
        "id": st.session_state.next_id,
        "name": name.strip(),
        "deadline": deadline,
        "importance": importance,
        "hours": float(hours),
        "status": "Pending",
        "reminder_days": 1,
        "reminder_enabled": True,
    })

    st.session_state.next_id += 1


def update_task_deadline(task_id):
    """Save an edited deadline to the correct task."""

    new_deadline = st.session_state[f"deadline_editor_{task_id}"]

    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["deadline"] = new_deadline
            break


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
# GROQ API CONFIGURATION
# --------------------------------------------------

def get_groq_api_key():
    """Read the key from Streamlit Secrets or environment variables."""

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
            "Groq AI is not configured. Add GROQ_API_KEY to the "
            "test app's Streamlit Secrets. Other features will continue "
            "to work."
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
                "priority_score": score(task),
            })

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful student task-planning assistant. "
                        "Create a realistic study and task plan using only "
                        "the supplied tasks. Prioritize deadlines, importance, "
                        "and estimated effort. Explain the order, suggest "
                        "manageable work sessions and short breaks, and give "
                        "practical first steps. Respect the supplied deadlines "
                        "and scores. Identify overdue tasks. The student makes "
                        "the final decisions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Today's date: {date.today().isoformat()}\n\n"
                        f"Pending tasks with current deadlines: "
                        f"{task_details}\n\n"
                        f"Student context: "
                        f"{user_context or 'None provided.'}\n\n"
                        "Create a prioritized action plan with reasons, "
                        "first steps, and a realistic schedule."
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
            st.warning("The AI returned an empty response. Please try again.")

    except Exception as error:
        error_message = str(error).replace(api_key, "[REDACTED]")

        print(
            f"GROQ AI ERROR: {type(error).__name__}: {error_message}"
        )

        st.error(
            f"Groq AI error ({type(error).__name__}): {error_message}"
        )

        st.caption(
            "Your other task features remain available. "
            "Check the Streamlit Cloud logs for details."
        )


# --------------------------------------------------
# SIDEBAR: ADD TASK
# --------------------------------------------------

with st.sidebar:
    st.header("➕ Add a Task")

    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input(
            "Task name",
            placeholder="e.g. Prepare for internal exam",
        )

        deadline = st.date_input(
            "Deadline",
            value=date.today() + timedelta(days=1),
            min_value=date(1900, 1, 1),
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
        st.rerun()


# --------------------------------------------------
# SMART PRODUCTIVITY DASHBOARD
# --------------------------------------------------

st.subheader("📊 Smart Productivity Dashboard")

all_tasks = st.session_state.tasks

total_tasks = len(all_tasks)

completed_tasks = [
    task for task in all_tasks
    if task["status"] == "Completed"
]

pending_tasks = [
    task for task in all_tasks
    if task["status"] == "Pending"
]

overdue_tasks = [
    task for task in pending_tasks
    if days_remaining(task) < 0
]

completion_rate = (
    len(completed_tasks) / total_tasks
    if total_tasks > 0
    else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("📝 Total Tasks", total_tasks)
col2.metric("⏳ Pending", len(pending_tasks))
col3.metric("✅ Completed", len(completed_tasks))
col4.metric("🚨 Overdue", len(overdue_tasks))

st.markdown("### 🎯 Overall Completion Progress")

st.progress(
    completion_rate,
    text=f"{completion_rate * 100:.1f}% completed",
)

if total_tasks == 0:
    st.info("Add a task to start tracking your productivity.")
elif completion_rate == 1:
    st.success("Amazing! You have completed every task! 🎉")
elif overdue_tasks:
    st.warning(
        f"You have {len(overdue_tasks)} overdue task(s). "
        "Consider reviewing these first."
    )
else:
    st.success("Keep going! You're making progress. 💪")

st.markdown("### 📈 Task Status Overview")

chart_data = {
    "Status": ["Completed", "Pending", "Overdue"],
    "Number of Tasks": [
        len(completed_tasks),
        len(pending_tasks) - len(overdue_tasks),
        len(overdue_tasks),
    ],
}

st.bar_chart(
    chart_data,
    x="Status",
    y="Number of Tasks",
)

st.caption(
    "Overdue tasks are included in Pending and highlighted separately "
    "in the chart for easier tracking."
)

st.divider()


# --------------------------------------------------
# IN-APP REMINDERS
# --------------------------------------------------

st.subheader("🔔 Upcoming Task Reminders")

today = date.today()
reminders = []
overdue_reminders = []

for task in st.session_state.tasks:
    if task["status"] != "Pending":
        continue

    days_left = days_remaining(task)

    if days_left < 0:
        overdue_reminders.append(task)

    elif (
        task.get("reminder_enabled", True)
        and days_left <= task.get("reminder_days", 1)
    ):
        reminders.append(task)

if overdue_reminders:
    st.error(
        f"🚨 You have {len(overdue_reminders)} overdue task(s)!"
    )

    for task in overdue_reminders:
        days_overdue = abs(days_remaining(task))

        st.warning(
            f"**{task['name']}** — overdue by {days_overdue} day(s). "
            "Review the deadline and update your plan."
        )

if reminders:
    for task in sorted(reminders, key=lambda item: item["deadline"]):
        days_left = days_remaining(task)

        if days_left == 0:
            message = "Due today!"
        elif days_left == 1:
            message = "Due tomorrow!"
        else:
            message = f"Due in {days_left} days!"

        st.info(f"🔔 **{task['name']}** — {message}")

elif not overdue_reminders:
    st.success(
        "You're all caught up! No reminders due right now. 🎉"
    )

st.caption(
    "In-app reminders appear while the app is open or refreshed. "
    "They do not send notifications while the app is closed."
)

st.divider()


# --------------------------------------------------
# TASK LIST WITH EDITABLE DEADLINES
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
        task_col1, task_col2, task_col3 = st.columns([5, 2, 1])

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

            st.date_input(
                "📅 Edit deadline",
                value=task["deadline"],
                key=f"deadline_editor_{task['id']}",
                on_change=update_task_deadline,
                args=(task["id"],),
                help=(
                    "Change this date if an exam or assignment "
                    "deadline has been postponed."
                ),
            )

        with task_col2:
            st.metric("Priority score", score(task))

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
        "Recommended order based on deadline, importance, and effort:"
    )

    for index, task in enumerate(ranked_tasks, start=1):
        days = days_remaining(task)

        if days < 0:
            deadline_label = f"Overdue by {abs(days)} day(s)"
        elif days == 0:
            deadline_label = "Due today"
        elif days == 1:
            deadline_label = "Due tomorrow"
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
        "Example: My internal exam is tomorrow, "
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
