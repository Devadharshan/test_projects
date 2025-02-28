from fastapi import FastAPI, HTTPException
import json
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

# Load Open-LLaMA 13B model (stored locally in Windows)
MODEL_PATH = "C:/models/open_llama_13b"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float16, device_map="auto")

# Load application config
def load_app_config():
    with open("app_config.json", "r") as f:
        return json.load(f)

# Load ticket data
def load_ticket_data():
    return pd.read_csv("tickets.csv")

# AI function to generate dynamic questions
def generate_questions(application, user_score, ticket_data):
    prompt = f"""Based on the application {application['name']} which is {application['functionality']} and has a criticality of {application['criticality']}, generate 5 questions for a support engineer. 
    The difficulty should match a self-assessed knowledge level of {user_score}/5. Use the past tickets for context:
    {ticket_data}"""

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    output = model.generate(**inputs, max_length=300)
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    
    questions = generated_text.split("\n")
    return questions[:5]  # Return only 5 questions

# Endpoint to get applications
@app.get("/applications")
def get_applications():
    return {"applications": load_app_config()["applications"]}

# Endpoint to get AI-generated questions
@app.get("/generate_questions/{app_name}/{user_score}")
def get_ai_questions(app_name: str, user_score: int):
    app_config = load_app_config()
    ticket_data = load_ticket_data()

    # Find application
    application = next((app for app in app_config["applications"] if app["name"] == app_name), None)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Filter tickets for the selected app
    filtered_tickets = ticket_data[ticket_data["Application"] == app_name].to_dict(orient="records")

    # Generate AI questions
    questions = generate_questions(application, user_score, filtered_tickets)
    return {"questions": questions}
    
    
    
    
    
    
    import streamlit as st
import requests

# FastAPI API URL
API_URL = "http://127.0.0.1:8000"

st.title("AI-Powered Production Support Assessment")

# Load applications
response = requests.get(f"{API_URL}/applications")
if response.status_code == 200:
    applications = response.json()["applications"]
    app_names = [app["name"] for app in applications]
    selected_app = st.selectbox("Choose an application:", app_names)

    # Get application details
    selected_app_data = next(app for app in applications if app["name"] == selected_app)
    st.write(f"**Functionality:** {selected_app_data['functionality']}")
    st.write(f"**Criticality:** {selected_app_data['criticality']}")

# User self-assessment
st.subheader("Self-Assessment")
user_score = st.slider("Rate your knowledge (1 = Low, 5 = High):", 1, 5, 3)

# Generate AI Questions
if st.button("Generate AI Questions"):
    response = requests.get(f"{API_URL}/generate_questions/{selected_app}/{user_score}")
    if response.status_code == 200:
        ai_questions = response.json()["questions"]
        st.session_state["ai_questions"] = ai_questions
        st.session_state["user_answers"] = [""] * len(ai_questions)

# Show AI Questions
if "ai_questions" in st.session_state:
    st.subheader("AI-Generated Questions")
    for i, question in enumerate(st.session_state["ai_questions"]):
        st.session_state["user_answers"][i] = st.text_input(f"Q{i+1}: {question}", key=f"q{i}")

# Submit Answers
if st.button("Submit Answers"):
    st.success("Answers submitted! AI will evaluate your {
    "applications": [
        {
            "name": "Application A",
            "functionality": "User authentication and access management",
            "criticality": "High"
        },
        {
            "name": "Application B",
            "functionality": "Database management system",
            "criticality": "Critical"
        },
        {
            "name": "Application C",
            "functionality": "Software distribution platform",
            "criticality": "Medium"
        }
    ]
}
    
    