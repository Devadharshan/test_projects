import datetime
import sybpydb
import time
import logging
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_db(server, database):
    """Connect to the Sybase database."""
    conn_string = f"dsn='server name={server}; database={database}; chainxacts=0'"
    try:
        conn = sybpydb.connect(dsn=conn_string)
        logger.info(f"Connected to {server} server.")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        return None

def fetch_incident_data(connection):
    """Fetch incident data from the ServiceNow database, excluding S5 incidents."""
    query = """
    SELECT assignment_group, cause_ci, actual_severity, impacted_ci, opened_at
    FROM incident_view
    WHERE opened_at >= DATEADD(year, -1, GETDATE())
      AND actual_severity != 'S5'
    """
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info("Fetched incident data from database (excluding S5 incidents).")
        return rows
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return []

def process_incident_data(rows):
    """Process incident data to prepare counts for each assignment group and time period."""
    incident_counts = {}
    now = datetime.datetime.now()
    
    for row in rows:
        assignment_group, cause_ci, actual_severity, impacted_ci, opened_at = row
        time_period = determine_time_period(opened_at, now)
        
        # Aggregate by assignment_group and time_period, storing all details in one label
        key = (assignment_group, time_period)
        
        if key not in incident_counts:
            incident_counts[key] = {
                'count': 0,
                'details': set()
            }
        
        # Update count and aggregate details
        incident_counts[key]['count'] += 1
        incident_counts[key]['details'].add(f"cause_ci={cause_ci}, actual_severity={actual_severity}, impacted_ci={impacted_ci}")

    logger.info("Processed incident data.")
    return incident_counts

def determine_time_period(opened_at, now):
    """Determine the time period label for each incident based on its opened_at date."""
    if opened_at >= now - datetime.timedelta(weeks=1):
        return 'Last 1 Week'
    elif opened_at >= now - datetime.timedelta(days=180):
        return 'Last 6 Months'
    else:
        return 'Last 1 Year'

def push_metrics_to_gateway(incident_counts, pushgateway, jobname):
    """Push metrics to Push Gateway."""
    push_start_time = time.time()
    registry = CollectorRegistry()
    
    g_incident_count = Gauge(
        'incident_count',
        'Incident count per assignment group and time period',
        ['assignment_group', 'time_period', 'details'],
        registry=registry
    )
    
    for (assignment_group, time_period), data in incident_counts.items():
        count = data['count']
        # Join details into a single string label
        details_label = '; '.join(data['details'])

        g_incident_count.labels(
            assignment_group=assignment_group,
            time_period=time_period,
            details=details_label
        ).set(count)
    
    try:
        push_to_gateway(pushgateway, job=jobname, registry=registry, timeout=10)
        push_time = time.time() - push_start_time
        logger.info(f"Metrics pushed successfully to {pushgateway}. Time taken: {push_time:.2f} seconds.")
    except Exception as e:
        logger.error(f"Failed to push metrics to Push Gateway: {e}")

def main():
    parser = argparse.ArgumentParser(description="Push incident data to Push Gateway")
    parser.add_argument('--pushgateway', required=True, help="Push Gateway URL")
    parser.add_argument('--server', required=True, help="Database server name (e.g., 'prods')")
    parser.add_argument('--env', required=True, choices=['prod', 'qa', 'uat'], help="Environment (prod, qa, uat)")
    args = parser.parse_args()

    # Set database name based on environment
    database = 'sndata' if args.env in ['prod', 'qa'] else 'otherdb'
    
    # Connect to the database and fetch incident data
    connection = connect_to_db(args.server, database)
    if connection:
        incident_rows = fetch_incident_data(connection)
        connection.close()
        
        # Process the data and push metrics
        incident_counts = process_incident_data(incident_rows)
        push_metrics_to_gateway(incident_counts, args.pushgateway, jobname="ABC_Incidents_6_months")

if __name__ == "__main__":
    main()