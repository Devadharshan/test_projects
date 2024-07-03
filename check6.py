import yaml
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tabulate import tabulate

def read_urls_from_yaml(file_path):
    with open(file_path, 'r') as file:
        urls = yaml.safe_load(file)
        return urls.get('urls', [])

def check_url_status(url):
    try:
        response = requests.get(url)
        return response.status_code
    except requests.exceptions.RequestException as e:
        return str(e)

def generate_status_report(url_statuses):
    table = []
    for url, status in url_statuses.items():
        table.append([url, status])
    report = tabulate(table, headers=['URL', 'Status'], tablefmt='grid')
    return report

def send_email(sender_email, sender_password, receiver_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

def main():
    # Step 1: Read URLs from YAML file
    urls = read_urls_from_yaml('urls.yaml')

    # Step 2: Check URL Status
    url_statuses = {}
    for url in urls:
        url_statuses[url] = check_url_status(url)

    # Step 3: Generate Status Report
    status_report = generate_status_report(url_statuses)
    print(status_report)  # For testing purposes, you can print the report

    # Step 4: Send Email
    sender_email = 'your_email@gmail.com'
    sender_password = 'your_password'
    receiver_email = 'recipient@example.com'
    subject = 'URL Status Report'
    body = status_report

    send_email(sender_email, sender_password, receiver_email, subject, body)

if __name__ == "__main__":
    main()