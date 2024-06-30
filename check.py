import requests
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def verify_https_status(check):
    url = check['url']
    expected_status = check['expected_status']

    try:
        response = requests.get(url)
        if response.status_code == expected_status:
            return f"{url} is reachable and returns status {expected_status}"
        else:
            return f"{url} returned status {response.status_code}, expected {expected_status}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to {url}: {e}"

def send_email(results):
    # Email configuration
    sender_email = 'your_email@example.com'
    receiver_email = 'recipient_email@example.com'
    password = 'your_email_password'
    
    # Email content
    message = MIMEMultipart("alternative")
    message["Subject"] = "HTTPS Status Check Results"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Create HTML content for the email body
    html = "<html><body>"
    html += "<h2>HTTPS Status Check Results:</h2>"
    for result in results:
        html += f"<p>{result}</p>"
    html += "</body></html>"

    # Attach HTML content to the email
    mime_html = MIMEText(html, "html")
    message.attach(mime_html)

    # Connect to SMTP server and send email
    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def main():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    results = []
    if 'checks' in config:
        for check in config['checks']:
            result = verify_https_status(check)
            results.append(result)
    else:
        print("No 'checks' found in config.yaml")
    
    # Send email with results
    send_email(results)
    print("Email sent successfully")

if __name__ == '__main__':
    main()
