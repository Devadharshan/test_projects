import subprocess
import smtplib
from email.mime.text import MIMEText
import requests

# Function to check database connection status
def is_database_connected():
    command = "isql -S <your_sybase_server> -U <your_username> -P <your_password> -w 1000 -b"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return "Login failed" not in result.stderr

# Function to get AutoSys job status with characters 108-109 and 0-28 extracted
def get_job_status(job_name):
    command = f"autorep -J {job_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Extract characters 108-109 and 0-28, and combine them
    status_info = [line[107:109] + line[:28] for line in result.stdout.split('\n')]

    # Filter out unwanted lines and remove empty spaces
    status_info = [line.strip() for line in status_info if line.strip()]

    return status_info

# Function to check URL status
def is_url_reachable(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Function to send email
def send_email(body):
    sender_email = 'your_email@example.com'
    receiver_email = 'recipient@example.com'
    password = 'your_password'
    
    message = MIMEText(body, 'html')  # Set content type to HTML
    message['Subject'] = 'Status Update: Database, Job, and URL'
    message['From'] = sender_email
    message['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# Check database connection status
database_status = "Database Connection is UP." if is_database_connected() else "Database Connection is DOWN."

# List of job patterns to check
job_patterns = ['JOB_PATTERN_1', 'JOB_PATTERN_2', 'JOB_PATTERN_3']

# URL to check
url_to_check = 'https://example.com'

# Check and collect status for each job pattern and URL
status_info = [
    f"<p style='color: blue;'><strong>Database Connection Status:</strong> {database_status}</p>"
]

for pattern in job_patterns:
    job_status = get_job_status(pattern)
    
    # Display the cleaned-up text for job status
    status_info.extend([
        f"<p><strong>Job pattern: {pattern}</strong></p>",
        f"<p style='color: green;'><strong>Job Status (Combined Characters 108-109 and 0-28):</strong> {' '.join(job_status)}</p>"
    ])

# Check URL status
url_status = "URL is reachable." if is_url_reachable(url_to_check) else "URL is not reachable."

# Display URL status in the email body
status_info.append(f"<p style='color: purple;'><strong>URL Status:</strong> {url_status}</p>")

# Send email with status information
email_body = "\n".join(status_info)
send_email(email_body)