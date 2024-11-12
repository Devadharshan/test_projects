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

def fetch_incidents(conn, start_date, end_date):
    query = """
    SELECT 
        assignment_group, 
        number, 
        cause_ci, 
        actual_severity, 
        impacted_ci, 
        opened_at 
    FROM incidents 
    WHERE opened_at >= ? AND opened_at < ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchall()

def format_date_to_month_year(date):
    return date.strftime('%b-%Y')  # Returns format Jan-2024

def send_all_metrics_to_pushgateway(incidents_by_period, gateway_url, job_name):
    registry = CollectorRegistry()
    incident_gauge = Gauge('incident_count', 'Number of incidents', 
                           labelnames=['assignment_group', 'number', 'cause_ci', 'actual_severity', 'opened_at', 'period'], 
                           registry=registry)
    
    for period, incidents in incidents_by_period.items():
        for incident in incidents:
            assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
            opened_month_year = format_date_to_month_year(opened_at)

            # Adding metrics for each incident
            incident_gauge.labels(
                assignment_group=assignment_group,
                number=number,
                cause_ci=cause_ci,
                actual_severity=actual_severity,
                opened_at=opened_month_year,
                period=period
            ).set(1)  # Increment by 1 for each incident

    # Push all metrics to Push Gateway in a single operation
    push_to_gateway(gateway_url, job=job_name, registry=registry)

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
    conn = connect_to_sybase(server, db)

    # Define exclusive date ranges for each period
    end_date = datetime.now()
    periods = {
        "Last_7_days": (end_date - timedelta(days=7), end_date),
        "Last_6_months": (end_date - timedelta(days=6*30), end_date - timedelta(days=7)),
        "Last_12_months": (end_date - timedelta(days=12*30), end_date - timedelta(days=6*30)),
        "Last_1_year": (end_date - timedelta(days=365), end_date - timedelta(days=12*30))
    }

    # Dictionary to hold incidents by period
    incidents_by_period = {}

    # Fetch incidents for each period
    for period, (start_date, end_date) in periods.items():
        try:
            incidents = fetch_incidents(conn, start_date, end_date)
            incidents_by_period[period] = incidents
            logger.info(f"Fetched {len(incidents)} incidents for period '{period}'")
        except Exception as e:
            logger.error(f"Error fetching incidents for period {period}: {e}")

    # Send all metrics at once
    send_all_metrics_to_pushgateway(incidents_by_period, args.gateway_url, args.job_name)

    conn.close()
    logger.info("All metrics have been processed and pushed successfully.")

if __name__ == "__main__":
    main()