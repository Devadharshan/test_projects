import streamlit as st
import subprocess

def get_job_status(job_name):
    try:
        # Run the autosys_secure command to get the job status
        result = subprocess.run(['autosys_secure', '-j', job_name], capture_output=True, text=True)
        output = result.stdout
        status = output.split('\n')[1].split(':')[1].strip()
        return status
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.title("Autosys Job Status Checker")
    job_name = st.text_input("Enter job name:")

    if st.button("Check Status"):
        if job_name:
            job_status = get_job_status(job_name)
            st.write(f"Job '{job_name}' status is: {job_status}")
        else:
            st.write("Please enter a job name.")

if __name__ == "__main__":
    main()