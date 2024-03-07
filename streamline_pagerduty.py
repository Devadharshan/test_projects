import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

# Replace these with your actual PagerDuty API credentials
PAGERDUTY_API_KEY = 'YOUR_PAGERDUTY_API_KEY'
PAGERDUTY_API_ENDPOINT = 'https://api.pagerduty.com/incidents'

# Set up basic authentication for PagerDuty API
auth = HTTPBasicAuth(PAGERDUTY_API_KEY, '')

# Streamlit app
st.title("PagerDuty Alerts Viewer")

# Function to fetch and display PagerDuty alerts
def get_pagerduty_alerts():
    st.subheader("Latest PagerDuty Alerts")

    try:
        # Make a request to PagerDuty API to get incidents
        response = requests.get(PAGERDUTY_API_ENDPOINT, auth=auth)
        response.raise_for_status()
        incidents = response.json()["incidents"]

        # Display alerts in a table
        for incident in incidents:
            st.write(f"**Incident ID:** {incident['id']}")
            st.write(f"**Description:** {incident['summary']}")
            st.write(f"**Status:** {incident['status']}")
            st.write("---")
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error: {errh}")
    except requests.exceptions.RequestException as err:
        st.error(f"Something went wrong: {err}")

# Display PagerDuty alerts
get_pagerduty_alerts()
