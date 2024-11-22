def send_metrics_to_pushgateway(incidents, period, gateway_url, job_name):
    from datetime import datetime  # Ensure datetime is imported
    from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
    
    def format_date_to_month_year(date):
        return date.strftime('%b-%Y')  # Example: Jan-2024

    # Create a new CollectorRegistry
    registry = CollectorRegistry()

    # Define the gauge metric with all the specified labels
    incident_gauge = Gauge(
        'incident_count', 
        'Number of incidents',
        labelnames=[
            'actual_severity', 
            'assignment_group', 
            'cause_ci', 
            'number', 
            'opened_at', 
            'period', 
            'month'
        ],
        registry=registry
    )
    
    # Loop through incidents and add to gauge
    for incident in incidents:
        assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
        opened_month_year = format_date_to_month_year(opened_at)

        # Update the gauge metric with labels
        incident_gauge.labels(
            actual_severity=actual_severity,
            assignment_group=assignment_group,
            cause_ci=cause_ci,
            number=number,
            opened_at=opened_at.strftime('%Y-%m-%d %H:%M:%S'),  # Full datetime
            period=period,
            month=opened_month_year
        ).set(1)  # Each incident increments by 1

    # Push metrics to Push Gateway
    try:
        push_to_gateway(gateway_url, job=job_name, registry=registry)
        logger.info(f"Metrics for period '{period}' successfully pushed to {gateway_url}.")
    except Exception as e:
        logger.error(f"Error pushing metrics: {e}")