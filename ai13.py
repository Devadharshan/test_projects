from fastapi import FastAPI, HTTPException
import json
import pandas as pd
import sqlite3
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Load Config
with open("app_conf.json", "r") as f:
    applications_data = json.load(f)
applications = applications_data["Application"]
static_questions = applications_data["StaticQuestions"]

# Load ServiceNow Data (CSV)
df = pd.read_csv("servicenow_tickets.csv")

# Load AI Model (Phi-2)
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token

# Setup Database
conn = sqlite3.connect("skill_assessment.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        application TEXT,
        static_answers TEXT,
        ai_questions TEXT,
        ai_responses TEXT,
        final_score REAL
    )
""")
conn.commit()


class SelfAssessmentRequest(BaseModel):
    user: str
    application: str
    static_answers: List[int]


class AnswerSubmissionRequest(BaseModel):
    user: str
    application: str
    static_answers: List[int]
    ai_questions: List[str]
    ai_responses: List[str]


@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}


@app.get("/static-questions")
def get_static_questions():
    return {"questions": static_questions}


@app.post("/verify-skill")
def verify_skill(data: SelfAssessmentRequest):
    """Generates AI-based validation questions."""
    user_score = sum(data.static_answers) / len(data.static_answers)
    app_tickets = df[df["Application"] == data.application]

    prompt = f"User rated themselves {user_score} on {data.application}. Generate {len(static_questions)} relevant scenario-based validation questions."

    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=250)
    outputs = model.generate(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], max_length=500)
    
    ai_questions = tokenizer.decode(outputs[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": ai_questions[:len(static_questions)]}


@app.post("/submit-responses")
def submit_responses(data: AnswerSubmissionRequest):
    """Stores user responses in DB."""
    final_score = sum(data.static_answers) * 5  

    cursor.execute("""
        INSERT INTO assessments (user, application, static_answers, ai_questions, ai_responses, final_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.user, data.application, json.dumps(data.static_answers), json.dumps(data.ai_questions), json.dumps(data.ai_responses), final_score))
    conn.commit()

    return {"final_score": final_score}


@app.get("/manager-view")
def manager_view():
    """Returns stored assessments from DB."""
    cursor.execute("SELECT user, application, final_score FROM assessments")
    results = cursor.fetchall()
    return {"assessments": [{"user": r[0], "application": r[1], "final_score": r[2]} for r in results]}




import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    response = requests.get(f"{API_URL}/applications")
    applications = response.json().get("applications", []) if response.status_code == 200 else []
    
    response = requests.get(f"{API_URL}/static-questions")
    static_questions = response.json().get("questions", []) if response.status_code == 200 else []

    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

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
        response = requests.post(f"{API_URL}/verify-skill", json=payload)
        questions = response.json().get("ai_questions", []) if response.status_code == 200 else []
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
            response = requests.post(f"{API_URL}/submit-responses", json=payload)
            final_score = response.json().get("final_score", "N/A") if response.status_code == 200 else "N/A"
            st.success(f"Final Score: {final_score}%")

elif page == "Manager View":
    st.title("Manager View")

    response = requests.get(f"{API_URL}/manager-view")
    assessments = response.json().get("assessments", []) if response.status_code == 200 else []
    
    st.write(pd.DataFrame(assessments))
