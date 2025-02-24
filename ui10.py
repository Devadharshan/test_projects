import streamlit as st
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Self-Assessment", "Manager View"])

# Fetch Applications
@st.cache_data
def get_applications():
    try:
        response = requests.get(f"{BASE_URL}/applications")
        return response.json().get("applications", [])
    except:
        st.error("Error fetching applications")
        return []

if page == "Self-Assessment":
    st.title("Self-Assessment")

    user = st.text_input("Enter Your Name")
    applications = get_applications()
    selected_app = st.selectbox("Select Application", applications)

    static_questions = [
        "How do you handle incident resolution?",
        "Can you describe the impact analysis process?",
        "What steps do you take in root cause analysis?",
        "How do you ensure documentation for a resolved issue?",
        "Explain a troubleshooting method you often use."
    ]

    static_answers = []
    st.subheader("Self-Assessment (Rate 1-5)")
    for i, question in enumerate(static_questions):
        answer = st.slider(f"Q{i+1}: {question}", 1, 5, 3)
        static_answers.append(answer)

    if st.button("Submit Self-Assessment"):
        if not user or not selected_app:
            st.error("Please enter your name and select an application")
        else:
            payload = {
                "user": user,
                "application": selected_app,
                "static_answers": static_answers
            }
            try:
                response = requests.post(f"{BASE_URL}/verify-skill", json=payload)
                ai_questions = response.json().get("ai_questions", [])
                st.session_state["questions"] = ai_questions
                st.session_state["answers"] = [""] * len(ai_questions)
            except:
                st.error("Error verifying skill")

    if "questions" in st.session_state:
        st.subheader("AI-Generated Questions")
        for i, question in enumerate(st.session_state["questions"]):
            st.session_state["answers"][i] = st.text_area(f"Q{i+1}: {question}", st.session_state["answers"][i])

        if st.button("Submit Responses"):
            payload = {
                "user": user,
                "application": selected_app,
                "static_answers": static_answers,
                "ai_questions": st.session_state["questions"],
                "ai_responses": st.session_state["answers"]
            }
            try:
                response = requests.post(f"{BASE_URL}/submit-responses", json=payload)
                final_score = response.json().get("final_score", "N/A")
                st.success(f"Final Score: {final_score}%")
            except:
                st.error("Error submitting responses")

elif page == "Manager View":
    st.title("Manager View")

    try:
        response = requests.get(f"{BASE_URL}/manager-view")
        assessments = response.json().get("assessments", [])
        for assessment in assessments:
            st.write(f"User: {assessment['user']} | Application: {assessment['application']} | Final Score: {assessment['final_score']}% | Time: {assessment['timestamp']}")
    except:
        st.error("Error fetching manager data")