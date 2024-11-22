import sys
import sybpydb
import time
import logging
from datetime import datetime, timedelta
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENV_CONFIG = {
    'qa': {'server': 'qaservername', 'database': 'sndata'},
    'prod': {'server': 'prodservername', 'database': 'sndata'},
    'uat': {'server': 'uatservername', 'database': 'sndata'}
}

def connect_to_sybase(server, db):
    return sybpydb.connect(server=server, database=db)

def fetch_incidents(conn, period):
    query = """
    SELECT assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at 
    FROM incidents WHERE opened_at >= ?
    """
    end_date = datetime.now()
    if period == "Last_7_days":
        start_date = end_date - timedelta(days=end_date.weekday())
    elif period == "Last_6_months":
        start_date = end_date - timedelta(days=6*30)
    elif period == "Last_12_months":
        start_date = end_date - timedelta(days=12*30)
    elif period == "Last_1_year":
        start_date = datetime(end_date.year, 1, 1)
    cursor = conn.cursor()
    cursor.execute(query, (start_date,))
    incidents = cursor.fetchall()
    logger.info(f"Fetched {len(incidents)} incidents for period '{period}'.")
    return incidents

def format_date_to_month_year(date):
    return date.strftime('%b-%Y')

def send_metrics_to_pushgateway(incidents, period, gateway_url, job_name):
    registry = CollectorRegistry()
    incident_gauge = Gauge('incident_count', 'Number of incidents', 
                           labelnames=['assignment_group', 'number', 'cause_ci', 
                                       'actual_severity', 'opened_at', 'period', 'month'], 
                           registry=registry)
    for incident in incidents:
        assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
        opened_month_year = format_date_to_month_year(opened_at)
        logger.info(f"Pushing: {assignment_group}, {number}, {cause_ci}, {actual_severity}, {opened_at}, {period}, {opened_month_year}")
        incident_gauge.labels(
            assignment_group=assignment_group,
            number=number,
            cause_ci=cause_ci,
            actual_severity=actual_severity,
            opened_at=str(opened_at),
            period=period,
            month=opened_month_year
        ).set(1)
    push_to_gateway(gateway_url, job=job_name, registry=registry)
    logger.info(f"Metrics for '{period}' pushed.")

def main():
    parser = argparse.ArgumentParser(description="Push incident metrics")
    parser.add_argument('--env', required=True, help="Environment (qa, prod, uat)")
    parser.add_argument('--gateway_url', required=True, help="Push Gateway URL")
    parser.add_argument('--job_name', required=True, help="Metrics job name")
    args = parser.parse_args()
    if args.env not in ENV_CONFIG:
        logger.error("Invalid environment. Use 'qa', 'prod', or 'uat'.")
        sys.exit(1)
    server, db = ENV_CONFIG[args.env]['server'], ENV_CONFIG[args.env]['database']
    conn = connect_to_sybase(server, db)
    periods = ["Last_7_days", "Last_6_months", "Last_12_months", "Last_1_year"]
    for period in periods:
        try:
            incidents = fetch_incidents(conn, period)
            send_metrics_to_pushgateway(incidents, period, args.gateway_url, args.job_name)
        except Exception as e:
            logger.error(f"Error for {period}: {e}")
    conn.close()

if __name__ == "__main__":
    main()