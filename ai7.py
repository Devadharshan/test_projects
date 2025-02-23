from fastapi import FastAPI, HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sqlite3
import pandas as pd
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Load Application Config
with open("applications.json", "r") as f:
    applications_data = json.load(f)
    applications = applications_data["applications"]

# Load ServiceNow Ticket Data
ticket_data = pd.read_csv("servicenow_tickets.csv").fillna("Unknown")

# Load AI Model (Phi-2)
MODEL_PATH = "C:/Users/YourUsername/phi-2/"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float32)

# Initialize SQLite Database
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    application TEXT,
    score INTEGER,
    questions TEXT,
    responses TEXT,
    final_score REAL
)
""")
conn.commit()

# Static Self-Assessment Questions
STATIC_QUESTIONS = [
    "How familiar are you with the core infrastructure of this application?",
    "Have you resolved any critical issues related to this application?",
    "How well do you understand its functionalities and dependencies?",
    "Have you worked on performance optimization for this application?",
    "Can you troubleshoot complex failures in this application?"
]

@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}

@app.get("/static-questions")
def get_static_questions():
    return {"questions": STATIC_QUESTIONS}

@app.post("/verify-skill")
def verify_skill(payload: dict):
    user = payload["user"]
    application = payload["application"]
    score = payload["score"]

    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    # Fetch ServiceNow tickets for this application
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Fetch Application Details
    app_details = applications.get(application, {})
    functionality = app_details.get("functionality", "Unknown functionality")
    criticality = app_details.get("criticality", "Unknown criticality")
    common_issues = app_details.get("common_issues", [])

    # AI Prompt Construction
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"This application handles: {functionality}. "
        f"It has a criticality level of {criticality}. "
        f"Common issues include: {', '.join(common_issues)}. "
        f"Here are some past issues from ServiceNow:\n"
    )

    for _, row in app_tickets.iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += "Generate 5 relevant questions to assess the user's actual expertise."

    inputs = tokenizer(input_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)
    
    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    return {"questions": [q for q in questions if q.strip()]}

@app.post("/submit-responses")
def submit_responses(payload: dict):
    user = payload["user"]
    application = payload["application"]
    questions = payload["questions"]
    responses = payload["responses"]

    # AI Validation Prompt
    validation_prompt = "Evaluate these answers on a scale of 0 to 100:\n"
    for q, r in zip(questions, responses):
        validation_prompt += f"Q: {q}\nA: {r}\n"

    inputs = tokenizer(validation_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=100)
    
    final_score = float(tokenizer.decode(output[0], skip_special_tokens=True).strip().split()[-1])

    # Store in DB
    cursor.execute("INSERT INTO assessments (user, application, score, questions, responses, final_score) VALUES (?, ?, ?, ?, ?, ?)",
                   (user, application, payload["score"], json.dumps(questions), json.dumps(responses), final_score))
    conn.commit()

    return {"final_score": final_score}

@app.get("/manager-view")
def get_manager_data():
    cursor.execute("SELECT * FROM assessments")
    data = cursor.fetchall()
    return {"assessments": data}





import streamlit as st
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_URL = "http://127.0.0.1:8000"

# Navbar
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

    if st.button("Submit Self-Assessment"):
        payload = {"user": user, "application": selected_application, "score": score}
        response = requests.post(f"{API_URL}/verify-skill", json=payload)
        questions = response.json().get("questions", [])

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
                "questions": st.session_state["questions"],
                "responses": st.session_state["answers"],
                "score": score
            }
            response = requests.post(f"{API_URL}/submit-responses", json=payload)
            st.success(f"Final Score: {response.json()['final_score']}%")

elif page == "Manager View":
    st.title("Manager View")

    response = requests.get(f"{API_URL}/manager-view")
    assessments = response.json()["assessments"]

    st.write(pd.DataFrame(assessments, columns=["ID", "User", "Application", "Score", "Questions", "Responses", "Final Score"]))
