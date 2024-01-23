import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(body):
    sender_email = "your_email@example.com"  # Replace with your email
    receiver_email = "receiver_email@example.com"  # Replace with recipient email
    password = "your_password"  # Replace with your email password

    subject = "Failed URL Status Report"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Email body with the failed URLs
    part = MIMEText(body, "plain")
    message.attach(part)

    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:  # Replace with your SMTP server details
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def send_failed_urls(csv_file):
    failed_urls = []  # To store failed URLs

    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header if exists
        for row in csv_reader:
            url, status = row[0], row[1]
            if status.lower() != 'up':
                failed_urls.append(f"{url} is {status}")

    # Constructing plain text body from failed URLs
    body = "\n".join(failed_urls)

    # Send email with failed URLs in the body
    if failed_urls:
        send_email(body)
        print("Email sent successfully.")
    else:
        print("No failed URLs to report.")

# Replace 'url_status_results.csv' with the path to your output CSV file
send_failed_urls('url_status_results.csv')