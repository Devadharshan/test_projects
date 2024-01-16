import subprocess
import smtplib
from email.mime.text import MIMEText
import pandas as pd

# Function to check Sybase server status
def is_sybase_server_up():
    command = "isql -S <your_sybase_server> -U <your_username> -P <your_password> -w 1000 -b"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return "Login failed" not in result.stderr

# Function to get AutoSys job status as a Pandas DataFrame
def get_job_status(job_name):
    command = f"autorep -J {job_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Extract only the relevant status information
    status_lines = [line.strip() for line in result.stdout.split('\n') if 'Status' in line]
    
    # Assuming the status information has a structured format
    df = pd.DataFrame([line.split(':') for line in status_lines], columns=['Field', 'Value'])
    
    return df

# Function to send email
def send_email(body):
    sender_email = 'your_email@example.com'
    receiver_email = 'recipient@example.com'
    password = 'your_password'
    
    message = MIMEText(body, 'html')  # Set content type to HTML
    message['Subject'] = 'AutoSys Job and Sybase Server Status'
    message['From'] = sender_email
    message['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# Check Sybase server status
sybase_status = "Sybase Server is UP." if is_sybase_server_up() else "Sybase Server is DOWN."

# List of job patterns to check
job_patterns = ['JOB_PATTERN_1', 'JOB_PATTERN_2', 'JOB_PATTERN_3']

# Collect and display status for each job pattern
status_info = [sybase_status]
for pattern in job_patterns:
    job_status_df = get_job_status(pattern)

    # Display the DataFrame in the email body
    status_info.extend([
        f"<p><strong>Job pattern: {pattern}</strong></p>",
        f"<p style='color: green;'><strong>Sybase Server Status:</strong> {sybase_status}</p>",
        f"<p style='color: green;'><strong>Job Status:</strong></p>",
        job_status_df.to_html(index=False)
    ])

# Send email with status information
email_body = "\n".join(status_info)
send_email(email_body)
