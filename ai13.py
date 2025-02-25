from fastapi import FastAPI, HTTPException
import json
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Load Application Config
with open("app_conf.json", "r") as f:
    applications_data = json.load(f)
applications = applications_data["Application"]

# Load ServiceNow Data (CSV)
df = pd.read_csv("servicenow_tickets.csv")

# Load AI Model (Phi-2)
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Ensure tokenizer has pad_token
if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token


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


# Store responses (acting as DB)
db = []


@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}


@app.get("/static-questions")
def get_static_questions():
    return {"questions": applications_data["StaticQuestions"]}


@app.post("/verify-skill")
def verify_skill(data: SelfAssessmentRequest):
    """Generates AI-based validation questions."""
    user_score = sum(data.static_answers) / len(data.static_answers)

    # Select ServiceNow tickets for the application
    app_tickets = df[df["Application"] == data.application]

    # Generate AI Question Prompt
    prompt = f"User rated themselves {user_score} on {data.application}. Based on this, generate {len(data.static_answers)} scenario-based validation questions."

    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=250)
    
    outputs = model.generate(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], max_length=500)
    
    ai_questions = tokenizer.decode(outputs[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": ai_questions[:len(data.static_answers)]}  # Ensure correct question count


@app.post("/submit-responses")
def submit_responses(data: AnswerSubmissionRequest):
    """Stores user responses and evaluates answers."""
    db.append(data.dict())  # Save to DB

    final_score = sum(data.static_answers) * 5  # Dummy scoring logic

    return {"final_score": final_score}


@app.get("/manager-view")
def manager_view():
    """Returns stored assessments."""
    return {"assessments": db}





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
        st.error("Error fetching applications")
        applications = []

    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Fetch Static Questions
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
            st.error("Error generating AI questions")
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
        st.write(pd.DataFrame(assessments))
    except:
        st.error("Error fetching manager data")
