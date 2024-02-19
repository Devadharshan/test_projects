import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

# List of URLs to check
urls_to_check = ["https://example1.com", "https://example2.com", "https://example3.com"]

# Email configuration
sender_email = "your_email@gmail.com"
sender_password = "your_email_password"
receiver_email = "recipient_email@gmail.com"

# Function to check URL status
def check_url_status(url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code
    except requests.exceptions.RequestException as e:
        return str(e)

# Function to send email
def send_email(subject, body, attachment=None):
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, "html"))

    if attachment:
        with open(attachment, "rb") as file:
            attachment_file = MIMEApplication(file.read())
            attachment_file.add_header("Content-Disposition", "attachment", filename="failed_urls.html")
            msg.attach(attachment_file)

    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

# Main script
failed_urls = []

for url in urls_to_check:
    status = check_url_status(url)

    if not isinstance(status, int) or status >= 400:
        failed_urls.append((url, str(status)))

# If there are failed URLs, send an email
if failed_urls:
    subject = "Website Status Report - {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    body = "<h2>Failed URLs:</h2><br><table border='1'><tr><th>URL</th><th>Status Code</th></tr>"

    for url, status_code in failed_urls:
        body += "<tr><td>{}</td><td style='color:red;'>{}</td></tr>".format(url, status_code)

    body += "</table>"
    send_email(subject, body, "failed_urls.html")