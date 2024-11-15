import sys
import sybpydb
import time
import logging
from datetime import datetime, timedelta
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
import argparse

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
ENV_CONFIG = {
    'qa': {
        'server': 'qaservername',
        'database': 'sndata'
    },
    'prod': {
        'server': 'prodservername',
        'database': 'sndata'
    },
    'uat': {
        'server': 'uatservername',
        'database': 'sndata'
    }
}

def connect_to_sybase(server, db):
    conn = sybpydb.connect(server=server, database=db)
    return conn

def calculate_period_dates():
    today = datetime.now()
    last_sunday = today - timedelta(days=today.weekday() + 1)  # Last Sunday
    
    # Period calculations
    one_year_ago = datetime(today.year, 1, 1)  # From Jan 1st of this year
    six_months_ago = today - timedelta(days=6*30)
    three_months_ago = today - timedelta(days=3*30)
    return {
        "Last_1_year": (one_year_ago, today),
        "Last_6_months": (six_months_ago, today),
        "Last_3_months": (three_months_ago, today),
        "Last_7_days": (last_sunday, today)
    }

def fetch_incidents_for_period(conn, start_date, end_date):
    query = """
    SELECT 
        assignment_group, 
        number, 
        cause_ci, 
        actual_severity, 
        impacted_ci, 
        opened_at 
    FROM incidents 
    WHERE opened_at >= ? AND opened_at <= ?
    """
    
    cursor = conn.cursor()
    start_time = time.time()
    cursor.execute(query, (start_date, end_date))
    incidents = cursor.fetchall()
    query_duration = time.time() - start_time
    logger.info(f"Query executed in {query_duration:.2f} seconds for period from {start_date} to {end_date}.")
    return incidents

def format_date_to_month_day(date):
    return date.strftime('%b-%d')  # Returns the format Jan-15

def send_metrics_to_pushgateway(incidents, period, gateway_url, job_name):
    registry = CollectorRegistry()
    incident_gauge = Gauge('incident_count', 'Number of incidents', 
                           labelnames=['assignment_group', 'number', 'cause_ci', 'actual_severity', 'opened_at', 'period'], 
                           registry=registry)
    
    for incident in incidents:
        assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
        opened_day = format_date_to_month_day(opened_at)

        # Sending metrics for each incident
        incident_gauge.labels(
            assignment_group=assignment_group,
            number=number,
            cause_ci=cause_ci,
            actual_severity=actual_severity,
            opened_at=opened_day,
            period=period
        ).set(1)  # Increment by 1 for each incident
    
    # Push metrics to Push Gateway
    start_time = time.time()
    try:
        push_to_gateway(gateway_url, job=job_name, registry=registry)
        push_duration = time.time() - start_time
        logger.info(f"Metrics for period '{period}' pushed to {gateway_url} in {push_duration:.2f} seconds.")
    except Exception as e:
        logger.error(f"Error pushing metrics: {e}")

def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Fetch and push incident metrics")
    parser.add_argument('--env', type=str, required=True, help="Environment (qa, prod, uat)")
    parser.add_argument('--gateway_url', type=str, required=True, help="Push Gateway URL")
    parser.add_argument('--job_name', type=str, required=True, help="Job name for metrics")
    args = parser.parse_args()

    # Validate and retrieve environment configuration
    if args.env not in ENV_CONFIG:
        logger.error("Invalid environment specified. Use 'qa', 'prod', or 'uat'.")
        sys.exit(1)
    
    server = ENV_CONFIG[args.env]['server']
    db = ENV_CONFIG[args.env]['database']
    
    # Log the connection details
    logger.info(f"Connecting to server: {server}, database: {db} for environment '{args.env}'")
    
    # Connect to Sybase database
    try:
        conn = connect_to_sybase(server, db)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Fetch incidents for different periods and push to gateway
    periods = calculate_period_dates()
    for period_name, (start_date, end_date) in periods.items():
        try:
            incidents = fetch_incidents_for_period(conn, start_date, end_date)
            send_metrics_to_pushgateway(incidents, period_name, args.gateway_url, args.job_name)
        except Exception as e:
            logger.error(f"Error processing period {period_name}: {e}")

    conn.close()
    logger.info("All metrics have been processed and pushed successfully.")

if __name__ == "__main__":
    main()