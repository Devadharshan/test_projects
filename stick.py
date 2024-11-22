import time
import logging
from pysyb import connect
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import argparse
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment configuration
def get_config(env):
    env_config = {
        "qa": {"server": "qa_server", "database": "sndata"},
        "uat": {"server": "uat_server", "database": "sndata"},
        "prod": {"server": "prod_server", "database": "sndata"},
    }
    return env_config.get(env)

# Connect to the database
def connect_to_db(server, database):
    try:
        conn = connect(dsn=f"server name={server};database={database};chainxacts=0")
        logger.info(f"Connected to {server}/{database}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to {server}/{database}: {e}")
        raise

# Query tickets based on periods
def query_ticket_counts(conn, view_name):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    last_month = today.replace(day=1) - datetime.timedelta(days=1)
    last_3_months = today - datetime.timedelta(days=90)
    year_start = today.replace(month=1, day=1)

    queries = {
        "today": f"SELECT COUNT(*) AS count FROM {view_name} WHERE opened_at >= '{today}'",
        "yesterday": f"SELECT COUNT(*) AS count FROM {view_name} WHERE opened_at BETWEEN '{yesterday}' AND '{today}'",
        "last_month": f"SELECT COUNT(*) AS count FROM {view_name} WHERE opened_at >= '{last_month.replace(day=1)}'",
        "last_3_months": f"SELECT COUNT(*) AS count FROM {view_name} WHERE opened_at >= '{last_3_months}'",
        "last_year": f"SELECT COUNT(*) AS count FROM {view_name} WHERE opened_at >= '{year_start}'",
    }

    results = {}
    for period, query in queries.items():
        start_time = time.time()
        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        results[period] = count
        logger.info(f"Query for {period} executed in {time.time() - start_time:.2f} seconds")
    return results

# Push metrics to Prometheus Push Gateway
def push_metrics(pushgateway_url, job_name, ticket_counts):
    start_time = time.time()
    registry = CollectorRegistry()
    gauge = Gauge("task_ticket_count", "Ticket counts for different periods", ["period"], registry=registry)

    for period, count in ticket_counts.items():
        gauge.labels(period=period).set(count)

    push_to_gateway(pushgateway_url, job=job_name, registry=registry)
    logger.info(f"Metrics pushed to {pushgateway_url} in {time.time() - start_time:.2f} seconds")

# Main function
def main():
    parser = argparse.ArgumentParser(description="Fetch and push ServiceNow ticket counts.")
    parser.add_argument("--env", required=True, help="Environment: qa, uat, or prod")
    parser.add_argument("--job-name", required=True, help="Job name for Prometheus Push Gateway")
    parser.add_argument("--pushgateway-url", required=True, help="Push Gateway URL")
    args = parser.parse_args()

    # Get config and connect to database
    config = get_config(args.env)
    if not config:
        logger.error("Invalid environment specified.")
        return

    server, database = config["server"], config["database"]
    conn = connect_to_db(server, database)

    # Query ticket counts
    view_name = "task_view"  # Replace with your actual view name
    ticket_counts = query_ticket_counts(conn, view_name)

    # Push metrics
    push_metrics(args.pushgateway_url, args.job_name, ticket_counts)

if __name__ == "__main__":
    main()