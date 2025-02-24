import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

# Fetch applications
st.title("Self-Assessment Tool")
apps_response = requests.get(f"{API_BASE_URL}/applications")
applications = apps_response.json()["applications"] if apps_response.status_code == 200 else []

# User selects application
user_name = st.text_input("Enter your name:")
selected_app = st.selectbox("Select an application:", applications)

# Fetch static questions
static_questions = requests.get(f"{API_BASE_URL}/static-questions").json()["questions"]
static_answers = []

# User rates themselves (1-5) on static questions
st.subheader("Rate yourself on the following questions (1 = Low, 5 = High):")
for i, question in enumerate(static_questions):
    static_answers.append(st.slider(question, 1, 5, 3))

if st.button("Submit Self-Assessment"):
    # Request AI-generated questions
    skill_data = {
        "user": user_name,
        "application": selected_app,
        "static_answers": static_answers
    }
    ai_response = requests.post(f"{API_BASE_URL}/verify-skill", json=skill_data)
    
    if ai_response.status_code == 200:
        ai_questions = ai_response.json()["ai_questions"]
        user_responses = []

        # AI Questions Section
        st.subheader("Answer AI-Generated Questions:")
        for i, q in enumerate(ai_questions):
            user_responses.append(st.text_area(q, key=f"ai_q_{i}"))

        if st.button("Submit Answers"):
            # Submit AI responses
            submit_data = {
                "user": user_name,
                "application": selected_app,
                "static_answers": static_answers,
                "ai_questions": ai_questions,
                "ai_responses": user_responses
            }
            submit_response = requests.post(f"{API_BASE_URL}/submit-responses", json=submit_data)
            if submit_response.status_code == 200:
                st.success(f"Final Score: {submit_response.json()['final_score']}%")

# Manager View
if st.checkbox("Show Manager View"):
    manager_response = requests.get(f"{API_BASE_URL}/manager-view")
    if manager_response.status_code == 200:
        st.write(manager_response.json())