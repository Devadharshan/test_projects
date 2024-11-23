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










import argparse
import datetime
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pysyb

# Parser for command-line arguments
parser = argparse.ArgumentParser(description="Push ServiceNow metrics to Prometheus Push Gateway.")
parser.add_argument("--env", required=True, help="Environment (qa, uat, prod).")
parser.add_argument("--job_name", required=True, help="Job name for Prometheus metrics.")
parser.add_argument("--push_gateway_url", required=True, help="URL of the Prometheus Push Gateway.")
args = parser.parse_args()

# Configuration for environments
env_config = {
    "qa": {"server": "qas", "db": "sndata"},
    "uat": {"server": "uas", "db": "sndb"},
    "prod": {"server": "prods", "db": "sndata"},
}

# Get server and database based on environment
env = args.env
if env not in env_config:
    raise ValueError(f"Invalid environment: {env}. Choose from qa, uat, or prod.")

server = env_config[env]["server"]
database = env_config[env]["db"]

# Logger setup
def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Convert seconds to a human-readable format
def format_time_to_close(seconds):
    """Convert seconds into a human-readable format."""
    if seconds is None:
        return "N/A"
    
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{int(days)} days")
    if hours > 0:
        time_parts.append(f"{int(hours)} hours")
    if minutes > 0:
        time_parts.append(f"{int(minutes)} minutes")
    if seconds > 0:
        time_parts.append(f"{int(seconds)} seconds")
    
    return ", ".join(time_parts)

# Connect to the database
conn = pysyb.connect(dsn=f"server name={server}; database={database};chainxacts=0")
cursor = conn.cursor()

# SQL Query to fetch data
query = """
SELECT
    task_number,
    request_number,
    assignment_group,
    catalog_type,
    opened_at,
    closed_at,
    state,
    assigned_to
FROM task_view
WHERE opened_at >= DATEADD(year, -1, GETDATE());
"""
log("Executing SQL query...")
start_query_time = time.time()
cursor.execute(query)
rows = cursor.fetchall()
end_query_time = time.time()
log(f"Query executed in {end_query_time - start_query_time:.2f} seconds.")

# Prepare metrics
registry = CollectorRegistry()

# Define gauges
gauge_ticket_count = Gauge(
    "ticket_count_by_period",
    "Count of tickets by period",
    ["assignment_group", "catalog_type", "period", "month"],
    registry=registry,
)

gauge_ticket_state_count = Gauge(
    "ticket_state_count",
    "Count of tickets by state",
    ["state", "assignment_group", "catalog_type", "period", "month"],
    registry=registry,
)

gauge_ticket_status_count = Gauge(
    "ticket_status_count",
    "Count of tickets opened or closed",
    ["status", "assignment_group", "catalog_type", "period", "month"],
    registry=registry,
)

# Process data
log("Processing data...")
metrics = []
for row in rows:
    task_number, request_number, assignment_group, catalog_type, opened_at, closed_at, state, assigned_to = row
    opened_at = datetime.datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S")
    closed_at = datetime.datetime.strptime(closed_at, "%Y-%m-%d %H:%M:%S") if closed_at else None

    # Calculate time to close
    time_to_close_seconds = (closed_at - opened_at).total_seconds() if closed_at else None
    time_to_close_label = format_time_to_close(time_to_close_seconds)

    # Determine period and month
    now = datetime.datetime.now()
    month_label = opened_at.strftime("%b-%Y")
    if now.date() == opened_at.date():
        period = "today"
    elif (now - opened_at).days == 1:
        period = "yesterday"
    elif opened_at >= now - datetime.timedelta(days=90):
        period = "last_3_months"
    elif opened_at >= now.replace(day=1) - datetime.timedelta(days=1):
        period = "last_month"
    elif opened_at >= now.replace(month=1, day=1):
        period = "last_year"
    else:
        period = "other"

    # Add metrics
    metrics.append({
        "task_number": task_number,
        "request_number": request_number,
        "assignment_group": assignment_group,
        "catalog_type": catalog_type,
        "state": state,
        "period": period,
        "month": month_label,
        "time_to_close_label": time_to_close_label,
    })

