import argparse
import time
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import sybpydb
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_db(env):
    """Connect to the Sybase database based on environment."""
    server_db_mapping = {
        'prod': ('prods', 'sndata'),
        'qa': ('qas', 'sndata'),
        'uat': ('uas', 'sndata')
    }
    server, database = server_db_mapping.get(env)
    conn = sybpydb.connect(dsn=f"server name={server}; database={database}; chainxacts=0")
    logger.info("Connected to SN server.")
    return conn

def fetch_incident_data(conn):
    """Fetch incident data from the database."""
    query = """
    SELECT assignment_group, opened_at, inc_number, actual_severity, impacted_ci
    FROM incident_view
    WHERE actual_severity IS NOT NULL AND actual_severity != 'S5'
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return rows

def aggregate_data(rows):
    """Aggregate incident counts by assignment group and time range."""
    current_date = datetime.now()
    last_six_months = current_date - timedelta(days=180)
    last_week = current_date - timedelta(weeks=1)
    yesterday = current_date - timedelta(days=1)

    data_aggregated = {
        'last_6_months': {},
        'last_week': {},
        'yesterday': {}
    }

    for row in rows:
        assignment_group, opened_at, inc_number, actual_severity, impacted_ci = row
        month_year = opened_at.strftime("%b_%Y")  # Example: Jan_2024

        if opened_at >= last_six_months:
            range_key = 'last_6_months'
        elif opened_at >= last_week:
            range_key = 'last_week'
        elif opened_at >= yesterday:
            range_key = 'yesterday'
        else:
            continue  # Skip if outside of last 6 months, last week, or yesterday

        key = (assignment_group, actual_severity, month_year)
        if key not in data_aggregated[range_key]:
            data_aggregated[range_key][key] = 0
        data_aggregated[range_key][key] += 1

    return data_aggregated

def push_metrics(data_aggregated, pushgateway_url, job_name):
    """Push aggregated metrics to the Pushgateway."""
    registry = CollectorRegistry()
    gauge = Gauge('incident_count', 'Count of incidents by severity and time range',
                  ['severity_time_range', 'assignment_group', 'month_year'],
                  registry=registry)

    for range_key, incidents in data_aggregated.items():
        for (assignment_group, actual_severity, month_year), count in incidents.items():
            severity_time_range = f"{actual_severity}_{range_key}"
            gauge.labels(severity_time_range=severity_time_range,
                         assignment_group=assignment_group,
                         month_year=month_year).set(count)

    start_time = time.time()
    push_to_gateway(pushgateway_url, job=job_name, registry=registry)
    elapsed_time = time.time() - start_time
    logger.info("Metrics pushed to Pushgateway in %.2f seconds", elapsed_time)

def main():
    parser = argparse.ArgumentParser(description="Send incident data to Pushgateway")
    parser.add_argument('--env', choices=['prod', 'qa', 'uat'], required=True, help="Environment: prod, qa, or uat")
    parser.add_argument('--job_name', required=True, help="Job name for Pushgateway")
    parser.add_argument('--pushgateway_url', required=True, help="URL of the Pushgateway instance")
    args = parser.parse_args()

    conn = connect_to_db(args.env)
    try:
        rows = fetch_incident_data(conn)
        data_aggregated = aggregate_data(rows)
        push_metrics(data_aggregated, args.pushgateway_url, args.job_name)
    finally:
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    main()