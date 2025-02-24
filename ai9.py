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