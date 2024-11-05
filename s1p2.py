import argparse
import datetime
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pyodbc  # Assuming pyodbc for Synapse connectivity

# Set up argument parser
parser = argparse.ArgumentParser(description='Push incident counts to Push Gateway with specified job name.')
parser.add_argument('--jobname', type=str, required=True, help='Job name for Push Gateway')
args = parser.parse_args()

# Database connection
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=your_server;DATABASE=your_database;UID=your_username;PWD=your_password')
query = """
SELECT assignment_group, opened_at
FROM your_view
WHERE opened_at >= DATEADD(month, -6, GETDATE())
"""
df = pd.read_sql(query, conn)

# Data processing
df['opened_at'] = pd.to_datetime(df['opened_at'])
df['month'] = df['opened_at'].dt.to_period('M')
monthly_counts = df.groupby(['assignment_group', 'month']).size().reset_index(name='count')

# Push data to Push Gateway
registry = CollectorRegistry()
g = Gauge('incident_count', 'Incident count per assignment group and month', 
          ['assignment_group', 'month'], registry=registry)

for _, row in monthly_counts.iterrows():
    g.labels(assignment_group=row['assignment_group'], month=str(row['month'])).set(row['count'])

# Use the job name from command line argument
push_to_gateway('your_pushgateway_address', job=args.jobname, registry=registry)

# Close connection
conn.close()








--------\



# Process the Data to Aggregate Monthly Counts
monthly_counts = defaultdict(int)
for assignment_group, opened_at in cursor.fetchall():
    opened_at_date = datetime.datetime.strptime(opened_at, '%Y-%m-%d %H:%M:%S')
    month = opened_at_date.strftime('%Y-%m')  # Format date to 'YYYY-MM'
    monthly_counts[(assignment_group, month)] += 1

# Push Data to Push Gateway
registry = CollectorRegistry()
g = Gauge('incident_count', 'Incident count per assignment group and month',
          ['assignment_group', 'month'], registry=registry)

for (assignment_group, month), count in monthly_counts.items():
    g.labels(assignment_group=assignment_group, month=month).set(count)

# Use the job name from command line argument
push_to_gateway('your_pushgateway_address', job=args.jobname, registry=registry)






import argparse
import datetime
from collections import defaultdict
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pyodbc

def fetch_and_process_data(cursor):
    """
    Fetches and processes incident data to count incidents by assignment group and month.

    Args:
        cursor (pyodbc.Cursor): The database cursor.

    Returns:
        dict: A dictionary with keys as (assignment_group, month) and values as counts.
    """
    monthly_counts = defaultdict(int)
    for assignment_group, opened_at in cursor.fetchall():
        opened_at_date = datetime.datetime.strptime(opened_at, '%Y-%m-%d %H:%M:%S')
        month = opened_at_date.strftime('%Y-%m')  # Format date to 'YYYY-MM'
        monthly_counts[(assignment_group, month)] += 1

    return monthly_counts

# Set up argument parser
parser = argparse.ArgumentParser(description='Push incident counts to Push Gateway with specified job name.')
parser.add_argument('--jobname', type=str, required=True, help='Job name for Push Gateway')
args = parser.parse_args()

# Connect to the Synapse Database
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=your_server;DATABASE=your_database;UID=your_username;PWD=your_password')
query = """
SELECT assignment_group, opened_at
FROM your_view
WHERE opened_at >= DATEADD(month, -6, GETDATE())
"""
cursor = conn.cursor()
cursor.execute(query)

# Process Data
monthly_counts = fetch_and_process_data(cursor)

# Push Data to Push Gateway
registry = CollectorRegistry()
g = Gauge('incident_count', 'Incident count per assignment group and month',
          ['assignment_group', 'month'], registry=registry)

for (assignment_group, month), count in monthly_counts.items():
    g.labels(assignment_group=assignment_group, month=month).set(count)

# Use the job name from command line argument
push_to_gateway('your_pushgateway_address', job=args.jobname, registry=registry)

# Close connection
conn.close()


