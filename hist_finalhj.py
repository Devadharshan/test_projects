import argparse
import time
from prometheus_client import Gauge, push_to_gateway, CollectorRegistry
import sybpydb

# Define environment details
ENV_DETAILS = {
    "qa": {"server": "qa_server_name", "db": "sn"},
    "prod": {"server": "prod_server_name", "db": "sn"},
    "uat": {"server": "uat_server_name", "db": "sn"},
}

# Define periods for querying
PERIODS = {
    "last_1_year": "WHERE opened_at >= DATEADD(year, -1, GETDATE())",
    "last_12_months": "WHERE opened_at >= DATEADD(month, -12, GETDATE())",
    "last_6_months": "WHERE opened_at >= DATEADD(month, -6, GETDATE())",
    "last_7_days": "WHERE opened_at >= DATEADD(day, -7, GETDATE())"
}

# Set up argparse for environment, job name, and Push Gateway URL
parser = argparse.ArgumentParser(description="Push incident metrics to Prometheus Push Gateway.")
parser.add_argument("--env", choices=ENV_DETAILS.keys(), required=True, help="Environment (e.g., qa, prod, uat)")
parser.add_argument("--job", required=True, help="Job name for Push Gateway")
parser.add_argument("--pushgateway", required=True, help="Push Gateway URL (e.g., http://localhost:9091)")
args = parser.parse_args()

# Get environment details
env_config = ENV_DETAILS[args.env]
server = env_config["server"]
db = env_config["db"]
pushgateway_url = args.pushgateway

# Initialize the Sybase database connection
conn = sybpydb.connect(dsn=f"server={server};db={db};chainxacts=0")

# Set up logging
def log_time(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Loop through each period and push metrics
for period, condition in PERIODS.items():
    log_time(f"Querying data for period: {period}")

    # Query incidents from Sybase
    start_time = time.time()
    query = f"""
        SELECT assignment_group, COUNT(*) AS count
        FROM incidents
        {condition} AND actual_severity != 'S5'
        GROUP BY assignment_group
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    query_duration = time.time() - start_time
    log_time(f"Query execution time for {period}: {query_duration:.2f} seconds")

    # Register a new metric for this period
    registry = CollectorRegistry()
    gauge = Gauge("incident_count", "Count of incidents by period", ["assignment_group", "period"], registry=registry)

    # Set gauge values based on the query result
    for row in rows:
        assignment_group = row[0]
        count = row[1]
        gauge.labels(assignment_group=assignment_group, period=period).set(count)

    # Push to Push Gateway
    push_start = time.time()
    push_to_gateway(f"{pushgateway_url}", job=args.job, registry=registry)
    push_duration = time.time() - push_start
    log_time(f"Successfully pushed metrics for {period} to {pushgateway_url} in {push_duration:.2f} seconds")

log_time("Completed all metrics pushes.")
conn.close()