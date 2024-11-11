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

def fetch_incidents(conn, period):
    query = """
    SELECT 
        assignment_group, 
        number, 
        cause_ci, 
        actual_severity, 
        impacted_ci, 
        opened_at 
    FROM incidents 
    WHERE opened_at >= ?
    """
    end_date = datetime.now()
    if period == "Last_7_days":
        start_date = end_date - timedelta(days=7)
    elif period == "Last_6_months":
        start_date = end_date - timedelta(days=6*30)  # Approx 6 months
    elif period == "Last_12_months":
        start_date = end_date - timedelta(days=12*30)  # Approx 12 months
    elif period == "Last_1_year":
        start_date = end_date - timedelta(days=365)
    
    cursor = conn.cursor()
    cursor.execute(query, (start_date,))
    incidents = cursor.fetchall()
    return incidents

def format_date_to_month_year(date):
    return date.strftime('%b-%Y')  # Returns the format Jan-2024

def send_metrics_to_pushgateway(incidents, period, gateway_url, job_name):
    registry = CollectorRegistry()
    incident_gauge = Gauge('incident_count', 'Number of incidents', 
                           labelnames=['assignment_group', 'number', 'cause_ci', 'actual_severity', 'opened_at', 'period'], 
                           registry=registry)
    
    for incident in incidents:
        assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
        opened_month_year = format_date_to_month_year(opened_at)

        # Sending metrics for each incident
        incident_gauge.labels(
            assignment_group=assignment_group,
            number=number,
            cause_ci=cause_ci,
            actual_severity=actual_severity,
            opened_at=opened_month_year,
            period=period
        ).set(1)  # Increment by 1 for each incident
    
    # Push metrics to Push Gateway
    try:
        push_to_gateway(gateway_url, job=job_name, registry=registry)
        logger.info(f"Successfully pushed metrics to Push Gateway {gateway_url}")
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
    
    # Connect to Sybase database
    try:
        conn = connect_to_sybase(server, db)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Fetch incidents for different periods and push to gateway
    periods = ["Last_7_days", "Last_6_months", "Last_12_months", "Last_1_year"]
    for period in periods:
        try:
            incidents = fetch_incidents(conn, period)
            send_metrics_to_pushgateway(incidents, period, args.gateway_url, args.job_name)
        except Exception as e:
            logger.error(f"Error processing period {period}: {e}")

    conn.close()

if __name__ == "__main__":
    main()