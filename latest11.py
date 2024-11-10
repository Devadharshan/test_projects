import sys
import sybpydb
import time
import logging
from datetime import datetime
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
import yaml

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_sybase(server, db):
    conn = sybpydb.connect(server=server, database=db)
    return conn

def fetch_incidents(conn, period):
    query = """
    SELECT 
        assignment_group, 
        number, 
        cause_ci, 
        actual_severity, 
        impacted_ci, 
        opened_at 
    FROM incidents 
    WHERE opened_at >= ?
    """
    end_date = datetime.now()
    if period == "Last_7_days":
        start_date = end_date - timedelta(days=7)
    elif period == "Last_6_months":
        start_date = end_date - timedelta(days=6*30)  # Approx 6 months
    elif period == "Last_12_months":
        start_date = end_date - timedelta(days=12*30)  # Approx 12 months
    elif period == "Last_1_year":
        start_date = end_date - timedelta(days=365)
    
    cursor = conn.cursor()
    cursor.execute(query, (start_date,))
    incidents = cursor.fetchall()
    return incidents

def format_date_to_month_year(date):
    return date.strftime('%b-%Y')  # Returns the format Jan-2024

def send_metrics_to_pushgateway(incidents, period, gateway_url, job_name):
    registry = CollectorRegistry()
    incident_gauge = Gauge('incident_count', 'Number of incidents', 
                           labelnames=['assignment_group', 'number', 'cause_ci', 'actual_severity', 'opened_at', 'period'], 
                           registry=registry)
    
    for incident in incidents:
        assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
        opened_month_year = format_date_to_month_year(opened_at)

        # Sending metrics for each incident
        incident_gauge.labels(
            assignment_group=assignment_group,
            number=number,
            cause_ci=cause_ci,
            actual_severity=actual_severity,
            opened_at=opened_month_year,
            period=period
        ).set(1)  # Increment by 1 for each incident
    
    # Push metrics to Push Gateway
    try:
        push_to_gateway(gateway_url, job=job_name, registry=registry)
        logger.info(f"Successfully pushed metrics to Push Gateway {gateway_url}")
    except Exception as e:
        logger.error(f"Error pushing metrics: {e}")

def main():
    try:
        env = sys.argv[1]  # QA, PROD, etc.
        gateway_url = sys.argv[2]
        job_name = sys.argv[3]
        
        # Load configuration from YAML file
        with open("config.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)
        
        # Determine server and database based on environment
        server = config[env]['server']
        db = config[env]['db']
        
        # Connect to Sybase database
        conn = connect_to_sybase(server, db)
        
        # Fetch incidents for different periods
        periods = ["Last_7_days", "Last_6_months", "Last_12_months", "Last_1_year"]
        for period in periods:
            incidents = fetch_incidents(conn, period)
            send_metrics_to_pushgateway(incidents, period, gateway_url, job_name)
            
        conn.close()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()