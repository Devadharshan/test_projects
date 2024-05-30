import streamlit as st
import pyodbc
import subprocess

def connect_sybase_server(server, username, password, database):
    # Connect to Sybase server
    conn = pyodbc.connect(f'DRIVER=FreeTDS;SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
    return conn

def execute_unix_command(command):
    # Execute Unix command
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

# Streamlit app
st.title("Sybase Server & Unix Command App")

# Connection inputs
st.subheader("Sybase Server Connection")
server = st.text_input("Server")
username = st.text_input("Username")
password = st.text_input("Password", type="password")
database = st.text_input("Database")

# Connect button
if st.button("Connect to Sybase Server"):
    conn = connect_sybase_server(server, username, password, database)
    st.success("Connected to Sybase server successfully!")

# Unix command execution
st.subheader("Unix Command Execution")
unix_command = st.text_input("Enter Unix command")
if st.button("Execute Unix Command"):
    output = execute_unix_command(unix_command)
    st.code(output)

st.write("Note: Make sure you have FreeTDS installed for Sybase connectivity and appropriate permissions for Unix commands.")