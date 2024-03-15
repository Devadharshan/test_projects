import csv
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def check_url_status(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return "Success"
        else:
            return f"Failed with status code {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Failed with exception: {str(e)}"

def send_email(subject, body):
    sender_email = "your_email@example.com"
    receiver_email = "recipient@example.com"
    password = "your_email_password"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.example.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def main():
    failed_urls = []
    with open('urls.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            url = row[0]
            status = check_url_status(url)
            if "Failed" in status:
                failed_urls.append((url, status))

    if failed_urls:
        subject = "URL Status Report - Failures Detected"
        body = "\n".join([f"URL: {url}, Status: {status}" for url, status in failed_urls])
        send_email(subject, body)

if __name__ == "__main__":
    main()