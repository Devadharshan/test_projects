import time
from pymongo import MongoClient
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['admin']  # Use the admin database for serverStatus

# Function to fetch MongoDB serverStatus metrics
def fetch_mongo_metrics():
    return db.command("serverStatus")

# Function to push metrics to Pushgateway
def push_metrics_to_gateway(metrics):
    registry = CollectorRegistry()

    # Example: Define gauges for some key metrics
    memory_usage = Gauge('mongodb_memory_usage_mb', 'MongoDB memory usage in MB', registry=registry)
    connections_current = Gauge('mongodb_connections_current', 'Current number of connections', registry=registry)
    op_insert_total = Gauge('mongodb_op_insert_total', 'Total insert operations', registry=registry)
    op_query_total = Gauge('mongodb_op_query_total', 'Total query operations', registry=registry)

    # Set the metric values
    memory_usage.set(metrics['mem']['resident'])  # Resident memory in MB
    connections_current.set(metrics['connections']['current'])  # Current connections
    op_insert_total.set(metrics['opcounters']['insert'])  # Insert operations
    op_query_total.set(metrics['opcounters']['query'])  # Query operations

    # Push metrics to Pushgateway
    push_to_gateway('localhost:9091', job='mongodb_real_time_metrics', registry=registry)

# Main loop for fetching and pushing real-time metrics
if __name__ == "__main__":
    while True:
        metrics = fetch_mongo_metrics()  # Fetch real-time MongoDB metrics
        push_metrics_to_gateway(metrics)  # Push metrics to Pushgateway
        print("Metrics successfully pushed to Pushgateway.")

        # Sleep for a while (e.g., 30 seconds) before fetching metrics again
        time.sleep(30)
