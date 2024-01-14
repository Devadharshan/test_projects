import subprocess
import smtplib
from email.mime.text import MIMEText

# Function to get job status from AutoSys
def get_job_status(job_name):
    command = f"autorep -J {job_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

# Function to send email
def send_email(body):
    sender_email = 'your_email@example.com'
    receiver_email = 'recipient@example.com'
    password = 'your_password'
    
    message = MIMEText(body)
    message['Subject'] = 'AutoSys Job Status'
    message['From'] = sender_email
    message['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# List of job patterns to check
job_patterns = ['JOB_PATTERN_1', 'JOB_PATTERN_2', 'JOB_PATTERN_3']

# Collect status for each job pattern
status_info = []
for pattern in job_patterns:
    status = get_job_status(pattern)
    status_info.append(f"Job pattern: {pattern}\n{status}\n\n")

# Send email with status information
email_body = "\n".join(status_info)
send_email(email_body)