# Push metrics to Prometheus
log("Pushing metrics to Prometheus...")
start_push_time = time.time()
for metric in metrics:
    # Ticket count
    gauge_ticket_count.labels(
        assignment_group=metric["assignment_group"],
        catalog_type=metric["catalog_type"],
        period=metric["period"],
        month=metric["month"],
    ).inc()

    # Ticket state count
    gauge_ticket_state_count.labels(
        state=metric["state"],
        assignment_group=metric["assignment_group"],
        catalog_type=metric["catalog_type"],
        period=metric["period"],
        month=metric["month"],
    ).inc()

    # Ticket status count (opened/closed)
    status = "opened" if metric["state"] in ["New", "In Progress"] else "closed"
    gauge_ticket_status_count.labels(
        status=status,
        assignment_group=metric["assignment_group"],
        catalog_type=metric["catalog_type"],
        period=metric["period"],
        month=metric["month"],
    ).inc()

push_to_gateway(args.push_gateway_url, job=args.job_name, registry=registry)
end_push_time = time.time()
log(f"Metrics pushed to Prometheus in {end_push_time - start_push_time:.2f} seconds.")




------------

new changges


import argparse
import datetime
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pysyb

# Parser for command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Push ServiceNow metrics to Prometheus Push Gateway.")
    parser.add_argument("--env", required=True, help="Environment (qa, uat, prod).")
    parser.add_argument("--job_name", required=True, help="Job name for Prometheus metrics.")
    parser.add_argument("--push_gateway_url", required=True, help="URL of the Prometheus Push Gateway.")
    return parser.parse_args()

# Configuration for environments
env_config = {
    "qa": {"server": "qas", "db": "sndata"},
    "uat": {"server": "uas", "db": "sndb"},
    "prod": {"server": "prods", "db": "sndata"},
}

# Logger setup
def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}][{timestamp}] {message}")

# Convert seconds to a human-readable format
def format_time_to_close(seconds):
    """Convert seconds into a human-readable format."""
    if seconds is None:
        return "N/A"
    
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{int(days)} days")
    if hours > 0:
        time_parts.append(f"{int(hours)} hours")
    if minutes > 0:
        time_parts.append(f"{int(minutes)} minutes")
    if seconds > 0:
        time_parts.append(f"{int(seconds)} seconds")
    
    return ", ".join(time_parts)

# Connect to database and fetch data
def fetch_task_data(server, database):
    try:
        log(f"Connecting to the database on server '{server}' and database '{database}'...")
        conn = pysyb.connect(dsn=f"server name={server}; database={database};chainxacts=0")
        cursor = conn.cursor()
        log("Database connection established successfully.")

        # SQL Query to fetch data
        query = """
        SELECT
            task_number,
            request_number,
            assignment_group,
            catalog_type,
            opened_at,
            closed_at,
            state,
            assigned_to
        FROM task_view
        WHERE opened_at >= DATEADD(year, -1, GETDATE());
        """
        log("Executing SQL query...")
        start_query_time = time.time()
        cursor.execute(query)
        rows = cursor.fetchall()
        end_query_time = time.time()
        log(f"Query executed in {end_query_time - start_query_time:.2f} seconds.")
        log(f"Fetched {len(rows)} rows from the database.")
        return rows, conn, cursor
    except Exception as e:
        log(f"Error while executing query or connecting to the database: {e}", level="ERROR")
        raise

