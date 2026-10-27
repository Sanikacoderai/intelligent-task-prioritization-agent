# Intelligent Task Prioritization Agent — Web Version

## Run locally on Windows
1. Open Command Prompt in this folder.
2. Install Streamlit: `py -m pip install -r requirements.txt`
3. Start the app: `py -m streamlit run app.py`
4. Your browser should open at `http://localhost:8501`.

## Publish a public link
1. Sign in or create a GitHub account.
2. Create a repository such as `task-prioritization-agent`.
3. Upload `app.py`, `requirements.txt`, and this `README.md`.
4. Sign in to Streamlit Community Cloud with GitHub.
5. Create an app, select the repository and `app.py`, then deploy.
6. Copy the generated `streamlit.app` URL and share it.

## Honest project description
This prototype uses rule-based scoring, not a trained machine-learning model or LLM. Its workflow is to collect task details, calculate scores, rank tasks and recommend an action plan.
