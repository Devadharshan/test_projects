import argparse
import time
from datetime import datetime, timedelta
from sybpydb import connect
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_incident_data(db_server, db_name, env):
    """Fetch incident data from the ServiceNow Synapse DB."""
    logger.info("Connecting to ServiceNow database...")
    connection_string = f"dsn='server name={db_server};database={db_name};chainxacts=0'"
    conn = connect(dsn=connection_string)
    cursor = conn.cursor()
    
    # Define date ranges for the queries
    date_6_months_ago = datetime.now() - timedelta(days=180)
    date_yesterday = datetime.now() - timedelta(days=1)
    date_last_week = datetime.now() - timedelta(days=7)

    # Prepare query to fetch incidents for last 6 months, yesterday, and last weekdays (Mon-Fri)
    query = """
        SELECT inc_number, opened_at, actual_severity, assignment_group, ci_impacted
        FROM incident_view
        WHERE actual_severity != 'S5'
          AND (
              opened_at >= ? OR
              (opened_at BETWEEN ? AND ?) OR
              (opened_at BETWEEN ? AND ? AND DATEPART(dw, opened_at) BETWEEN 2 AND 6)
          )
    """
    
    cursor.execute(query, (
        date_6_months_ago.strftime("%Y-%m-%d %H:%M:%S"), # Last 6 months
        date_yesterday.strftime("%Y-%m-%d 00:00:00"), date_yesterday.strftime("%Y-%m-%d 23:59:59"), # Yesterday
        date_last_week.strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d") # Last Mon-Fri
    ))
    
    incidents = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info("Data fetching completed.")
    return incidents

def process_incidents(incidents):
    """Process incidents by time range: Last 6 Months, Yesterday, and Weekdays."""
    incident_data = {'last_6_months': {}, 'yesterday': {}, 'weekdays': {}}

    for incident in incidents:
        inc_number, opened_at, severity, assignment_group, ci_impacted = incident
        opened_datetime = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S")
        month_year = opened_datetime.strftime("%b %Y")

        if opened_datetime >= datetime.now() - timedelta(days=180):  # Last 6 months
            key = f"{severity}_{month_year}"
            if key not in incident_data['last_6_months']:
                incident_data['last_6_months'][key] = {
                    'count': 0,
                    'assignment_group': assignment_group,
                    'inc_number': inc_number,
                    'ci_impacted': ci_impacted
                }
            incident_data['last_6_months'][key]['count'] += 1

        if opened_datetime.date() == (datetime.now() - timedelta(days=1)).date():  # Yesterday
            key = f"{severity}_yesterday"
            if key not in incident_data['yesterday']:
                incident_data['yesterday'][key] = {
                    'count': 0,
                    'assignment_group': assignment_group,
                    'inc_number': inc_number,
                    'ci_impacted': ci_impacted
                }
            incident_data['yesterday'][key]['count'] += 1

        if opened_datetime >= datetime.now() - timedelta(days=7) and opened_datetime.weekday() < 5:  # Weekdays (Mon-Fri)
            key = f"{severity}_weekdays"
            if key not in incident_data['weekdays']:
                incident_data['weekdays'][key] = {
                    'count': 0,
                    'assignment_group': assignment_group,
                    'inc_number': inc_number,
                    'ci_impacted': ci_impacted
                }
            incident_data['weekdays'][key]['count'] += 1

    return incident_data

def send_to_pushgateway(incident_data, pushgateway_url, job_name):
    """Send processed data to the Pushgateway."""
    registry = CollectorRegistry()
    gauge = Gauge(
        'incident_count',
        'Count of incidents by severity and time range',
        labelnames=['severity_time_range', 'assignment_group', 'inc_number', 'ci_impacted'],
        registry=registry
    )

    for time_range, data in incident_data.items():
        for key, details in data.items():
            gauge.labels(
                severity_time_range=f"{key}_{time_range}",
                assignment_group=details['assignment_group'],
                inc_number=details['inc_number'],
                ci_impacted=details['ci_impacted']
            ).set(details['count'])

    # Push metrics to the Pushgateway
    logger.info("Pushing metrics to Pushgateway...")
    start_time = time.time()
    push_to_gateway(pushgateway_url, job=job_name, registry=registry)
    logger.info("Metrics pushed. Time taken: %.2f seconds", time.time() - start_time)

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process and send incident data to Pushgateway.")
    parser.add_argument("--env", required=True, help="Environment (prod, qa, uat)")
    parser.add_argument("--pushgateway_url", required=True, help="Pushgateway URL")
    parser.add_argument("--job_name", required=True, help="Job name for Pushgateway")
    args = parser.parse_args()

    # Determine server and database based on environment
    env = args.env.lower()
    db_server = 'prods' if env == 'prod' else 'qas' if env == 'qa' else 'uas'
    db_name = 'sndata'  # Same for both prod and qa as per user requirements

    # Fetch and process incidents
    start_time = time.time()
    incidents = fetch_incident_data(db_server, db_name, env)
    logger.info("Connected to SN server.")
    incident_data = process_incidents(incidents)
    logger.info("Data processing completed. Time taken: %.2f seconds", time.time() - start_time)

    # Send to Pushgateway
    send_to_pushgateway(incident_data, args.pushgateway_url, args.job_name)

if __name__ == "__main__":
    main()