import subprocess
import smtplib
from email.mime.text import MIMEText

# Function to run autorep and extract job information
def get_job_status(job_name):
    command = f"autorep -J {job_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Extract Job Name, Last End, and ST/Ex information
    job_info = [line.split()[0] for line in result.stdout.split('\n')[7:] if line.strip()]
    
    return job_info

# Function to send email
def send_email(job_info):
    sender_email = 'your_email@example.com'
    receiver_email = 'recipient@example.com'
    password = 'your_password'
    
    message = MIMEText("\n".join(job_info), 'plain')
    message['Subject'] = 'AutoSys Job Status Report'
    message['From'] = sender_email
    message['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# Specify the job name to check
job_to_check = 'JOB_NAME_1'

# Get Job Name, Last End, and ST/Ex information
job_info = get_job_status(job_to_check)

# Send email with job information
send_email(job_info)
