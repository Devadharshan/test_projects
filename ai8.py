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
            st.success("AI has generated validation questions!")
        else:
            st.error("Error verifying skill.")
    else:
        st.warning("Please select an application first.")

# Step 4: Display AI-Generated Questions
if "ai_questions" in st.session_state:
    st.subheader("AI-Generated Questions (Answer Below)")
    user_responses = []
    for q in st.session_state["ai_questions"]:
        user_responses.append(st.text_area(q, ""))

    # Step 5: Submit AI-Generated Responses
    if st.button("Submit Responses"):
        payload = {
            "user": "test_user",  # Placeholder
            "ai_responses": user_responses
        }
        response = requests.post(f"{API_BASE_URL}/submit-responses", json=payload)
        if response.status_code == 200:
            final_score = response.json().get("final_score", 0)
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

--
Task Number,Application,Short Description,Close Notes,Created On
INC001,App1,Login failure,Password reset,2023-12-15
INC002,App2,API timeout,Increased timeout,2023-11-10
INC003,App1,Data inconsistency,DB sync,2024-01-05



---
from fastapi import FastAPI, HTTPException
import json
import pandas as pd
import random

app = FastAPI()

# Load application config
with open("app_conf.json", "r") as f:
    applications_data = json.load(f)
applications = applications_data["Application"]

# Path to the large CSV file
CSV_FILE_PATH = "servicenow_tickets.csv"

# Load tickets efficiently (read only needed columns)
def load_tickets():
    try:
        df = pd.read_csv(CSV_FILE_PATH, usecols=["Task Number", "Application", "Short Description", "Close Notes", "Created On"], parse_dates=["Created On"])
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

service_now_tickets = load_tickets()

# Store user responses
user_assessments = {}

@app.get("/applications")
def get_applications():
    return {"applications": list(applications.keys())}

@app.get("/static-questions")
def get_static_questions():
    return {"questions": [
        "How well do you understand this application?",
        "How often have you worked with this application?",
        "How confident are you in troubleshooting this application?",
        "How well can you explain this application to others?",
        "How well do you know this application’s architecture?"
    ]}

@app.post("/verify-skill")
def verify_skill(data: dict):
    user = data.get("user")
    application = data.get("application")
    static_answers = data.get("static_answers", [])

    if not user or not application:
        raise HTTPException(status_code=400, detail="User and application are required")

    score = sum(static_answers) / len(static_answers)  # Avg Score (1-5)

    # Determine question complexity
    if score <= 2:
        difficulty = "basic"
    elif score == 3:
        difficulty = "moderate"
    else:
        difficulty = "advanced"

    # Reload CSV data in case it was updated
    global service_now_tickets
    service_now_tickets = load_tickets()

    # Filter only relevant tickets
    relevant_tickets = service_now_tickets[service_now_tickets["Application"].str.strip() == application]

    # Filter tickets from the last 6 months (if applicable)
    if "Created On" in relevant_tickets.columns:
        relevant_tickets = relevant_tickets[relevant_tickets["Created On"] >= pd.Timestamp.now() - pd.DateOffset(months=6)]

    # Select random 10 tickets to avoid repetition
    relevant_tickets = relevant_tickets.sample(min(len(relevant_tickets), 10), random_state=42)

    # Generate AI questions
    ai_questions = []
    for _, ticket in relevant_tickets.iterrows():
        if difficulty == "basic":
            ai_questions.append(f"What was the issue in ticket {ticket.get('Task Number', 'Unknown')}?")
        elif difficulty == "moderate":
            ai_questions.append(f"How was ticket {ticket.get('Task Number', 'Unknown')} resolved?")
        else:
            ai_questions.append(f"What was the root cause of ticket {ticket.get('Task Number', 'Unknown')}?")

    # Save initial assessment
    user_assessments[user] = {
        "application": application,
        "static_answers": static_answers,
        "ai_questions": ai_questions,
        "ai_responses": [],
        "final_score": None
    }

    return {"ai_questions": ai_questions}

@app.post("/submit-responses")
def submit_responses(data: dict):
    user = data.get("user")
    ai_responses = data.get("ai_responses", [])

    if user not in user_assessments:
        raise HTTPException(status_code=400, detail="Assessment not found")

    # AI verification logic (simple matching for now)
    correct_answers = sum(1 for answer in ai_responses if answer.strip())  # Count non-empty answers
    final_score = (correct_answers / len(ai_responses)) * 100 if ai_responses else 0

    # Update user data
    user_assessments[user]["ai_responses"] = ai_responses
    user_assessments[user]["final_score"] = final_score

    return {"final_score": final_score}

