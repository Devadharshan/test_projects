import sybpydb
import requests
import argparse
from datetime import datetime

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
        cursor.execute(query)
        results[period] = cursor.fetchall()

    conn.close()
    return results

def push_to_gateway(data, gateway_url, job_name):
    for period, incidents in data.items():
        for incident in incidents:
            # Format the opened_at date to "mm-yy" format
            month_year = incident['opened_at'].strftime("%m-%y")
            metrics_data = (
                f"incident_count{{period=\"{period}\", assignment_group=\"{incident['assignment_group']}\", "
                f"number=\"{incident['number']}\", cause_ci=\"{incident['cause_ci']}\", "
                f"actual_severity=\"{incident['actual_severity']}\", impacted_ci=\"{incident['impacted_ci']}\", "
                f"month_year=\"{month_year}\"}} 1\n"
            )
            response = requests.post(f"{gateway_url}/metrics/job/{job_name}", data=metrics_data)
            response.raise_for_status()

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