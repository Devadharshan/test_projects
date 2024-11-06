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
    Fetches and processes incident data to count incidents by assignment group and month.
    
    Args:
        cursor (sybpydb.Cursor): The database cursor.
        
    Returns:
        dict: A dictionary with keys as (assignment_group, month) and values as counts.
    """
    monthly_counts = defaultdict(int)
    logger.info("Fetching data from the database...")
    for assignment_group, opened_at in cursor.fetchall():
        if isinstance(opened_at, datetime.datetime):  # Ensure opened_at is a datetime object
            month = opened_at.strftime('%Y-%m')  # Format date to 'YYYY-MM'
            monthly_counts[(assignment_group, month)] += 1
        else:
            logger.warning(f"Skipping row with invalid opened_at: {opened_at}")
    logger.info("Data fetched and processed successfully.")
    return monthly_counts

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

# Query to retrieve data
query = """
SELECT assignment_group, opened_at
FROM your_view
WHERE opened_at >= DATEADD(month, -6, GETDATE())
"""
cursor = conn.cursor()
try:
    cursor.execute(query)
except Exception as e:
    logger.error(f"Query execution failed: {e}")
    conn.close()
    exit(1)

# Process Data
monthly_counts = fetch_and_process_data(cursor)

# Measure the time taken to push metrics
start_time = time.time()

# Push Data to Push Gateway
try:
    registry = CollectorRegistry()
    g = Gauge('incident_count', 'Incident count per assignment group and month',
              ['assignment_group', 'month'], registry=registry)
    
    for (assignment_group, month), count in monthly_counts.items():
        g.labels(assignment_group=assignment_group, month=month).set(count)

    # Use the job name and push gateway link from command line arguments
    push_to_gateway(args.pushgateway, job=args.jobname, registry=registry)
    elapsed_time = time.time() - start_time
    logger.info(f"Metrics pushed successfully to {args.pushgateway}. Time taken: {elapsed_time:.2f} seconds.")
except Exception as e:
    logger.error(f"Failed to push metrics to Push Gateway: {e}")

# Close connection
conn.close()
logger.info("Database connection closed.")