@app.get("/manager-view")
def manager_view():
    return {"assessments": [
        {"User": user, **data} for user, data in user_assessments.items()
    ]}



---
@app.post("/verify-skill")
def verify_skill(data: dict):
    user = data["user"]
    application = data["application"]
    static_answers = data["static_answers"]
    score = data["score"]

    # Determine question complexity based on score
    if score <= 2:
        difficulty = "basic"
    elif score == 3:
        difficulty = "moderate"
    else:
        difficulty = "advanced"

    # Fetch past tickets for the selected application
    relevant_tickets = []
    for ticket in service_now_tickets:  # Assuming this is a preloaded list of tickets
        if ticket["Application"] == application:
            relevant_tickets.append(ticket)

    # Generate AI questions based on ticket history and difficulty level
    ai_questions = []
    for ticket in relevant_tickets[:5]:  # Limit to 5 relevant tickets
        if difficulty == "basic":
            ai_questions.append(f"What is the main issue reported in ticket {ticket['Task Number']}?")
        elif difficulty == "moderate":
            ai_questions.append(f"How was ticket {ticket['Task Number']} resolved?")
        else:
            ai_questions.append(f"What root cause was identified for ticket {ticket['Task Number']}?")

    return {"ai_questions": ai_questions}


---import streamlit as st
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
        if response.status_code == 200:
            applications = response.json().get("applications", [])
        else:
            st.error(f"Error fetching applications: {response.text}")
            applications = []
    except (requests.exceptions.RequestException, ValueError):
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
    try:
        response = requests.get(f"{API_URL}/static-questions")
        if response.status_code == 200:
            static_questions = response.json().get("questions", [])
        else:
            st.error(f"Error fetching static questions: {response.text}")
            static_questions = []
    except (requests.exceptions.RequestException, ValueError):
        st.error("Error fetching static questions")
        static_questions = []

    static_answers = []
    st.subheader("Static Questions (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.selectbox(f"Q{i+1}: {question}", [1, 2, 3, 4, 5], index=2, key=f"static_{i}")
        static_answers.append(answer)

    if st.button("Submit Self-Assessment"):
        if not user or not selected_application:
            st.error("Please enter your name and select an application.")
        else:
            score = sum(static_answers) / len(static_answers)  # Average Score

            payload = {
                "user": user,
                "application": selected_application,
                "score": score,
                "static_answers": static_answers
            }

            try:
                response = requests.post(f"{API_URL}/verify-skill", json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    questions = response_data.get("ai_questions", [])
                else:
                    st.error(f"Error processing assessment: {response.text}")
                    questions = []
            except (requests.exceptions.RequestException, ValueError):
                st.error("Error processing your assessment")
                questions = []

            st.session_state["questions"] = questions
            st.session_state["answers"] = [""] * len(questions)

    if "questions" in st.session_state:
        st.subheader("AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        if st.button("Submit Responses"):
            if not st.session_state["answers"]:
                st.error("Please answer all questions before submitting.")
            else:
                payload = {
                    "user": user,
                    "application": selected_application,
                    "static_answers": static_answers,
                    "ai_questions": st.session_state["questions"],
                    "ai_responses": st.session_state["answers"]
                }
                try:
                    response = requests.post(f"{API_URL}/submit-responses", json=payload)
                    if response.status_code == 200:
                        response_data = response.json()
                        final_score = response_data.get("final_score", "N/A")
                        ai_responses = response_data.get("responses", [])
                    else:
                        st.error(f"Error submitting responses: {response.text}")
                        final_score = "N/A"
                        ai_responses = []
                except (requests.exceptions.RequestException, ValueError, KeyError, TypeError):
                    st.error("Error submitting responses")
                    final_score = "N/A"
                    ai_responses = []

                st.success(f"Final Score: {final_score}%")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        if response.status_code == 200:
            assessments = response.json().get("assessments", [])
            df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
            st.write(df)
        else:
            st.error(f"Error fetching manager data: {response.text}")
    except (requests.exceptions.RequestException, ValueError):
        st.error("Error fetching manager data")



p-----
if st.button("Submit Self-Assessment"):
    payload = {
        "user": user,
        "application": selected_application,
        "score": sum(static_answers) / len(static_answers),  # Calculate average score
        "static_answers": static_answers
    }

----
@app.post("/verify-skill")
def verify_skill(payload: dict):
    user = payload.get("user", "")
    application = payload.get("application", "")
    score = payload.get("score", None)  # Use .get() to avoid KeyError
    static_answers = payload.get("static_answers", [])

    if not user or not application:
        raise HTTPException(status_code=400, detail="User or application missing")
    
    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    if score is None:
        raise HTTPException(status_code=400, detail="Score missing in request")

    # Get Tickets for the selected application
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Construct AI Prompt
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"Here are their answers:\n"
    )

    for q, ans in zip(STATIC_QUESTIONS, static_answers):
        input_prompt += f"Q: {q}\nA: {ans}\n"

    input_prompt += "\nHere are past ServiceNow issues:\n"
    
    # Limit ticket history to avoid exceeding model input limits
    for _, row in app_tickets.head(5).iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += "Generate 5 questions to test the user’s skill."

    # **Tokenize with truncation**
    inputs = tokenizer(input_prompt, return_tensors="pt", truncation=True, max_length=1024)

    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)

    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": [q for q in questions if q.strip()]}


----
@app.post("/verify-skill")
def verify_skill(payload: dict):
    user = payload["user"]
    application = payload["application"]
    score = payload["score"]
    static_answers = payload["static_answers"]

    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    # Get Tickets
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Construct AI Prompt
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"Here are their answers:\n"
    )

    for q, ans in zip(STATIC_QUESTIONS, static_answers):
        input_prompt += f"Q: {q}\nA: {ans}\n"

    input_prompt += "\nHere are past ServiceNow issues:\n"
    
    # Limit to last 5 tickets to reduce token count
    for _, row in app_tickets.head(5).iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += "Generate 5 questions to test the user’s skill."

    # **Tokenize with truncation**
    inputs = tokenizer(input_prompt, return_tensors="pt", truncation=True, max_length=1024)

    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)

    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")

    return {"ai_questions": [q for q in questions if q.strip()]}


