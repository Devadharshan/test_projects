import time
import logging
from pysyb import connect
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import argparse
from datetime import datetime, timedelta

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

# Query data and calculate metrics
def query_data(conn, view_name):
    query = f"""
    SELECT 
        task_number, 
        request_number, 
        assignment_group, 
        closed_at, 
        opened_at, 
        assigned_to, 
        catalog_type, 
        state 
    FROM {view_name}
    """
    cursor = conn.cursor()
    start_time = time.time()
    cursor.execute(query)
    rows = cursor.fetchall()
    logger.info(f"Data queried in {time.time() - start_time:.2f} seconds")

    metrics = []
    for row in rows:
        task_number, request_number, assignment_group, closed_at, opened_at, assigned_to, catalog_type, state = row
        
        # Calculate time to close (in seconds)
        time_to_close = (closed_at - opened_at).total_seconds() if closed_at and opened_at else None

        # Determine the period
        current_time = datetime.now()
        if closed_at and closed_at.date() == current_time.date():
            period = "today"
        elif closed_at and closed_at.date() == (current_time - timedelta(days=1)).date():
            period = "yesterday"
        elif closed_at and closed_at >= current_time - timedelta(days=90):
            period = "last_3_months"
        elif closed_at and closed_at >= current_time - timedelta(days=30):
            period = "last_month"
        elif closed_at and closed_at >= datetime(current_time.year, 1, 1):
            period = "last_year"
        else:
            period = "older"

        # Get the month based on opened_at
        month = opened_at.strftime("%b-%Y") if opened_at else "unknown"

        metrics.append({
            "task_number": task_number,
            "request_number": request_number,
            "assignment_group": assignment_group,
            "catalog_type": catalog_type,
            "state": state,
            "assigned_to": assigned_to,
            "period": period,
            "month": month,
            "time_to_close": time_to_close,
        })
    return metrics

# Push metrics to Prometheus Push Gateway
def push_metrics(pushgateway_url, job_name, metrics):
    registry = CollectorRegistry()

    # Define Gauge
    gauge_time_to_close = Gauge(
        "ticket_time_to_close",
        "Time taken to close tickets",
        ["task_number", "request_number", "assignment_group", "catalog_type", "state", "assigned_to", "period", "month"],
        registry=registry
    )

    for metric in metrics:
        labels = {
            "task_number": metric["task_number"],
            "request_number": metric["request_number"],
            "assignment_group": metric["assignment_group"],
            "catalog_type": metric["catalog_type"],
            "state": metric["state"],
            "assigned_to": metric["assigned_to"],
            "period": metric["period"],
            "month": metric["month"],
        }

        if metric["time_to_close"] is not None:
            gauge_time_to_close.labels(**labels).set(metric["time_to_close"])

    # Push to Push Gateway
    start_time = time.time()
    push_to_gateway(pushgateway_url, job=job_name, registry=registry)
    logger.info(f"Metrics pushed to {pushgateway_url} in {time.time() - start_time:.2f} seconds")

# Main function
def main():
    parser = argparse.ArgumentParser(description="Fetch and push ServiceNow ticket metrics.")
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

    # Query data
    view_name = "task_view"  # Replace with your actual view name
    metrics = query_data(conn, view_name)

    # Push metrics
    push_metrics(args.pushgateway_url, args.job_name, metrics)

if __name__ == "__main__":
    main()