import argparse
import datetime
import time
import logging
from collections import defaultdict
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import sybpydb

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_and_process_data(cursor):
    """
    Fetches and processes incident data to count incidents by assignment group and time period.
    
    Args:
        cursor (sybpydb.Cursor): The database cursor.
        
    Returns:
        dict: A dictionary with counts by (assignment_group, time_period) as keys.
    """
    counts = defaultdict(int)
    today = datetime.datetime.now()
    start_date_6_months = today - datetime.timedelta(days=6*30)
    start_date_1_week = today - datetime.timedelta(weeks=1)

    fetch_start_time = time.time()  # Start time for fetching data
    
    query = f"""
    SELECT assignment_group, opened_at
    FROM your_view
    WHERE opened_at >= '{start_date_6_months.strftime('%Y-%m-%d %H:%M:%S')}'
    """
    cursor.execute(query)

    for assignment_group, opened_at in cursor.fetchall():
        if isinstance(opened_at, datetime.datetime):
            # For monthly counts within the last 6 months
            if opened_at >= start_date_6_months:
                month_label = opened_at.strftime('%Y-%m')
                counts[(assignment_group, f"month_{month_label}")] += 1

            # For last 1 week count
            if opened_at >= start_date_1_week:
                counts[(assignment_group, "last_1_week")] += 1
        else:
            logger.warning(f"Skipping row with invalid opened_at: {opened_at}")
    
    fetch_time = time.time() - fetch_start_time  # Calculate fetch time in seconds
    logger.info(f"Data fetched and processed successfully. Time taken: {fetch_time:.2f} seconds.")
    return counts

# Set up argument parser
parser = argparse.ArgumentParser(description='Push incident counts to Push Gateway with specified job name and environment.')
parser.add_argument('--jobname', type=str, required=True, help='Job name for Push Gateway')
parser.add_argument('--pushgateway', type=str, required=True, help='Push Gateway URL')
parser.add_argument('--env', type=str, required=True, choices=['prod', 'qa', 'uat'], help='Environment (prod, qa, uat)')
args = parser.parse_args()

# Determine server and database based on environment
config = {
    'prod': {'dbserver': 'prods', 'database': 'sndata'},
    'qa': {'dbserver': 'qas', 'database': 'sndata'},
    'uat': {'dbserver': 'uas', 'database': 'sndata'}
}
dbserver = config[args.env]['dbserver']
database = config[args.env]['database']

# Connect to the Sybase Database
try:
    conn = sybpydb.connect(dsn=f"server name={dbserver}; database={database}; chainxacts=0")
    logger.info(f"Connected to SN server: {dbserver}")
except Exception as e:
    logger.error(f"Failed to connect to SN server: {e}")
    exit(1)

# Query to retrieve data and process counts
cursor = conn.cursor()
counts = fetch_and_process_data(cursor)

# Measure the time taken to push metrics
push_start_time = time.time()

# Push Data to Push Gateway
try:
    registry = CollectorRegistry()
    g = Gauge('incident_count', 'Incident count per assignment group and time period',
              ['assignment_group', 'time_period'], registry=registry)
    
    for (assignment_group, time_period), count in counts.items():
        g.labels(assignment_group=assignment_group, time_period=time_period).set(count)

    # Use the job name and push gateway link from command line arguments
    push_to_gateway(args.pushgateway, job=args.jobname, registry=registry)
    push_time = time.time() - push_start_time  # Calculate push time in seconds
    logger.info(f"Metrics pushed successfully to {args.pushgateway}. Time taken: {push_time:.2f} seconds.")
except Exception as e:
    logger.error(f"Failed to push metrics to Push Gateway: {e}")

# Close connection
conn.close()
logger.info("Database connection closed.")