import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

if page == "Self-Assessment":
    st.title("Self-Assessment")

    # Get Applications with 400 Error Handling
    try:
        response = requests.get(f"{API_URL}/applications")
        if response.status_code == 200:
            applications = response.json().get("applications", [])
        else:
            st.error(f"Error fetching applications: {response.status_code}")
            applications = []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name").strip()
    selected_application = st.selectbox("Select Application", applications if applications else ["No applications found"])

    # Static Questions with 400 Error Handling
    try:
        response = requests.get(f"{API_URL}/static-questions")
        if response.status_code == 200:
            static_questions = response.json().get("questions", [])
        else:
            st.error(f"Error fetching static questions: {response.status_code}")
            static_questions = []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        static_questions = []

    static_answers = []
    st.subheader("Static Questions (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.selectbox(f"Q{i+1}: {question}", [1, 2, 3, 4, 5], index=2, key=f"static_{i}")
        static_answers.append(answer)

    # Submit Self-Assessment with 400 Error Handling
    if st.button("Submit Self-Assessment"):
        if not user:
            st.error("Please enter your name.")
        elif selected_application == "No applications found":
            st.error("No applications available to select.")
        else:
            payload = {
                "user": user,
                "application": selected_application,
                "static_answers": static_answers
            }
            try:
                response = requests.post(f"{API_URL}/verify-skill", json=payload)
                if response.status_code == 200:
                    questions = response.json().get("ai_questions", [])
                    st.session_state["questions"] = questions
                    st.session_state["answers"] = [""] * len(questions)
                else:
                    st.error(f"Error processing assessment: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {e}")

    # AI-Generated Questions Section
    if "questions" in st.session_state and st.session_state["questions"]:
        st.subheader("AI-Generated Questions")
        if "answers" not in st.session_state:
            st.session_state["answers"] = [""] * len(st.session_state["questions"])

        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        # Submit AI Responses
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
                if response.status_code == 200:
                    final_score = response.json().get("final_score", "N/A")
                    st.success(f"Final Score: {final_score}%")
                else:
                    st.error(f"Error submitting responses: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {e}")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{API_URL}/manager-view")
        if response.status_code == 200:
            assessments = response.json().get("assessments", [])
            df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
            st.write(df)
        else:
            st.error(f"Error fetching manager data: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")



----
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
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
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
            st.session_state["questions"] = questions
            st.session_state["answers"] = [""] * len(questions)  # Fixes KeyError
        except:
            st.error("Error processing your assessment")
            st.session_state["questions"] = []
            st.session_state["answers"] = []

    if "questions" in st.session_state and st.session_state["questions"]:
        st.subheader("AI-Generated Questions")
        if "answers" not in st.session_state:
            st.session_state["answers"] = [""] * len(st.session_state["questions"])  # Ensure answers exist

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
        df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
        st.write(df)
    except:
        st.error("Error fetching manager data")


----
from fastapi import FastAPI, HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sqlite3
import pandas as pd
import json
import logging

app = FastAPI()

# Load Applications
with open("applications.json", "r") as f:
    applications = json.load(f)["applications"]

# Load Ticket Data
ticket_data = pd.read_csv("servicenow_tickets.csv").fillna("Unknown")

# Load AI Model
MODEL_PATH = "C:/Users/YourUsername/phi-2/"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float32)

