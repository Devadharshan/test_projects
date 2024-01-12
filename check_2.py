import csv
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(body, file_path):
    sender_email = "your_email@example.com"  # Replace with your email
    receiver_email = "receiver_email@example.com"  # Replace with recipient email
    password = "your_password"  # Replace with your email password

    subject = "URL Status Report"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Email body with HTML table
    html_content = f"""\
    <html>
      <head>
        <style>
          table {{
            border-collapse: collapse;
            width: 100%;
          }}
          th, td {{
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
          }}
          th {{
            background-color: #f2f2f2;
          }}
          .up {{
            background-color: #99ff99;
          }}
          .down {{
            background-color: #ff9999;
          }}
        </style>
      </head>
      <body>
        <p>URL Status Report:</p>
        {body}
      </body>
    </html>
    """

    part = MIMEText(html_content, "html")
    message.attach(part)

    # Attaching the CSV file
    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {file_path}",
        )
        message.attach(part)

    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:  # Replace with your SMTP server details
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def check_urls_and_send_email(csv_file):
    results = []  # To store URL status
    timeout_seconds = 5  # Adjust the timeout value as needed

    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header if exists
        for row in csv_reader:
            url = row[0]  # Assuming URL is in the first column
            try:
                response = requests.get(url, timeout=timeout_seconds)
                if response.status_code == 200:
                    result = f"<a href='{url}' class='up'>{url}</a> is up"
                else:
                    result = f"<a href='{url}' class='down'>{url}</a> is down with status code: {response.status_code}"
            except requests.RequestException as e:
                result = f"{url} encountered an error: {e}"
            except requests.Timeout:
                result = f"{url} timed out after {timeout_seconds} seconds"
            finally:
                results.append([url, result])  # Storing URL and its status

    # Writing results to a CSV file
    output_file = 'url_status.csv'
    with open(output_file, 'w', newline='') as result_file:
        csv_writer = csv.writer(result_file)
        csv_writer.writerow(['URL', 'Status'])
        csv_writer.writerows(results)

    # Constructing HTML table from CSV data with highlighting and clickable URLs
    table_content = "<table><tr><th>URL</th><th>Status</th></tr>"
    for url, status in results:
        table_content += f"<tr>{status}</tr>"
    table_content += "</table>"

    # Send email with the table embedded in the email body and CSV file attached
    send_email(table_content, output_file)

# Replace 'urls.csv' with the path to your CSV file containing URLs
check_urls_and_send_email('urls.csv')
