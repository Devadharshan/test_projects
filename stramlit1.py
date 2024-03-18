import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

def check_url_status(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return "Up"
        else:
            return "Down"
    except requests.ConnectionError:
        return "Down"

def main():
    st.title("URL Status Report")

    # File upload
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write(df)

        # Check URL status
        statuses = []
        for index, row in df.iterrows():
            url = row['URL']
            status = check_url_status(url)
            statuses.append(status)
            df.at[index, 'Status'] = status

        # Display report
        st.write(df)

        # Plot failed URLs
        failed_count = statuses.count("Down")
        if failed_count > 0:
            st.write(f"Number of failed URLs: {failed_count}")
            failed_urls = df[df['Status'] == 'Down']['URL']
            plt.figure(figsize=(10, 6))
            plt.barh(failed_urls, [1] * len(failed_urls), color='red')
            plt.xlabel('Status')
            plt.title('Failed URLs')
            st.pyplot()

if __name__ == "__main__":
    main()