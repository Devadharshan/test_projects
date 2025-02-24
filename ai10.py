from fastapi import FastAPI, HTTPException
import pandas as pd
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime
from pydantic import BaseModel
import sqlite3

# Load Configuration
with open("app_conf.json", "r") as f:
    app_conf = json.load(f)

applications = app_conf["Application"]

# Load CSV Data
csv_file = "servicenow_tickets.csv"
df = pd.read_csv(csv_file)

# Load AI Model (Phi-2)
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

app = FastAPI()

# SQLite Database
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        application TEXT,
        static_answers TEXT,
        ai_questions TEXT,
        ai_responses TEXT,
        final_score INTEGER,
        timestamp TEXT
    )
""")
conn.commit()

# API Models
class AssessmentRequest(BaseModel):
    user: str
    application: str
    static_answers: list

class ResponseSubmission(BaseModel):
    user: str
    application: str
    static_answers: list
    ai_questions: list
    ai_responses: list

# Get Applications
@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}

# AI Question Generation
def generate_questions(application, static_answers):
    # Filter related tickets
    app_tickets = df[df["Application"] == application]["Close Notes"].dropna().tolist()
    context = " ".join(app_tickets[:5])  # Limit context size

    prompt = f"Based on the following ServiceNow tickets, generate {len(static_answers)} relevant questions: {context}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        output = model.generate(**inputs, max_length=100)
    
    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")
    return questions[:len(static_answers)]  # Ensure same number as static questions

# Verify Skill & Generate AI Questions
@app.post("/verify-skill")
def verify_skill(request: AssessmentRequest):
    ai_questions = generate_questions(request.application, request.static_answers)
    return {"ai_questions": ai_questions}

# Process Responses & Store in DB
@app.post("/submit-responses")
def submit_responses(request: ResponseSubmission):
    final_score = sum(request.static_answers) * 4  # Score based on self-ratings
    
    # Store results
    cursor.execute("""
        INSERT INTO assessments (user, application, static_answers, ai_questions, ai_responses, final_score, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (request.user, request.application, json.dumps(request.static_answers), json.dumps(request.ai_questions),
          json.dumps(request.ai_responses), final_score, datetime.now().isoformat()))
    conn.commit()

    return {"final_score": final_score}

# Manager View
@app.get("/manager-view")
def manager_view():
    cursor.execute("SELECT * FROM assessments")
    results = cursor.fetchall()
    assessments = [
        {"id": r[0], "user": r[1], "application": r[2], "static_answers": json.loads(r[3]),
         "ai_questions": json.loads(r[4]), "ai_responses": json.loads(r[5]), "final_score": r[6], "timestamp": r[7]}
        for r in results
    ]
    return {"assessments": assessments}