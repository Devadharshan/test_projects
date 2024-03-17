import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import autosys


def send_email(subject, body, to_email, smtp_server, smtp_port, sender_email, sender_password):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, to_email, text)
    server.quit()


def check_job_status(pattern, autosys_server, autosys_port, email_settings):
    client = autosys.client.Client(hostname=autosys_server, port=autosys_port)

    failed_jobs = []

    for job in client.get_jobs():
        if pattern in job.name:
            if job.status == 'FA':
                failed_jobs.append(job.name)

    client.disconnect()

    if failed_jobs:
        subject = "Autosys Job Failure Notification"
        body = "The following Autosys jobs have failed:\n\n" + "\n".join(failed_jobs)
        send_email(subject, body, **email_settings)


if __name__ == "__main__":
    # Autosys Server Settings
    autosys_server = "autosys_server_hostname"
    autosys_port = 9000

    # Email Settings
    email_settings = {
        "sender_email": "your_email@example.com",
        "sender_password": "your_email_password",
        "to_email": "recipient@example.com",
        "smtp_server": "smtp.example.com",
        "smtp_port": 587
    }

    # Pattern to match against job names
    pattern = "your_pattern"

    check_job_status(pattern, autosys_server, autosys_port, email_settings)
