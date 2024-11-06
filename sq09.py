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

def fetch_and_process_data(cursor, time_range):
    """
    Fetches and processes incident data to count incidents by assignment group and time range.
    
    Args:
        cursor (sybpydb.Cursor): The database cursor.
        time_range (str): The time range for data fetch (e.g., 'last_6_months', 'last_1_week').
        
    Returns:
        dict: A dictionary with keys as (assignment_group, time_range) and values as counts.
    """
    monthly_counts = defaultdict(int)
    logger.info(f"Fetching data for {time_range}...")

    # Calculate the start date based on time range
    if time_range == 'last_6_months':
        start_date = datetime.datetime.now() - datetime.timedelta(days=6*30)  # Approx 6 months
    elif time_range == 'last_1_week':
        start_date = datetime.datetime.now() - datetime.timedelta(weeks=1)  # Last 7 days
    else:
        logger.error(f"Unknown time range: {time_range}")
        return monthly_counts

    fetch_start_time = time.time()  # Start time for fetching data
    
    query = f"""
    SELECT assignment_group, opened_at
    FROM your_view
    WHERE opened_at >= '{start_date.strftime('%Y-%m-%d %H:%M:%S')}'
    """
    cursor.execute(query)

    for assignment_group, opened_at in cursor.fetchall():
        if isinstance(opened_at, datetime.datetime):  # Ensure opened_at is a datetime object
            time_period = time_range  # Use time range as the label (e.g., last 6 months, last 1 week)
            monthly_counts[(assignment_group, time_period)] += 1
        else:
            logger.warning(f"Skipping row with invalid opened_at: {opened_at}")
    
    fetch_time = time.time() - fetch_start_time  # Calculate fetch time in seconds
    logger.info(f"Data fetched and processed successfully. Time taken: {fetch_time:.2f} seconds.")
    return monthly_counts

# Set up argument parser
parser = argparse.ArgumentParser(description='Push incident counts to Push Gateway with specified job name and environment.')
parser.add_argument('--jobname', type=str, required=True, help='Job name for Push Gateway')
parser.add_argument('--pushgateway', type=str, required=True, help='Push Gateway URL')
parser.add_argument('--env', type=str, required=True, choices=['prod', 'qa', 'uat'], help='Environment (prod, qa, uat)')
parser.add_argument('--time_range', type=str, required=True, choices=['last_6_months', 'last_1_week'], help='Time range for data (last_6_months, last_1_week)')
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

# Query to retrieve data (adjusted for dynamic time range)
cursor = conn.cursor()

# Process Data for the given time range
monthly_counts = fetch_and_process_data(cursor, args.time_range)

# Measure the time taken to push metrics
push_start_time = time.time()

# Push Data to Push Gateway
try:
    registry = CollectorRegistry()
    g = Gauge('incident_count', 'Incident count per assignment group and time range',
              ['assignment_group', 'time_range'], registry=registry)
    
    for (assignment_group, time_period), count in monthly_counts.items():
        g.labels(assignment_group=assignment_group, time_range=time_period).set(count)

    # Use the job name and push gateway link from command line arguments
    push_to_gateway(args.pushgateway, job=args.jobname, registry=registry)
    push_time = time.time() - push_start_time  # Calculate push time in seconds
    logger.info(f"Metrics pushed successfully to {args.pushgateway}. Time taken: {push_time:.2f} seconds.")
except Exception as e:
    logger.error(f"Failed to push metrics to Push Gateway: {e}")

# Close connection
conn.close()
logger.info("Database connection closed.")