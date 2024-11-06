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
parser = argparse.ArgumentParser(description='Push incident counts to Push Gateway with specified job name and environment.')
parser.add_argument('--jobname', type=str, required=True, help='Job name for Push Gateway')
parser.add_argument('--pushgateway', type=str, required=True, help='Push Gateway URL')
parser.add_argument('--env', type=str, required=True, choices=['prod', 'qa', 'uat'], help='Environment (prod, qa, uat)')
args = parser.parse_args()

# Determine database server based on environment
server_mapping = {
    'prod': 'prods',
    'qa': 'qas',
    'uat': 'uas'
}
server = server_mapping[args.env]

# Connect to the Synapse Database
conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE=your_database;UID=your_username;PWD=your_password')
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

# Use the job name and push gateway link from command line arguments
push_to_gateway(args.pushgateway, job=args.jobname, registry=registry)

# Close connection
conn.close()




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
parser = argparse.ArgumentParser(description='Push incident counts to Push Gateway with specified job name and environment.')
parser.add_argument('--jobname', type=str, required=True, help='Job name for Push Gateway')
parser.add_argument('--pushgateway', type=str, required=True, help='Push Gateway URL')
parser.add_argument('--env', type=str, required=True, choices=['prod', 'qa', 'uat'], help='Environment (prod, qa, uat)')
args = parser.parse_args()

# Determine server and database based on environment
config = {
    'prod': {'server': 'prods', 'database': 'sndata'},
    'qa': {'server': 'qas', 'database': 'sndata'},
    'uat': {'server': 'uas', 'database': 'sndata'}  # Assuming 'sndata' is also the db name in uat
}
server = config[args.env]['server']
database = config[args.env]['database']

# Connect to the Synapse Database
conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID=your_username;PWD=your_password')
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

# Use the job name and push gateway link from command line arguments
push_to_gateway(args.pushgateway, job=args.jobname, registry=registry)

# Close connection
conn.close()







import argparse
import datetime
import time
from collections import defaultdict
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import sybpydb

def fetch_and_process_data(cursor):
    """
    Fetches and processes incident data to count incidents by assignment group and month.
    
    Args:
        cursor (sybpydb.Cursor): The database cursor.
        
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
conn = sybpydb.connect(dsn=f"server name={dbserver}; database={database}; chainxacts=0")
print(f"Connected to SN server: {dbserver}")

# Query to retrieve data
query = """
SELECT assignment_group, opened_at
FROM your_view
WHERE opened_at >= DATEADD(month, -6, GETDATE())
"""
cursor = conn.cursor()
cursor.execute(query)

# Process Data
monthly_counts = fetch_and_process_data(cursor)

# Measure the time taken to push metrics
start_time = time.time()

# Push Data to Push Gateway
registry = CollectorRegistry()
g = Gauge('incident_count', 'Incident count per assignment group and month',
          ['assignment_group', 'month'], registry=registry)

for (assignment_group, month), count in monthly_counts.items():
    g.labels(assignment_group=assignment_group, month=month).set(count)

# Use the job name and push gateway link from command line arguments
push_to_gateway(args.pushgateway, job=args.jobname, registry=registry)

# Calculate the elapsed time
elapsed_time = time.time() - start_time
print(f"Metrics pushed successfully to {args.pushgateway}. Time taken: {elapsed_time:.2f} seconds.")

# Close connection
conn.close()





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
        month = opened_at.strftime('%Y-%m')  # Directly format the datetime object to 'YYYY-MM'
        monthly_counts[(assignment_group, month)] += 1
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