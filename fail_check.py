import csv
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def check_url(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code
    except requests.exceptions.RequestException as e:
        return str(e)

def send_email(url, status):
    # Email configuration
    sender_email = 'your_email@gmail.com'  # Update with your email
    sender_password = 'your_password'  # Update with your password
    receiver_email = 'recipient@example.com'  # Update with recipient email
    subject = 'Website Down or Timing Out'
    
    # Email content
    body = f"<p>URL: {url}<br>Status: {status}</p>"
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))
    
    # Sending email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully.")

def main():
    with open('websites.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            url = row['url']
            status_code = check_url(url)
            if isinstance(status_code, int):
                if status_code != 200:
                    send_email(url, f"Error - Status Code: {status_code}")
            else:
                send_email(url, f"Error - {status_code}")

if __name__ == "__main__":
    main()
