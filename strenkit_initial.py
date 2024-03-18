import streamlit as st
import requests

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
    st.title("URL Status Checker")
    url = st.text_input("Enter URL to check:")
    if st.button("Check Status"):
        if url:
            status = check_url_status(url)
            st.write(f"The status of {url} is: {status}")
        else:
            st.write("Please enter a URL to check.")

if __name__ == "__main__":
    main()