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
    'qa': {'server': 'qaservername', 'database': 'sndata'},
    'prod': {'server': 'prodservername', 'database': 'sndata'},
    'uat': {'server': 'uatservername', 'database': 'sndata'}
}

def connect_to_sybase(server, db):
    return sybpydb.connect(server=server, database=db)

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
        start_date = end_date - timedelta(days=6 * 30)  # Approx 6 months
    elif period == "Last_1_year":
        start_date = end_date.replace(month=1, day=1)  # From Jan 1st
    else:
        raise ValueError("Invalid period")

    cursor = conn.cursor()
    start_time = time.time()
    cursor.execute(query, (start_date,))
    incidents = cursor.fetchall()
    query_duration = time.time() - start_time
    logger.info(f"Query executed for period '{period}' in {query_duration:.2f} seconds.")
    return incidents

def get_month_from_date(date):
    """Formats month as 'Jan-YYYY'."""
    return date.strftime('%b-%Y')

def send_metrics_to_pushgateway(incidents, period, gateway_url, job_name):
    registry = CollectorRegistry()
    incident_gauge = Gauge('incident_count', 'Number of incidents', 
                           labelnames=['assignment_group', 'month', 'period'], 
                           registry=registry)
    
    for incident in incidents:
        assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
        month_label = get_month_from_date(opened_at)

        # Increment the gauge for each incident
        incident_gauge.labels(
            assignment_group=assignment_group,
            month=month_label,
            period=period
        ).inc()  # Increment by 1 for each incident

    # Push metrics to Push Gateway
    start_time = time.time()
    try:
        push_to_gateway(gateway_url, job=job_name, registry=registry)
        push_duration = time.time() - start_time
        logger.info(f"Metrics for period '{period}' pushed to {gateway_url} in {push_duration:.2f} seconds.")
    except Exception as e:
        logger.error(f"Error pushing metrics: {e}")

def main():
    parser = argparse.ArgumentParser(description="Fetch and push incident metrics")
    parser.add_argument('--env', type=str, required=True, help="Environment (qa, prod, uat)")
    parser.add_argument('--gateway_url', type=str, required=True, help="Push Gateway URL")
    parser.add_argument('--job_name', type=str, required=True, help="Job name for metrics")
    args = parser.parse_args()

    if args.env not in ENV_CONFIG:
        logger.error("Invalid environment specified. Use 'qa', 'prod', or 'uat'.")
        sys.exit(1)
    
    server = ENV_CONFIG[args.env]['server']
    db = ENV_CONFIG[args.env]['database']
    logger.info(f"Connecting to server: {server}, database: {db} for environment '{args.env}'")

    try:
        conn = connect_to_sybase(server, db)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    periods = ["Last_7_days", "Last_6_months", "Last_1_year"]
    for period in periods:
        try:
            incidents = fetch_incidents(conn, period)
            send_metrics_to_pushgateway(incidents, period, args.gateway_url, args.job_name)
        except Exception as e:
            logger.error(f"Error processing period {period}: {e}")

    conn.close()
    logger.info("All metrics have been processed and pushed successfully.")

if __name__ == "__main__":
    main()
