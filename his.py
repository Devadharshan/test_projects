import datetime
import pymysql  # Replace with pyodbc if necessary
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Push Gateway URL
PUSHGATEWAY_URL = "http://<push_gateway_url>:9091"
# Database connection parameters
DB_HOST = "your_servicenow_db_host"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_NAME = "your_db_name"

# Dates for last month and one-year breakdown
today = datetime.date.today()
start_of_last_month = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
start_of_year = today.replace(day=1).replace(year=today.year - 1)

def query_database(query, params=None):
    """Connects to the database and executes a query."""
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
        return results
    finally:
        connection.close()

def get_incident_counts():
    """Fetches change-related incidents and calculates counts for last month and each month in the past year."""
    # Query to retrieve incidents for the last month and past year, with relevant fields
    query = """
        SELECT assignment_group, DATE_FORMAT(sys_created_on, '%Y-%m') as month, COUNT(*) as count
        FROM your_view_name
        WHERE sys_created_on >= %s
        AND incident_type = 'change'
        GROUP BY assignment_group, month
    """
    
    # Retrieve data from start of last month for last-month data and year data
    results = query_database(query, params=(start_of_year,))
    
    # Separate data into last month and past year breakdown
    last_month_counts = {}
    yearly_counts = {}
    
    for row in results:
        assignment_group, month, count = row
        if month == start_of_last_month.strftime('%Y-%m'):
            last_month_counts[assignment_group] = count
        yearly_counts.setdefault(assignment_group, {})[month] = count
    
    return last_month_counts, yearly_counts

def push_metrics_to_gateway(last_month_counts, yearly_counts):
    """Pushes incident counts to the Push Gateway."""
    registry = CollectorRegistry()
    
    # Gauge for last month's count
    last_month_gauge = Gauge('incident_count_last_month', 'Incident count for the last month',
                             ['assignment_group'], registry=registry)
    for group, count in last_month_counts.items():
        last_month_gauge.labels(assignment_group=group).set(count)
    
    # Gauge for monthly counts over the past year
    yearly_gauge = Gauge('incident_count_monthly', 'Monthly incident count for the past year',
                         ['assignment_group', 'month'], registry=registry)
    for group, months in yearly_counts.items():
        for month, count in months.items():
            yearly_gauge.labels(assignment_group=group, month=month).set(count)
    
    # Push to Push Gateway
    push_to_gateway(PUSHGATEWAY_URL, job='service_now_incident_counts', registry=registry)

def main():
    # Fetch incident counts
    last_month_counts, yearly_counts = get_incident_counts()
    
    # Push data to Push Gateway
    push_metrics_to_gateway(last_month_counts, yearly_counts)
    print("Metrics pushed to Push Gateway.")

if __name__ == "__main__":
    main()