from fastapi import FastAPI, HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sqlite3
import pandas as pd
import json
import logging

app = FastAPI()

# Load Applications
with open("applications.json", "r") as f:
    applications = json.load(f)["applications"]

# Load Ticket Data
ticket_data = pd.read_csv("servicenow_tickets.csv").fillna("Unknown")

# Load AI Model
MODEL_PATH = "C:/Users/YourUsername/phi-2/"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float32)

# Database
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    application TEXT,
    score INTEGER,
    static_answers TEXT,
    ai_questions TEXT,
    ai_responses TEXT,
    final_score REAL
)
""")
conn.commit()

# Static Questions
STATIC_QUESTIONS = [
    "How familiar are you with this application's core infrastructure?",
    "Have you resolved any major issues related to this application?",
    "Do you understand its dependencies?",
    "Have you optimized its performance?",
    "Can you troubleshoot critical failures?"
]

@app.get("/static-questions")
def get_static_questions():
    return {"questions": STATIC_QUESTIONS}

@app.post("/verify-skill")
def verify_skill(payload: dict):
    user = payload["user"]
    application = payload["application"]
    score = payload["score"]
    static_answers = payload["static_answers"]

    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    # Get Tickets
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Construct AI Prompt
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"Here are their answers:\n"
    )

    for q, ans in zip(STATIC_QUESTIONS, static_answers):
        input_prompt += f"Q: {q}\nA: {ans}\n"

    input_prompt += "\nHere are past ServiceNow issues:\n"
    for _, row in app_tickets.iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += "Generate 5 questions to test the user’s skill."

    inputs = tokenizer(input_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)

    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": [q for q in questions if q.strip()]}

@app.post("/submit-responses")
def submit_responses(payload: dict):
    user = payload["user"]
    application = payload["application"]
    static_answers = payload["static_answers"]
    ai_questions = payload["ai_questions"]
    ai_responses = payload["ai_responses"]

    validation_prompt = "Evaluate these answers (0-100):\n"
    for q, r in zip(ai_questions, ai_responses):
        validation_prompt += f"Q: {q}\nA: {r}\n"

    inputs = tokenizer(validation_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=100)

    final_score = float(tokenizer.decode(output[0], skip_special_tokens=True).strip().split()[-1])

    cursor.execute("INSERT INTO assessments (user, application, score, static_answers, ai_questions, ai_responses, final_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (user, application, payload["score"], json.dumps(static_answers), json.dumps(ai_questions), json.dumps(ai_responses), final_score))
    conn.commit()

    return {"final_score": final_score}





import streamlit as st
import requests
import json
import pandas as pd

API_URL = "http://127.0.0.1:8000"

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    # Get Applications
    response = requests.get(f"{API_URL}/applications")
    applications = response.json()["applications"]

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)
    score = st.slider("Rate Your Skill (1-5)", 1, 5)

    # Static Questions
    response = requests.get(f"{API_URL}/static-questions")
    static_questions = response.json()["questions"]

    static_answers = []
    st.subheader("Static Questions")
    for i, question in enumerate(static_questions):
        answer = st.text_area(f"Q{i+1}: {question}", key=f"static_{i}")
        static_answers.append(answer)

    if st.button("Submit Self-Assessment"):
        payload = {
            "user": user,
            "application": selected_application,
            "score": score,
            "static_answers": static_answers
        }
        response = requests.post(f"{API_URL}/verify-skill", json=payload)
        questions = response.json().get("ai_questions", [])

        st.session_state["questions"] = questions
        st.session_state["answers"] = [""] * len(questions)

    if "questions" in st.session_state:
        st.subheader("AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        if st.button("Submit Responses"):
            payload = {
                "user": user,
                "application": selected_application,
                "static_answers": static_answers,
                "ai_questions": st.session_state["questions"],
                "ai_responses": st.session_state["answers"],
                "score": score
            }
            response = requests.post(f"{API_URL}/submit-responses", json=payload)
            st.success(f"Final Score: {response.json()['final_score']}%")

elif page == "Manager View":
    st.title("Manager View")

    response = requests.get(f"{API_URL}/manager-view")
    assessments = response.json()["assessments"]

    st.write(pd.DataFrame(assessments, columns=["ID", "User", "Application", "Score", "Static Answers", "AI Questions", "AI Responses", "Final Score"]))





import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    # Get Applications
    response = requests.get(f"{API_URL}/applications")
    applications = response.json()["applications"]

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)
    score = st.slider("Rate Your Skill (1-5)", 1, 5)

    # Static Questions with Dropdown
    response = requests.get(f"{API_URL}/static-questions")
    static_questions = response.json()["questions"]

    static_answers = []
    st.subheader("Static Questions (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.selectbox(f"Q{i+1}: {question}", [1, 2, 3, 4, 5], index=2, key=f"static_{i}")
        static_answers.append(answer)

    if st.button("Submit Self-Assessment"):
        payload = {
            "user": user,
            "application": selected_application,
            "score": score,
            "static_answers": static_answers
        }
        response = requests.post(f"{API_URL}/verify-skill", json=payload)
        questions = response.json().get("ai_questions", [])

        st.session_state["questions"] = questions
        st.session_state["answers"] = [""] * len(questions)

    if "questions" in st.session_state:
        st.subheader("AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        if st.button("Submit Responses"):
            payload = {
                "user": user,
                "application": selected_application,
                "static_answers": static_answers,
                "ai_questions": st.session_state["questions"],
                "ai_responses": st.session_state["answers"],
                "score": score
            }
            response = requests.post(f"{API_URL}/submit-responses", json=payload)
            st.success(f"Final Score: {response.json()['final_score']}%")

elif page == "Manager View":
    st.title("Manager View")

    response = requests.get(f"{API_URL}/manager-view")
    assessments = response.json()["assessments"]

    st.write(pd.DataFrame(assessments, columns=["ID", "User", "Application", "Score", "Static Answers", "AI Questions", "AI Responses", "Final Score"]))






import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    # Get Applications
    try:
        response = requests.get(f"{API_URL}/applications")
        applications = response.json().get("applications", [])
    except requests.exceptions.RequestException:
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
    try:
        response = requests.get(f"{API_URL}/static-questions")
        static_questions = response.json().get("questions", [])
    except requests.exceptions.RequestException:
        st.error("Error fetching static questions")
        static_questions = []

    static_answers = []
    st.subheader("Static Questions (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.selectbox(f"Q{i+1}: {question}", [1, 2, 3, 4, 5], index=2, key=f"static_{i}")
        static_answers.append(answer)

    if st.button("Submit Self-Assessment"):
        payload = {
            "user": user,
            "application": selected_application,
            "static_answers": static_answers
        }
        try:
            response = requests.post(f"{API_URL}/verify-skill", json=payload)
            data = response.json()
            questions = data.get("ai_questions", [])
        except requests.exceptions.RequestException:
            st.error("Error processing your assessment")
            questions = []

        st.session_state["questions"] = questions
        st.session_state["answers"] = [""] * len(questions)

    if "questions" in st.session_state:
        st.subheader("AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        if st.button("Submit Responses"):
            payload = {
                "user": user,
                "application": selected_application,
                "static_answers": static_answers,
                "ai_questions": st.session_state["questions"],
                "ai_responses": st.session_state["answers"]
            }
            try:
                response = requests.post(f"{API_URL}/submit-responses", json=payload)
                final_score = response.json().get("final_score", "N/A")
                st.success(f"Final Score: {final_score}%")
            except requests.exceptions.RequestException:
                st.error("Error submitting responses")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        assessments = response.json().get("assessments", [])
        st.write(pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"]))
    except requests.exceptions.RequestException:
        st.error("Error fetching manager data")





import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    # Get Applications
    try:
        response = requests.get(f"{API_URL}/applications")
        applications = response.json().get("applications", [])
    except (requests.exceptions.RequestException, ValueError):
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
    try:
        response = requests.get(f"{API_URL}/static-questions")
        static_questions = response.json().get("questions", [])
    except (requests.exceptions.RequestException, ValueError):
        st.error("Error fetching static questions")
        static_questions = []

    static_answers = []
    st.subheader("Static Questions (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.selectbox(f"Q{i+1}: {question}", [1, 2, 3, 4, 5], index=2, key=f"static_{i}")
        static_answers.append(answer)

    if st.button("Submit Self-Assessment"):
        payload = {
            "user": user,
            "application": selected_application,
            "static_answers": static_answers
        }
        try:
            response = requests.post(f"{API_URL}/verify-skill", json=payload)
            response_data = response.json()
            questions = response_data.get("ai_questions", [])  # Ensure key exists
        except (requests.exceptions.RequestException, ValueError):
            st.error("Error processing your assessment")
            questions = []

        st.session_state["questions"] = questions
        st.session_state["answers"] = [""] * len(questions)

    if "questions" in st.session_state:
        st.subheader("AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        if st.button("Submit Responses"):
            payload = {
                "user": user,
                "application": selected_application,
                "static_answers": static_answers,
                "ai_questions": st.session_state["questions"],
                "ai_responses": st.session_state["answers"]
            }
            try:
                response = requests.post(f"{API_URL}/submit-responses", json=payload)
                response_data = response.json()
                final_score = response_data.get("final_score", "N/A")
                ai_responses = response_data.get("responses", [])  # Fix KeyError issue
            except (requests.exceptions.RequestException, ValueError, KeyError, TypeError):
                st.error("Error submitting responses")
                final_score = "N/A"
                ai_responses = []

            st.success(f"Final Score: {final_score}%")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        assessments = response.json().get("assessments", [])
        st.write(pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"]))
    except (requests.exceptions.RequestException, ValueError):
        st.error("Error fetching manager data")

