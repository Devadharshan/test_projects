import json
import pandas as pd
import sqlite3
import torch
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM

app = FastAPI()

# Load application config from JSON
with open("app_conf.json", "r") as f:
    app_conf = json.load(f)
applications = app_conf["Application"]

# Load ServiceNow tickets from CSV (ensure relevant columns exist)
ticket_data = pd.read_csv("servicenow_tickets.csv").fillna("Unknown")

# Load AI Model (Phi-2)
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)

# SQLite Database Setup
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
# Models for API requests
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
# Get list of applications
@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}

# Get static self-assessment questions
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

# Generate AI questions based on static score & CSV data
def generate_questions(application: str, scores: list[int]):
    relevant_tickets = ticket_data[ticket_data["Application"].str.strip() == application]
    selected_tickets = relevant_tickets.sample(min(5, len(relevant_tickets)), random_state=42) if len(relevant_tickets) > 0 else pd.DataFrame()

    avg_score = sum(scores) / len(scores)
    difficulty = "beginner" if avg_score <= 2 else "moderate" if avg_score < 4 else "advanced"

    questions = []
    for i in range(5):
        prompt = f"Generate a {difficulty}-level question about troubleshooting in {application}."
        if i < len(selected_tickets):
            prompt += f" Consider this issue: '{selected_tickets.iloc[i]['Short Description']}'."
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        output_ids = model.generate(inputs.input_ids, max_length=50)
        question = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        questions.append(question)
    return questions

# Verify skill and generate AI questions
@app.post("/verify-skill")
def verify_skill(request: SkillVerificationRequest):
    if request.application not in applications:
        raise HTTPException(status_code=400, detail="Invalid application.")

    ai_questions = generate_questions(request.application, request.static_answers)
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

# Manager View: Fetch stored assessments
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