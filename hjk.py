import sybpydb
import requests
import argparse
import logging
from datetime import datetime
from time import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_incident_data(server, database):
    conn = sybpydb.connect(dsn=f"server name={server}; database={database}; chainxacts=0")
    cursor = conn.cursor()
    
    # Define your queries for each timeframe
    queries = {
        "last_7_days": "SELECT assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at "
                       "FROM your_view_name WHERE actual_severity != 'S5' AND opened_at >= DATEADD(day, -7, GETDATE())",
        "last_6_months": "SELECT assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at "
                         "FROM your_view_name WHERE actual_severity != 'S5' AND opened_at >= DATEADD(month, -6, GETDATE())",
        "last_12_months": "SELECT assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at "
                          "FROM your_view_name WHERE actual_severity != 'S5' AND opened_at >= DATEADD(month, -12, GETDATE())",
        "last_year": "SELECT assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at "
                     "FROM your_view_name WHERE actual_severity != 'S5' AND opened_at >= DATEADD(year, -1, GETDATE())"
    }

    results = {}
    for period, query in queries.items():
        start_time = time()
        cursor.execute(query)
        results[period] = cursor.fetchall()
        elapsed_time = time() - start_time
        logging.info(f"Fetched data for {period} in {elapsed_time:.2f} seconds.")

    conn.close()
    return results

def push_to_gateway(data, gateway_url, job_name):
    start_time = time()
    
    for period, incidents in data.items():
        for incident in incidents:
            # Extract fields by index since fetchall returns tuples
            assignment_group, number, cause_ci, actual_severity, impacted_ci, opened_at = incident
            
            # Format the opened_at date to "mm-yy" format
            month_year = opened_at.strftime("%m-%y")
            
            metrics_data = (
                f"incident_count{{period=\"{period}\", assignment_group=\"{assignment_group}\", "
                f"number=\"{number}\", cause_ci=\"{cause_ci}\", actual_severity=\"{actual_severity}\", "
                f"impacted_ci=\"{impacted_ci}\", month_year=\"{month_year}\"}} 1\n"
            )
            response = requests.post(f"{gateway_url}/metrics/job/{job_name}", data=metrics_data)
            response.raise_for_status()

    elapsed_time = time() - start_time
    logging.info(f"Pushed metrics to Push Gateway in {elapsed_time:.2f} seconds.")

def main():
    parser = argparse.ArgumentParser(description="Fetch incidents from ServiceNow and push to Grafana Push Gateway.")
    parser.add_argument("--env", choices=["prod", "qa", "uat"], required=True, help="Environment (prod, qa, uat)")
    parser.add_argument("--gateway_url", required=True, help="Push Gateway URL")
    parser.add_argument("--job_name", required=True, help="Job name to send data with")

    args = parser.parse_args()

    # Define server and database based on environment
    env_config = {
        "prod": {"server": "prods", "database": "sndata"},
        "qa": {"server": "qas", "database": "sndata"},
        "uat": {"server": "uas", "database": "sndata"}
    }

    server = env_config[args.env]["server"]
    database = env_config[args.env]["database"]

    # Fetch data and push to Push Gateway
    data = fetch_incident_data(server, database)
    push_to_gateway(data, args.gateway_url, args.job_name)

if __name__ == "__main__":
    main()