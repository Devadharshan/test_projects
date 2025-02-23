from fastapi import FastAPI, HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import pandas as pd
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Load Application Details
with open("applications.json", "r") as f:
    applications_data = json.load(f)
    applications = applications_data["applications"]

# Load ServiceNow Ticket Data
ticket_data = pd.read_csv("servicenow_tickets.csv").fillna("Unknown")  # Handle missing values

# Load Phi-2 Model (CPU-only)
MODEL_PATH = "C:/Users/YourUsername/phi-2/"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float32)

# Database Setup
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    application TEXT,
    score INTEGER,
    questions TEXT,
    answers TEXT,
    percentage_score REAL
)
""")
conn.commit()

# Static Self-Assessment Questions
STATIC_QUESTIONS = [
    "How well do you understand this application's architecture?",
    "Have you worked on major issues related to this application?",
    "How familiar are you with debugging and performance tuning?",
    "Have you worked on automating processes in this application?",
    "Can you troubleshoot complex failures efficiently?"
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
    responses = payload["responses"]

    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    # Fetch relevant ServiceNow tickets
    app_tickets = ticket_data[ticket_data["Application"] == application]
    logging.info(f"Found {len(app_tickets)} tickets for application {application}")

    # Fetch Application Details
    app_details = applications.get(application, {})
    functionality = app_details.get("functionality", "Unknown functionality")
    criticality = app_details.get("criticality", "Unknown criticality")
    common_issues = app_details.get("common_issues", [])

    # Compute AI Question Prompt
    input_prompt = (
        f"User rated themselves {responses} in {application}. "
        f"This application handles: {functionality}. "
        f"It has a criticality level of {criticality}. "
        f"Common issues include: {', '.join(common_issues)}. "
        f"Based on past ServiceNow tickets, generate 5 advanced questions."
    )

    # Generate AI Questions
    inputs = tokenizer(input_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=300, eos_token_id=tokenizer.eos_token_id)
    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    # Store Assessment Data
    cursor.execute(
        "INSERT INTO assessments (user, application, score, questions, answers, percentage_score) VALUES (?, ?, ?, ?, ?, ?)",
        (user, application, responses, json.dumps(questions), "Pending", 0.0),
    )
    conn.commit()

    return {"questions": [q for q in questions if q.strip()]}

@app.get("/manager-view")
def get_manager_view():
    cursor.execute("SELECT * FROM assessments")
    data = cursor.fetchall()
    return {"assessments": data}






import streamlit as st
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_BASE_URL = "http://127.0.0.1:8000"  # Change if running FastAPI on a different port

st.set_page_config(page_title="Self-Assessment Tool", layout="wide")

# Fetch Applications
def fetch_applications():
    response = requests.get(f"{API_BASE_URL}/applications")
    return response.json()["applications"]

# Fetch Static Questions
def fetch_static_questions():
    response = requests.get(f"{API_BASE_URL}/static-questions")
    return response.json()["questions"]

# Submit Self-Assessment
def submit_assessment(user, application, responses):
    payload = {"user": user, "application": application, "responses": responses}
    response = requests.post(f"{API_BASE_URL}/verify-skill", json=payload)
    return response.json()

# Fetch Manager View Data
def fetch_manager_view():
    response = requests.get(f"{API_BASE_URL}/manager-view")
    return response.json()["assessments"]

# UI Layout
st.title("🔍 Self-Assessment Tool")
st.sidebar.title("Navigation")
option = st.sidebar.radio("Go to", ["Home", "Manager View"])

if option == "Home":
    st.subheader("📋 Self-Assessment")
    applications = fetch_applications()
    static_questions = fetch_static_questions()

    user = st.text_input("Enter your name")
    application = st.selectbox("Select an Application", applications)
    responses = {}

    for question in static_questions:
        responses[question] = st.slider(question, 1, 5, 3)

    if st.button("Submit Assessment"):
        scores = sum(responses.values()) / len(responses)  # Average Score
        result = submit_assessment(user, application, scores)
        st.session_state["questions"] = result.get("questions", [])

    # Display AI-Generated Questions
    if "questions" in st.session_state:
        st.subheader("🧠 AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.write(f"{i+1}. {question}")

elif option == "Manager View":
    st.subheader("📊 Manager Dashboard")
    data = fetch_manager_view()

    if data:
        st.write("### Past Assessments")
        for record in data:
            st.write(f"**User:** {record[1]}")
            st.write(f"**Application:** {record[2]}")
            st.write(f"**Score:** {record[3]}")
            st.write(f"**Questions:** {json.loads(record[4])}")
            st.write(f"**Answers:** {record[5]}")
            st.write(f"**Score Percentage:** {record[6]}%")
            st.markdown("---")
    else:
        st.write("No data available.")
