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
    query = """
        SELECT inc_number, opened_at, actual_severity, assignment_group, ci_impacted
        FROM incident_view
        WHERE actual_severity != 'S5'
          AND opened_at >= ?
    """
    # Set the date to one year ago for last 1-year filtering
    date_one_year_ago = datetime.now() - timedelta(days=365)
    cursor.execute(query, (date_one_year_ago.strftime("%Y-%m-%d %H:%M:%S"),))
    incidents = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info("Data fetching completed.")
    return incidents

def process_incidents(incidents):
    """Process incidents and organize by severity, month, and year."""
    incident_data = {}
    for incident in incidents:
        inc_number, opened_at, severity, assignment_group, ci_impacted = incident
        # Extract month and year (e.g., "Jan 2024")
        month_year = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S").strftime("%b %Y")
        key = f"{severity}_{month_year}"

        # Initialize data structure if key does not exist
        if key not in incident_data:
            incident_data[key] = {
                'count': 0,
                'assignment_group': assignment_group,
                'inc_number': inc_number,
                'ci_impacted': ci_impacted
            }
        
        # Increment incident count
        incident_data[key]['count'] += 1
    
    return incident_data

def send_to_pushgateway(incident_data, pushgateway_url, job_name):
    """Send processed data to the Pushgateway."""
    registry = CollectorRegistry()
    gauge = Gauge(
        'incident_count',
        'Count of incidents by severity and month-year',
        labelnames=['severity_month_year', 'assignment_group', 'inc_number', 'ci_impacted'],
        registry=registry
    )

    for key, data in incident_data.items():
        gauge.labels(
            severity_month_year=key,
            assignment_group=data['assignment_group'],
            inc_number=data['inc_number'],
            ci_impacted=data['ci_impacted']
        ).set(data['count'])

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