# Prepare Prometheus metrics
def prepare_metrics(rows):
    log("Preparing metrics...")
    registry = CollectorRegistry()

    # Define gauges
    gauge_ticket_count = Gauge(
        "ticket_count_by_period",
        "Count of tickets by period",
        ["assignment_group", "catalog_type", "period", "month"],
        registry=registry,
    )

    gauge_ticket_state_count = Gauge(
        "ticket_state_count",
        "Count of tickets by state",
        ["state", "assignment_group", "catalog_type", "period", "month"],
        registry=registry,
    )

    gauge_ticket_status_count = Gauge(
        "ticket_status_count",
        "Count of tickets opened or closed",
        ["status", "assignment_group", "catalog_type", "period", "month"],
        registry=registry,
    )

    metrics = []
    for row in rows:
        try:
            task_number, request_number, assignment_group, catalog_type, opened_at, closed_at, state, assigned_to = row
            opened_at = datetime.datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S")
            closed_at = datetime.datetime.strptime(closed_at, "%Y-%m-%d %H:%M:%S") if closed_at else None

            # Calculate time to close
            time_to_close_seconds = (closed_at - opened_at).total_seconds() if closed_at else None
            time_to_close_label = format_time_to_close(time_to_close_seconds)

            # Determine period and month
            now = datetime.datetime.now()
            month_label = opened_at.strftime("%b-%Y")
            if now.date() == opened_at.date():
                period = "today"
            elif (now - opened_at).days == 1:
                period = "yesterday"
            elif opened_at >= now - datetime.timedelta(days=90):
                period = "last_3_months"
            elif opened_at >= now.replace(day=1) - datetime.timedelta(days=1):
                period = "last_month"
            elif opened_at >= now.replace(month=1, day=1):
                period = "last_year"
            else:
                period = "other"

            # Add metrics
            metrics.append({
                "task_number": task_number,
                "request_number": request_number,
                "assignment_group": assignment_group,
                "catalog_type": catalog_type,
                "state": state,
                "period": period,
                "month": month_label,
                "time_to_close_label": time_to_close_label,
            })

        except Exception as e:
            log(f"Error processing row: {row} | Error: {e}", level="ERROR")

    return metrics, registry

# Push metrics to Prometheus Push Gateway
def push_metrics_to_gateway(metrics, registry, push_gateway_url, job_name):
    log("Pushing metrics to Prometheus...")
    try:
        start_push_time = time.time()
        for metric in metrics:
            # Ticket count
            gauge_ticket_count.labels(
                assignment_group=metric["assignment_group"],
                catalog_type=metric["catalog_type"],
                period=metric["period"],
                month=metric["month"],
            ).inc()

            # Ticket state count
            gauge_ticket_state_count.labels(
                state=metric["state"],
                assignment_group=metric["assignment_group"],
                catalog_type=metric["catalog_type"],
                period=metric["period"],
                month=metric["month"],
            ).inc()

            # Ticket status count (opened/closed)
            status = "opened" if metric["state"] in ["New", "In Progress"] else "closed"
            gauge_ticket_status_count.labels(
                status=status,
                assignment_group=metric["assignment_group"],
                catalog_type=metric["catalog_type"],
                period=metric["period"],
                month=metric["month"],
            ).inc()

        push_to_gateway(push_gateway_url, job=job_name, registry=registry)
        end_push_time = time.time()
        log(f"Metrics pushed to Prometheus in {end_push_time - start_push_time:.2f} seconds.")

    except Exception as e:
        log(f"Error pushing metrics to Prometheus: {e}", level="ERROR")
        raise

# Main function
def main():
    # Parse arguments
    args = parse_args()

    # Get server and database based on environment
    env = args.env
    if env not in env_config:
        raise ValueError(f"Invalid environment: {env}. Choose from qa, uat, or prod.")
    
    server = env_config[env]["server"]
    database = env_config[env]["db"]

    # Fetch task data from ServiceNow
    rows, conn, cursor = fetch_task_data(server, database)

    # Prepare metrics
    metrics, registry = prepare_metrics(rows)

    # Push metrics to Prometheus Push Gateway
    push_metrics_to_gateway(metrics, registry, args.push_gateway_url, args.job_name)

    # Close connection to the database
    if cursor:
        cursor.close()
        log("Database cursor closed.")
    if conn:
        conn.close()
        log("Database connection closed.")

if __name__ == "__main__":
    main()

