from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import torch
import json
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load Model
device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "path_to_open_llama_13b"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path).to(device)

# Load Config & Tickets
with open("config.json", "r") as f:
    app_config = json.load(f)
ticket_data = pd.read_csv("tickets.csv")

# Initialize FastAPI
app = FastAPI()

# Database Setup
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        app_name TEXT,
        self_scores TEXT,
        ai_generated_questions TEXT,
        user_answers TEXT,
        final_score INTEGER,
        ai_feedback TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# Static Questions
STATIC_QUESTIONS = [
    "How well do you understand the architecture of this application?",
    "How confident are you in troubleshooting production issues?",
    "How familiar are you with the application's common issues?",
    "How well do you know the incident resolution workflow for this app?",
    "How comfortable are you with debugging logs and monitoring alerts?"
]

# Request Models
class AssessmentRequest(BaseModel):
    user_name: str
    app_name: str
    self_scores: list  # List of 5 self-ratings

class AnswerRequest(BaseModel):
    user_name: str
    app_name: str
    self_scores: list
    user_answers: list

# 1️⃣ Get Static Questions
@app.get("/static-questions")
def get_static_questions():
    return {"questions": STATIC_QUESTIONS}

# 2️⃣ Generate AI Questions
@app.post("/generate-questions")
def generate_questions(request: AssessmentRequest):
    app_info = app_config.get(request.app_name, {})
    
    # Extract past tickets
    app_tickets = ticket_data[ticket_data["Application"] == request.app_name]
    ticket_summary = "\n".join(app_tickets["Short Description"].tolist()[:10])

    # AI Prompt
    prompt = f"""
    The user rated themselves:
    1. Architecture: {request.self_scores[0]}/5
    2. Troubleshooting: {request.self_scores[1]}/5
    3. Common Issues: {request.self_scores[2]}/5
    4. Workflow: {request.self_scores[3]}/5
    5. Debugging: {request.self_scores[4]}/5

    Based on their scores, past tickets, and app details, generate 5 dynamic technical assessment questions.
    
    App Info:
    {app_info}

    Past Incidents:
    {ticket_summary}
    """

    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    output = model.generate(input_ids, max_length=300)
    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")[:5]
    
    return {"questions": questions}

# 3️⃣ Evaluate User Answers
@app.post("/evaluate-answers")
def evaluate_answers(request: AnswerRequest):
    prompt = f"""
    Evaluate these answers and assign a final skill score (1-5).

    Questions:
    {request.user_answers}

    Provide a final score and reasoning.
    """

    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    output = model.generate(input_ids, max_length=500)
    evaluation = tokenizer.decode(output[0], skip_special_tokens=True)

    final_score = int(evaluation.split("Final Score: ")[-1].strip()[0]) if "Final Score:" in evaluation else 1

    # Store Result
    cursor.execute("""
        INSERT INTO user_scores (user_name, app_name, self_scores, ai_generated_questions, user_answers, final_score, ai_feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (request.user_name, request.app_name, str(request.self_scores), str(request.user_answers), str(final_score), evaluation))
    conn.commit()

    return {"final_score": final_score, "ai_feedback": evaluation}

# 4️⃣ Get Previous Scores
@app.get("/get-scores")
def get_scores():
    cursor.execute("SELECT * FROM user_scores")
    scores = cursor.fetchall()
    return {"scores": scores}





import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

st.title("🚀 AI-Powered Knowledge Assessment")

view_mode = st.sidebar.radio("Select View", ["Self-Assessment", "Final Scores"])

if view_mode == "Self-Assessment":
    user_name = st.text_input("Enter your name")
    app_name = st.selectbox("Select Application", ["App1", "App2", "App3"])

    st.subheader("Predefined Self-Assessment Questions")
    static_questions_response = requests.get(f"{API_BASE}/static-questions")
    static_questions = static_questions_response.json()["questions"]
    
    self_scores = []
    for question in static_questions:
        self_scores.append(st.slider(question, 1, 5, 3))
    
    if st.button("Generate AI Questions"):
        response = requests.post(f"{API_BASE}/generate-questions", json={
            "user_name": user_name, "app_name": app_name, "self_scores": self_scores
        })
        questions = response.json()["questions"]
        
        st.subheader("AI-Generated Questions")
        user_answers = []
        for i, q in enumerate(questions):
            user_answers.append(st.text_area(f"Answer {i+1}: {q}"))

        if st.button("Submit Answers"):
            eval_response = requests.post(f"{API_BASE}/evaluate-answers", json={
                "user_name": user_name, "app_name": app_name, "self_scores": self_scores, "user_answers": user_answers
            })
            final_score = eval_response.json()["final_score"]
            ai_feedback = eval_response.json()["ai_feedback"]

            st.success(f"Final AI-Assigned Score: {final_score}")
            st.write("AI Feedback:", ai_feedback)

elif view_mode == "Final Scores":
    st.subheader("Previous Assessments")
    scores_response = requests.get(f"{API_BASE}/get-scores")
    scores = scores_response.json()["scores"]
    df = pd.DataFrame(scores, columns=["ID", "User", "App", "Self Scores", "AI Questions", "User Answers", "Final Score", "AI Feedback", "Timestamp"])
    st.dataframe(df)



