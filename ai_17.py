from fastapi import FastAPI
import torch
import sqlite3
import random
import json
import pandas as pd
from transformers import LlamaForCausalLM, LlamaTokenizer

app = FastAPI()

# ---- Load Model ----
MODEL_PATH = "models/llama-2-7b"
tokenizer = LlamaTokenizer.from_pretrained(MODEL_PATH)
model = LlamaForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)

# ---- Load Data ----
TICKET_DATA = pd.read_csv("data/tickets.csv")

with open("data/app_config.json", "r") as f:
    APP_CONFIG = json.load(f)

# ---- Initialize Database ----
DB_FILE = "assessment.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            static_score INTEGER,
            dynamic_questions TEXT,
            user_answers TEXT,
            final_score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_assessment(user, static_score, questions, answers, final_score):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assessments (user, static_score, dynamic_questions, user_answers, final_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (user, static_score, str(questions), str(answers), final_score))
    conn.commit()
    conn.close()

# ---- API Routes ----

@app.get("/")
def home():
    return {"message": "LLaMA-2 AI Assessment API"}

@app.post("/generate_questions/")
def generate_questions(user: str, static_score: int):
    """Generate AI questions based on user score and past tickets."""
    questions = []
    difficulty = ["Basic", "Moderate", "Advanced"]
    score_level = difficulty[min(static_score - 1, len(difficulty) - 1)]

    for _ in range(5):
        sample_ticket = TICKET_DATA.sample(1).iloc[0]
        app_name = sample_ticket["application"]

        if app_name in APP_CONFIG:
            app_details = APP_CONFIG[app_name]["functionality"]
            criticality = APP_CONFIG[app_name]["criticality"]
            common_issues = ", ".join(APP_CONFIG[app_name]["common_issues"])

            prompt = f"""
            Generate a {score_level} difficulty question for an engineer supporting {app_name}.
            - Functionality: {app_details}
            - Criticality: {criticality}
            - Common Issues: {common_issues}
            - Recent Ticket: {sample_ticket["short_description"]}, {sample_ticket["close notes"]}
            """
        else:
            prompt = f"Generate a {score_level} difficulty question based on the ticket: {sample_ticket['short_description']}"

        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = model.generate(**inputs, max_length=100)
        question = tokenizer.decode(outputs[0], skip_special_tokens=True)

        questions.append(question)

    return {"questions": questions}

@app.post("/evaluate_answers/")
def evaluate_answers(user: str, static_score: int, user_answers: list, dynamic_questions: list):
    """Evaluate user answers and compute final AI score."""
    correct_answers = sum(1 for ans in user_answers if len(ans) > 10)
    final_score = max(1, min(5, static_score + correct_answers - random.randint(0, 1)))

    save_assessment(user, static_score, dynamic_questions, user_answers, final_score)

    return {"final_score": final_score}





prompt = f"""
Generate a {score_level} difficulty question for an engineer supporting {sample_ticket['application']}.
Analyze the following details to understand the issue:
- Ticket Long Description: {sample_ticket['long description']}
- Message to User: {sample_ticket['message to user']}

The question should be relevant to the application's issue and require the engineer to demonstrate their understanding.
"""




import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("🔍 AI-Powered Support Assessment")

# User Input
user_name = st.text_input("Enter Your Name")
static_score = st.slider("Self-Assessment Score (1-5)", 1, 5, 3)

if st.button("Start AI Evaluation"):
    res = requests.post(f"{API_URL}/generate_questions/", json={"user": user_name, "static_score": static_score})
    questions = res.json()["questions"]
    
    user_answers = []
    for i, q in enumerate(questions):
        answer = st.text_area(f"Q{i+1}: {q}")
        user_answers.append(answer)

    if st.button("Submit Answers"):
        eval_res = requests.post(f"{API_URL}/evaluate_answers/", json={
            "user": user_name,
            "static_score": static_score,
            "user_answers": user_answers,
            "dynamic_questions": questions
        })
        final_score = eval_res.json()["final_score"]
        st.success(f"🎯 Your AI-verified score: {final_score}")



