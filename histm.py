import sybpydb
import argparse
import datetime
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection(env):
    """Establishes a Sybase database connection based on the environment."""
    db_server = {
        'prod': 'prods',
        'qa': 'qas',
        'uat': 'uas'
    }[env]
    conn = sybpydb.connect(dsn=f"server name={db_server}; database=sndata; chainxacts=0")
    logger.info(f"Connected to SN server for {env} environment.")
    return conn

def fetch_incident_data(conn, period):
    """Fetch incident data based on the given period."""
    today = datetime.datetime.today()
    date_filters = {
        'last_1_year': today - datetime.timedelta(days=365),
        'last_6_months': today - datetime.timedelta(days=182),
        'last_1_month': today - datetime.timedelta(days=30)
    }
    
    start_date = date_filters[period].strftime('%Y-%m-%d %H:%M:%S')
    query = f"""
    SELECT assignment_group, inc_number, actual_severity, impacted_ci, COUNT(*) as incident_count
    FROM incident_view
    WHERE opened_at >= '{start_date}' AND actual_severity != 'S5'
    GROUP BY assignment_group, inc_number, actual_severity, impacted_ci
    """
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    
    logger.info(f"Fetched {len(results)} records for {period}.")
    return results

def push_metrics(data, period, job_name, push_gateway):
    """Push metrics to Prometheus Push Gateway."""
    registry = CollectorRegistry()
    gauge = Gauge('incident_count', 'Number of incidents', 
                  ['assignment_group', 'inc_number', 'actual_severity', 'impacted_ci', 'time_period'],
                  registry=registry)

    for row in data:
        assignment_group, inc_number, actual_severity, impacted_ci, incident_count = row
        gauge.labels(assignment_group=assignment_group, inc_number=inc_number,
                     actual_severity=actual_severity, impacted_ci=impacted_ci,
                     time_period=period).set(incident_count)

    start_time = time.time()
    push_to_gateway(push_gateway, job=job_name, registry=registry)
    time_elapsed = time.time() - start_time
    logger.info(f"Metrics pushed to {push_gateway} for {period} in {time_elapsed:.2f} seconds.")

def main(env, job_name, push_gateway):
    conn = get_db_connection(env)

    for period in ['last_1_year', 'last_6_months', 'last_1_month']:
        data = fetch_incident_data(conn, period)
        push_metrics(data, period, job_name, push_gateway)

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', required=True, choices=['prod', 'qa', 'uat'], help="Environment (prod, qa, uat)")
    parser.add_argument('--job_name', required=True, help="Job name for Push Gateway")
    parser.add_argument('--push_gateway', required=True, help="Push Gateway URL")

    args = parser.parse_args()
    main(args.env, args.job_name, args.push_gateway)