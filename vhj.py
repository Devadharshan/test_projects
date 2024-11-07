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
    Fetches and processes incident data to count incidents by assignment group, time period,
    and additional fields (incident_number, cause_ci, actual_severity, impacted_ci).
    
    Args:
        cursor (sybpydb.Cursor): The database cursor.
        
    Returns:
        dict: Dictionary with counts for incidents grouped by (assignment_group, time_period, incident_number, cause_ci, actual_severity, impacted_ci).
    """
    incident_counts = defaultdict(int)
    today = datetime.datetime.now()
    start_date_1_year = today - datetime.timedelta(days=365)
    start_date_6_months = today - datetime.timedelta(days=6*30)
    start_date_1_week = today - datetime.timedelta(weeks=1)

    fetch_start_time = time.time()  # Start time for fetching data
    
    query = f"""
    SELECT assignment_group, incident_number, cause_ci, actual_severity, impacted_ci, opened_at
    FROM your_view
    WHERE opened_at >= '{start_date_1_year.strftime('%Y-%m-%d %H:%M:%S')}'
    """
    cursor.execute(query)

    for row in cursor.fetchall():
        if len(row) != 6:
            logger.warning(f"Skipping row with unexpected number of values: {row}")
            continue
        
        assignment_group, incident_number, cause_ci, actual_severity, impacted_ci, opened_at = row

        # Aggregate counts by the specific time periods
        if isinstance(opened_at, datetime.datetime):
            if opened_at >= start_date_1_year:
                incident_counts[(assignment_group, "last_1_year", cause_ci, actual_severity, impacted_ci)] += 1
            if opened_at >= start_date_6_months:
                incident_counts[(assignment_group, "last_6_months", cause_ci, actual_severity, impacted_ci)] += 1
            if opened_at >= start_date_1_week:
                incident_counts[(assignment_group, "last_1_week", cause_ci, actual_severity, impacted_ci)] += 1
        else:
            logger.warning(f"Skipping row with invalid opened_at: {opened_at}")
    
    fetch_time = time.time() - fetch_start_time  # Calculate fetch time in seconds
    logger.info(f"Data fetched and processed successfully. Time taken: {fetch_time:.2f} seconds.")
    return incident_counts

def push_metrics_to_gateway(incident_counts, pushgateway, jobname):
    """
    Push metrics to Push Gateway in batches to reduce load.
    
    Args:
        incident_counts (dict): Dictionary with processed incident data counts.
        pushgateway (str): Push Gateway URL.
        jobname (str): Job name for Push Gateway.
    """
    push_start_time = time.time()
    
    try:
        registry = CollectorRegistry()
        
        # Incident count gauge
        g_incident_count = Gauge(
            'incident_count',
            'Incident count per assignment group and time period',
            ['assignment_group', 'time_period', 'cause_ci', 'actual_severity', 'impacted_ci'],
            registry=registry
        )
        
        # Set metrics in batches
        for (assignment_group, time_period, cause_ci, actual_severity, impacted_ci), count in incident_counts.items():
            g_incident_count.labels(
                assignment_group=assignment_group, time_period=time_period, 
                cause_ci=cause_ci, actual_severity=actual_severity, impacted_ci=impacted_ci
            ).set(count)
        
        # Push metrics with a timeout and retry logic
        push_to_gateway(pushgateway, job=jobname, registry=registry, timeout=5)
        
        push_time = time.time() - push_start_time  # Calculate push time in seconds
        logger.info(f"Metrics pushed successfully to {pushgateway}. Time taken: {push_time:.2f} seconds.")
    except Exception as e:
        logger.error(f"Failed to push metrics to Push Gateway: {e}")

# Argument parser
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
incident_counts = fetch_and_process_data(cursor)

# Push metrics to Push Gateway
push_metrics_to_gateway(incident_counts, args.pushgateway, args.jobname)

# Close connection
conn.close()
logger.info("Database connection closed.")