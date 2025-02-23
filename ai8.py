if st.button("Submit Self-Assessment"):
    payload = {
        "user": user,
        "application": selected_application,
        "score": sum(static_answers) / len(static_answers),  # Calculate average score
        "static_answers": static_answers
    }

----
@app.post("/verify-skill")
def verify_skill(payload: dict):
    user = payload.get("user", "")
    application = payload.get("application", "")
    score = payload.get("score", None)  # Use .get() to avoid KeyError
    static_answers = payload.get("static_answers", [])

    if not user or not application:
        raise HTTPException(status_code=400, detail="User or application missing")
    
    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    if score is None:
        raise HTTPException(status_code=400, detail="Score missing in request")

    # Get Tickets for the selected application
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Construct AI Prompt
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"Here are their answers:\n"
    )

    for q, ans in zip(STATIC_QUESTIONS, static_answers):
        input_prompt += f"Q: {q}\nA: {ans}\n"

    input_prompt += "\nHere are past ServiceNow issues:\n"
    
    # Limit ticket history to avoid exceeding model input limits
    for _, row in app_tickets.head(5).iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += "Generate 5 questions to test the user’s skill."

    # **Tokenize with truncation**
    inputs = tokenizer(input_prompt, return_tensors="pt", truncation=True, max_length=1024)

    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)

    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": [q for q in questions if q.strip()]}


----
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
    
    # Limit to last 5 tickets to reduce token count
    for _, row in app_tickets.head(5).iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += "Generate 5 questions to test the user’s skill."

    # **Tokenize with truncation**
    inputs = tokenizer(input_prompt, return_tensors="pt", truncation=True, max_length=1024)

    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)

    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": [q for q in questions if q.strip()]}


import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    # Get Applications with 400 Error Handling
    try:
        response = requests.get(f"{API_URL}/applications")
        if response.status_code == 200:
            applications = response.json().get("applications", [])
        else:
            st.error(f"Error fetching applications: {response.status_code}")
            applications = []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name").strip()
    selected_application = st.selectbox("Select Application", applications if applications else ["No applications found"])

    # Static Questions with 400 Error Handling
    try:
        response = requests.get(f"{API_URL}/static-questions")
        if response.status_code == 200:
            static_questions = response.json().get("questions", [])
        else:
            st.error(f"Error fetching static questions: {response.status_code}")
            static_questions = []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        static_questions = []

    static_answers = []
    st.subheader("Static Questions (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.selectbox(f"Q{i+1}: {question}", [1, 2, 3, 4, 5], index=2, key=f"static_{i}")
        static_answers.append(answer)

    # Submit Self-Assessment with 400 Error Handling
    if st.button("Submit Self-Assessment"):
        if not user:
            st.error("Please enter your name.")
        elif selected_application == "No applications found":
            st.error("No applications available to select.")
        else:
            payload = {
                "user": user,
                "application": selected_application,
                "static_answers": static_answers
            }
            try:
                response = requests.post(f"{API_URL}/verify-skill", json=payload)
                if response.status_code == 200:
                    questions = response.json().get("ai_questions", [])
                    st.session_state["questions"] = questions
                    st.session_state["answers"] = [""] * len(questions)
                else:
                    st.error(f"Error processing assessment: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {e}")

    # AI-Generated Questions Section
    if "questions" in st.session_state and st.session_state["questions"]:
        st.subheader("AI-Generated Questions")
        if "answers" not in st.session_state:
            st.session_state["answers"] = [""] * len(st.session_state["questions"])

        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        # Submit AI Responses
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
                if response.status_code == 200:
                    final_score = response.json().get("final_score", "N/A")
                    st.success(f"Final Score: {final_score}%")
                else:
                    st.error(f"Error submitting responses: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {e}")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        if response.status_code == 200:
            assessments = response.json().get("assessments", [])
            df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
            st.write(df)
        else:
            st.error(f"Error fetching manager data: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")



----
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
    except:
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
    try:
        response = requests.get(f"{API_URL}/static-questions")
        static_questions = response.json().get("questions", [])
    except:
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
            questions = response.json().get("ai_questions", [])
            st.session_state["questions"] = questions
            st.session_state["answers"] = [""] * len(questions)  # Fixes KeyError
        except:
            st.error("Error processing your assessment")
            st.session_state["questions"] = []
            st.session_state["answers"] = []

    if "questions" in st.session_state and st.session_state["questions"]:
        st.subheader("AI-Generated Questions")
        if "answers" not in st.session_state:
            st.session_state["answers"] = [""] * len(st.session_state["questions"])  # Ensure answers exist

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
            except:
                st.error("Error submitting responses")
                final_score = "N/A"

            st.success(f"Final Score: {final_score}%")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        assessments = response.json().get("assessments", [])
        df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
        st.write(df)
    except:
        st.error("Error fetching manager data")


----
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
    static_answers = payload["static_answers"]
    score = sum(static_answers) / len(static_answers)  # Average static score

    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    # Get Tickets for Application
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Construct AI Prompt
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"Here are their answers:\n"
    )

    for q, ans in zip(STATIC_QUESTIONS, static_answers):
        input_prompt += f"Q: {q}\nA: {ans}\n"

    input_prompt += "\nPast ServiceNow Tickets:\n"
    for _, row in app_tickets.iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += f"\nGenerate 5 questions that assess a user with skill level {score}/5."

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

    # Validate Responses using AI
    validation_prompt = "Evaluate these answers (0-100):\n"
    for q, r in zip(ai_questions, ai_responses):
        validation_prompt += f"Q: {q}\nA: {r}\n"

    inputs = tokenizer(validation_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=100)

    final_score = float(tokenizer.decode(output[0], skip_special_tokens=True).strip().split()[-1])

    cursor.execute("INSERT INTO assessments (user, application, score, static_answers, ai_questions, ai_responses, final_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (user, application, sum(static_answers) / len(static_answers), json.dumps(static_answers), json.dumps(ai_questions), json.dumps(ai_responses), final_score))
    conn.commit()

    return {"final_score": final_score}

@app.get("/manager-view")
def manager_view():
    cursor.execute("SELECT * FROM assessments")
    data = cursor.fetchall()
    return {"assessments": data}






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
    except:
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
    try:
        response = requests.get(f"{API_URL}/static-questions")
        static_questions = response.json().get("questions", [])
    except:
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
            questions = response.json().get("ai_questions", [])
        except:
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
            except:
                st.error("Error submitting responses")
                final_score = "N/A"

            st.success(f"Final Score: {final_score}%")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        assessments = response.json().get("assessments", [])
        df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
        st.write(df)
    except:
        st.error("Error fetching manager data")
