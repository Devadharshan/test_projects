import json
import pandas as pd
import sqlite3
import torch
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM

app = FastAPI()

# Load application config
with open("app_conf.json", "r") as f:
    app_conf = json.load(f)
applications = app_conf["Application"]

# Load ServiceNow data from CSV
ticket_data = pd.read_csv("servicenow_tickets.csv").fillna("Unknown")

# Load AI Model (Phi-2)
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)

# SQLite DB Setup
conn = sqlite3.connect("assessments.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        application TEXT,
        static_answers TEXT,
        ai_questions TEXT,
        ai_responses TEXT,
        final_score REAL,
        timestamp TEXT
    )
""")
conn.commit()

# ---------------------------
# API Models
class SkillVerificationRequest(BaseModel):
    user: str
    application: str
    static_answers: list[int]

class ResponseVerificationRequest(BaseModel):
    user: str
    application: str
    static_answers: list[int]
    ai_questions: list[str]
    ai_responses: list[str]

# ---------------------------
# Fetch Applications
@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}

# Static Questions
@app.get("/static-questions")
def get_static_questions():
    return {
        "questions": [
            "How confident are you in debugging this application?",
            "How familiar are you with its architecture?",
            "Have you resolved critical incidents related to this app?",
            "How often do you work with this app?",
            "Can you explain the app’s core functionality?"
        ]
    }

# Generate **Scenario-Based** AI Questions
def generate_scenario_questions(application: str, scores: list[int]):
    relevant_tickets = ticket_data[ticket_data["Application"].str.strip() == application]
    selected_tickets = relevant_tickets.sample(min(5, len(relevant_tickets)), random_state=42) if len(relevant_tickets) > 0 else pd.DataFrame()

    avg_score = sum(scores) / len(scores)
    difficulty = "beginner" if avg_score <= 2 else "moderate" if avg_score < 4 else "advanced"

    questions = []
    for _, row in selected_tickets.iterrows():
        prompt = f"Create a {difficulty}-level troubleshooting scenario for {application}. "
        prompt += f"Based on this issue: '{row['Short Description']}', generate a detailed problem-solving question."

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        output_ids = model.generate(inputs.input_ids, max_length=50)
        question = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        questions.append(question)

    return questions if questions else ["No relevant tickets found for scenario generation."]

# Verify Skill & Generate AI Questions
@app.post("/verify-skill")
def verify_skill(request: SkillVerificationRequest):
    if request.application not in applications:
        raise HTTPException(status_code=400, detail="Invalid application.")

    ai_questions = generate_scenario_questions(request.application, request.static_answers)
    return {"static_questions": get_static_questions()["questions"], "ai_questions": ai_questions}

# Submit AI Responses & Store in DB
@app.post("/submit-responses")
def submit_responses(request: ResponseVerificationRequest):
    total_questions = len(request.ai_questions)
    correct = sum(1 for ans in request.ai_responses if ans.strip() != "")
    final_score = (correct / total_questions) * 100 if total_questions > 0 else 0

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO assessments (user, application, static_answers, ai_questions, ai_responses, final_score, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request.user,
        request.application,
        json.dumps(request.static_answers),
        json.dumps(request.ai_questions),
        json.dumps(request.ai_responses),
        final_score,
        timestamp
    ))
    conn.commit()

    return {"final_score": final_score}

# Manager View
@app.get("/manager-view")
def manager_view():
    cursor.execute("SELECT * FROM assessments ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    return [{
        "id": row[0],
        "user": row[1],
        "application": row[2],
        "static_answers": json.loads(row[3]),
        "ai_questions": json.loads(row[4]),
        "ai_responses": json.loads(row[5]),
        "final_score": row[6],
        "timestamp": row[7]
    } for row in rows]







import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.title("Self-Assessment Tool")

apps_response = requests.get(f"{API_BASE_URL}/applications")
applications = apps_response.json()["applications"] if apps_response.status_code == 200 else []

user_name = st.text_input("Enter your name:")
selected_app = st.selectbox("Select an application:", applications)

# Maintain Session State
if "static_answers" not in st.session_state:
    st.session_state.static_answers = []
if "ai_questions" not in st.session_state:
    st.session_state.ai_questions = []
if "user_responses" not in st.session_state:
    st.session_state.user_responses = []

# Static Questions
static_questions = requests.get(f"{API_BASE_URL}/static-questions").json()["questions"]
st.subheader("Rate yourself (1 = Low, 5 = High):")

for i, question in enumerate(static_questions):
    answer = st.slider(question, 1, 5, 3, key=f"static_q_{i}")
    if len(st.session_state.static_answers) < len(static_questions):
        st.session_state.static_answers.append(answer)

if st.button("Submit Self-Assessment"):
    skill_data = {
        "user": user_name,
        "application": selected_app,
        "static_answers": st.session_state.static_answers
    }
    ai_response = requests.post(f"{API_BASE_URL}/verify-skill", json=skill_data)
    
    if ai_response.status_code == 200:
        st.session_state.ai_questions = ai_response.json()["ai_questions"]

st.subheader("Answer AI-Generated Scenario Questions:")
for i, q in enumerate(st.session_state.ai_questions):
    response = st.text_area(q, key=f"ai_q_{i}")
    if len(st.session_state.user_responses) < len(st.session_state.ai_questions):
        st.session_state.user_responses.append(response)

if st.button("Submit Answers"):
    submit_data = {
        "user": user_name,
        "application": selected_app,
        "static_answers": st.session_state.static_answers,
        "ai_questions": st.session_state.ai_questions,
        "ai_responses": st.session_state.user_responses
    }
    submit_response = requests.post(f"{API_BASE_URL}/submit-responses", json=submit_data)
    if submit_response.status_code == 200:
        st.success(f"Final Score: {submit_response.json()['final_score']}%")