# Database
conn = sqlite3.connect("assessment.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    application TEXT,
    score INTEGER,
    static_answers TEXT,
    ai_questions TEXT,
    ai_responses TEXT,
    final_score REAL
)
""")
conn.commit()

# Static Questions
STATIC_QUESTIONS = [
    "How familiar are you with this application's core infrastructure?",
    "Have you resolved any major issues related to this application?",
    "Do you understand its dependencies?",
    "Have you optimized its performance?",
    "Can you troubleshoot critical failures?"
]

@app.get("/static-questions")
def get_static_questions():
    return {"questions": STATIC_QUESTIONS}

@app.post("/verify-skill")
def verify_skill(payload: dict):
    user = payload["user"]
    application = payload["application"]
    static_answers = payload["static_answers"]
    score = sum(static_answers) / len(static_answers)  # Average static score

    if application not in applications:
        raise HTTPException(status_code=400, detail="Application not found")

    # Get Tickets for Application
    app_tickets = ticket_data[ticket_data["Application"] == application]

    # Construct AI Prompt
    input_prompt = (
        f"User rated themselves {score}/5 for {application}. "
        f"Here are their answers:\n"
    )

    for q, ans in zip(STATIC_QUESTIONS, static_answers):
        input_prompt += f"Q: {q}\nA: {ans}\n"

    input_prompt += "\nPast ServiceNow Tickets:\n"
    for _, row in app_tickets.iterrows():
        input_prompt += f"- {row['Short Description']}\n"

    input_prompt += f"\nGenerate 5 questions that assess a user with skill level {score}/5."

    inputs = tokenizer(input_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=250)

    questions = tokenizer.decode(output[0], skip_special_tokens=True).split("\n")
    return {"ai_questions": [q for q in questions if q.strip()]}

@app.post("/submit-responses")
def submit_responses(payload: dict):
    user = payload["user"]
    application = payload["application"]
    static_answers = payload["static_answers"]
    ai_questions = payload["ai_questions"]
    ai_responses = payload["ai_responses"]

    # Validate Responses using AI
    validation_prompt = "Evaluate these answers (0-100):\n"
    for q, r in zip(ai_questions, ai_responses):
        validation_prompt += f"Q: {q}\nA: {r}\n"

    inputs = tokenizer(validation_prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_length=100)

    final_score = float(tokenizer.decode(output[0], skip_special_tokens=True).strip().split()[-1])

    cursor.execute("INSERT INTO assessments (user, application, score, static_answers, ai_questions, ai_responses, final_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (user, application, sum(static_answers) / len(static_answers), json.dumps(static_answers), json.dumps(ai_questions), json.dumps(ai_responses), final_score))
    conn.commit()

    return {"final_score": final_score}

@app.get("/manager-view")
def manager_view():
    cursor.execute("SELECT * FROM assessments")
    data = cursor.fetchall()
    return {"assessments": data}






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
        st.error("Error connecting to backend")
        applications = []

    # User Input
    user = st.text_input("Enter Your Name")
    selected_application = st.selectbox("Select Application", applications)

    # Static Questions with Dropdown
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
            st.error("Error processing your assessment")
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
        df = pd.DataFrame(assessments, columns=["ID", "User", "Application", "Static Answers", "AI Questions", "AI Responses", "Final Score"])
        st.write(df)
    except:
        st.error("Error fetching manager data")
