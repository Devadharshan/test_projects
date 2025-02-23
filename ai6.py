from fastapi import FastAPI, HTTPException
import sqlite3
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

# Load Model
model_name = "TheBloke/Phi-2-GGUF"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)

# Load Application Config
with open("app_config.json", "r", encoding="utf-8") as f:
    app_config = json.load(f)

# Initialize SQLite
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    application TEXT,
    score INTEGER,
    question TEXT,
    user_response TEXT,
    ai_feedback TEXT,
    percentage_score REAL
)
""")
conn.commit()

@app.post("/verify-skill")
def verify_skill(user: str, application: str, score: int):
    if application not in app_config:
        raise HTTPException(status_code=404, detail="Application not found")

    # Extract application details
    app_details = app_config[application]
    functionality = app_details.get("Functionality", "No details available")
    common_issues = app_details.get("CommonIssues", [])
    criticality = app_details.get("Criticality", "Unknown")

    # Fetch ServiceNow tickets
    cursor.execute("SELECT * FROM tickets WHERE application=?", (application,))
    ticket_data = cursor.fetchall()
    ticket_summaries = [f"Ticket {row[0]}: {row[2]}" for row in ticket_data]  # Assuming row[2] is description

    # Adjust difficulty based on score
    difficulty = "basic" if score <= 2 else "intermediate" if score <= 4 else "advanced"

    # Generate questions
    prompt = (
        f"User rated their skill as {score} ({difficulty} level) for {application}. "
        f"This app is used for {functionality} and has criticality {criticality}. "
        f"Common issues: {', '.join(common_issues)}. "
        f"Recent tickets:\n" + "\n".join(ticket_summaries) +
        f"\nGenerate 5 {difficulty} level questions."
    )

    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(**inputs, max_length=300)
    questions = tokenizer.decode(output[0], skip_special_tokens=True)

    return {"questions": questions.split("\n")}

@app.post("/submit-response")
def submit_response(user: str, application: str, question: str, user_response: str):
    # AI evaluates response
    eval_prompt = f"Evaluate the following answer: '{user_response}' for the question '{question}'. Score it from 0-100%."
    inputs = tokenizer(eval_prompt, return_tensors="pt")
    output = model.generate(**inputs, max_length=200)
    ai_feedback = tokenizer.decode(output[0], skip_special_tokens=True)

    # Extract numerical score
    percentage_score = float([s for s in ai_feedback.split() if s.replace('%', '').isdigit()][0].replace('%', ''))

    cursor.execute("""
    INSERT INTO assessments (user, application, question, user_response, ai_feedback, percentage_score)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user, application, question, user_response, ai_feedback, percentage_score))
    conn.commit()

    return {"feedback": ai_feedback, "score": percentage_score}

@app.get("/manager-view")
def manager_view():
    cursor.execute("SELECT * FROM assessments")
    data = cursor.fetchall()
    return {"assessments": data}






import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Skill Assessment", layout="wide")

# Navigation Menu
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("AI-Powered Skill Assessment")

    user = st.text_input("Enter Your Name")
    application = st.selectbox("Select Application", ["App1", "App2", "App3"])
    score = st.slider("Rate Your Skill (1-5)", 1, 5)

    if st.button("Submit Self-Assessment"):
        response = requests.post(f"{BASE_URL}/verify-skill", json={
            "user": user,
            "application": application,
            "score": score
        })
        if response.status_code == 200:
            questions = response.json()["questions"]
            st.session_state["questions"] = questions
            st.success("Questions generated!")
        else:
            st.error("Error generating questions")

    if "questions" in st.session_state:
        st.subheader("Answer the AI-Generated Questions:")
        for q in st.session_state["questions"]:
            user_answer = st.text_area(q, key=q)
            if st.button(f"Submit Answer: {q}", key=f"btn_{q}"):
                answer_response = requests.post(f"{BASE_URL}/submit-response", json={
                    "user": user,
                    "application": application,
                    "question": q,
                    "user_response": user_answer
                })
                if answer_response.status_code == 200:
                    feedback = answer_response.json()
                    st.write(f"**AI Feedback:** {feedback['feedback']}")
                    st.write(f"**Score:** {feedback['score']}%")
                else:
                    st.error("Error submitting response")

elif page == "Manager View":
    st.title("Manager View - Assessments Data")

    response = requests.get(f"{BASE_URL}/manager-view")
    if response.status_code == 200:
        assessments = response.json()["assessments"]
        if assessments:
            st.table(assessments)
        else:
            st.write("No assessments found.")
    else:
        st.error("Error fetching assessments")
