import datetime
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pyodbc  # Assuming pyodbc for Synapse connectivity

# Step 1: Connect to the Synapse Database
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=your_server;DATABASE=your_database;UID=your_username;PWD=your_password')
query = """
SELECT assignment_group, opened_at
FROM your_view
WHERE opened_at >= DATEADD(month, -6, GETDATE())
"""
df = pd.read_sql(query, conn)

# Step 2: Process Data to Get Monthly Counts
df['opened_at'] = pd.to_datetime(df['opened_at'])
df['month'] = df['opened_at'].dt.to_period('M')
monthly_counts = df.groupby(['assignment_group', 'month']).size().reset_index(name='count')

# Step 3: Push to Push Gateway
registry = CollectorRegistry()
g = Gauge('incident_count', 'Incident count per assignment group and month', 
          ['assignment_group', 'month'], registry=registry)

for _, row in monthly_counts.iterrows():
    g.labels(assignment_group=row['assignment_group'], month=str(row['month'])).set(row['count'])

push_to_gateway('your_pushgateway_address', job='incident_counts', registry=registry)

# Close connection
conn.close()
