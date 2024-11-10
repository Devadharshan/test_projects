from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set up a Gauge metric
def create_incident_gauge():
    return Gauge(
        "incident_count",  # Metric name
        "Count of incidents",  # Description
        labelnames=["period", "assignment_group", "number", "cause_ci", "actual_severity", "impacted_ci", "month_year"]  # Labels
    )

# Function to push data to Push Gateway
def push_to_gateway(data, gateway_url, job_name):
    start_time = time.time()

    # Create a Gauge instance for tracking incident counts
    incident_gauge = create_incident_gauge()

    for period, incidents in data.items():
        for incident in incidents:
            assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
            month_year = opened_at.strftime("%m-%y")

            # Set the Gauge with labels
            incident_gauge.labels(
                period=period,
                assignment_group=assignment_group,
                number=number,
                cause_ci=cause_ci,
                actual_severity=actual_severity,
                impacted_ci=impacted_ci,
                month_year=month_year
            ).set(1)  # The value of the Gauge (1 for each incident)

    try:
        # Send metrics to the Push Gateway
        logging.info(f"Pushing data to Push Gateway at {gateway_url}")
        push_to_gateway(gateway_url, job=job_name, registry=incident_gauge)
    except Exception as e:
        logging.error(f"Failed to push data to Push Gateway: {e}")

    elapsed_time = time.time() - start_time
    logging.info(f"Metrics sent to Push Gateway in {elapsed_time:.2f} seconds.")

# Sample data (incidents)
data = {
    "Last_6_months": [
        ("Group_A", "INC001", "CI_001", "High", "CI_001", datetime(2023, 6, 15)),
        ("Group_B", "INC002", "CI_002", "Low", "CI_002", datetime(2023, 7, 10)),
    ],
    "Last_12_months": [
        ("Group_A", "INC003", "CI_003", "Medium", "CI_003", datetime(2023, 1, 5)),
    ],
}

# Example Push Gateway URL and job name
gateway_url = "http://your-pushgateway-url:9091"
job_name = "incident_stats"

# Push the data
push_to_gateway(data, gateway_url, job_name)