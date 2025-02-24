import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

# Page Title
st.title("Skill Verification for ServiceNow Applications")

# Step 1: Get available applications
st.subheader("Select an Application")

response = requests.get(f"{API_BASE_URL}/applications")
if response.status_code == 200:
    applications = response.json().get("applications", [])
    selected_application = st.selectbox("Choose an application", applications)
else:
    st.error("Failed to fetch applications.")
    selected_application = None

# Step 2: Static Self-Assessment
st.subheader("Self-Assessment (Rate 1-5)")

response = requests.get(f"{API_BASE_URL}/static-questions")
if response.status_code == 200:
    questions = response.json().get("questions", [])
    static_answers = []
    for q in questions:
        static_answers.append(st.slider(q, 1, 5, 3))
else:
    st.error("Failed to fetch static questions.")

# Step 3: Submit Self-Assessment & Get AI Questions
if st.button("Submit Self-Assessment"):
    if selected_application:
        payload = {
            "user": "test_user",  # Placeholder for user identity
            "application": selected_application,
            "static_answers": static_answers
        }
        response = requests.post(f"{API_BASE_URL}/verify-skill", json=payload)
        if response.status_code == 200:
            ai_questions = response.json().get("ai_questions", [])
            st.session_state["ai_questions"] = ai_questions
            st.session_state["ai_responses"] = [""] * len(ai_questions)  # Placeholder for answers
            st.success("AI has generated validation questions!")
        else:
            st.error("Error verifying skill.")
    else:
        st.warning("Please select an application first.")

# Step 4: Display AI-Generated Questions
if "ai_questions" in st.session_state:
    st.subheader("AI-Generated Questions (Answer Below)")
    for i, q in enumerate(st.session_state["ai_questions"]):
        st.session_state["ai_responses"][i] = st.text_area(f"Q{i+1}: {q}", st.session_state["ai_responses"][i])

    # Step 5: Submit AI-Generated Responses for Verification
    if st.button("Submit Responses"):
        payload = {
            "user": "test_user",  # Placeholder
            "application": selected_application,
            "static_answers": static_answers,
            "ai_questions": st.session_state["ai_questions"],
            "ai_responses": st.session_state["ai_responses"]
        }
        response = requests.post(f"{API_BASE_URL}/submit-responses", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            final_score = response_data.get("final_score", 0)
            st.success(f"AI Verified Your Answers! Final Score: {final_score}%")
        else:
            st.error("Error submitting responses.")

# Manager View (For Review)
st.subheader("Manager View")
if st.button("View Submissions"):
    response = requests.get(f"{API_BASE_URL}/manager-view")
    if response.status_code == 200:
        submissions = response.json().get("assessments", [])
        if submissions:
            st.write(submissions)
        else:
            st.info("No submissions yet.")
    else:
        st.error("Failed to fetch submissions.")





import json
import pandas as pd
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

# Load application config
with open("app_conf.json", "r") as f:
    applications_data = json.load(f)
applications = applications_data["Application"]

# Load ServiceNow Tickets CSV
ticket_data = pd.read_csv("servicenow_tickets.csv")

# Load AI Model (Phi-2)
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Define Request Schema
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

# Get Available Applications
@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}

# Generate AI-Based Questions
def generate_questions(application: str, scores: list[int]):
    """
    Uses past ServiceNow tickets to generate AI questions relevant to the user's skill level.
    """
    relevant_tickets = ticket_data[ticket_data["Application"] == application]
    selected_tickets = relevant_tickets.sample(min(5, len(relevant_tickets)))  # Pick 5 random tickets

    questions = []
    for index, row in selected_tickets.iterrows():
        prompt = f"Given a ServiceNow ticket: {row['Short Description']} - {row['Close Notes']}, generate a question "
        if scores[0] < 3:  # If self-score is low, easier questions
            prompt += "that helps beginners understand how to troubleshoot this issue."
        else:
            prompt += "that challenges an experienced support engineer."

        input_ids = tokenizer(prompt, return_tensors="pt").input_ids
        output_ids = model.generate(input_ids, max_length=100)
        question = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        questions.append(question)

    return questions

# Verify Skill & Generate Questions
@app.post("/verify-skill")
def verify_skill(request: SkillVerificationRequest):
    if request.application not in applications:
        raise HTTPException(status_code=400, detail="Invalid application.")

    ai_questions = generate_questions(request.application, request.static_answers)
    return {"ai_questions": ai_questions}

# Verify User Responses
@app.post("/submit-responses")
def submit_responses(request: ResponseVerificationRequest):
    """
    AI evaluates the user’s answers based on historical ServiceNow tickets.
    """
    correct_responses = 0
    total_questions = len(request.ai_questions)

    for q, user_answer in zip(request.ai_questions, request.ai_responses):
        input_ids = tokenizer(f"Question: {q} | Answer: {user_answer} | Is this correct?", return_tensors="pt").input_ids
        output_ids = model.generate(input_ids, max_length=50)
        ai_verdict = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        if "Yes" in ai_verdict or "Correct" in ai_verdict:
            correct_responses += 1

    final_score = (correct_responses / total_questions) * 100 if total_questions > 0 else 0
    return {"final_score": final_score}

# Manager View - Retrieve Assessments
@app.get("/manager-view")
def manager_view():
    return {"assessments": []}  # This can be improved by storing previous results