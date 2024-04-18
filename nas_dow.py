import streamlit as st
import os
from pathlib import Path
import shutil

def list_files(directory):
    """List all files and folders in the given directory."""
    files = []
    folders = []
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            files.append(item)
        elif os.path.isdir(os.path.join(directory, item)):
            folders.append(item)
    return files, folders

def download_file(source_path, destination_path):
    """Download file from source path to destination path."""
    shutil.copy(source_path, destination_path)

def main():
    st.title("NAS File Downloader")

    nas_path = st.text_input("Enter NAS path:")
    if not nas_path:
        st.warning("Please enter a valid NAS path.")
        return

    if not os.path.exists(nas_path):
        st.warning("NAS path does not exist.")
        return

    st.write(f"Listing files and folders in {nas_path}:")
    files, folders = list_files(nas_path)

    selected_folder = st.selectbox("Select Folder:", folders)
    selected_folder_path = os.path.join(nas_path, selected_folder)

    selected_files = st.multiselect("Select Files:", files)

    download_button = st.button("Download Selected Files")
    if download_button:
        download_path = st.text_input("Enter download path:")
        if download_path:
            for file in selected_files:
                source_file_path = os.path.join(selected_folder_path, file)
                destination_file_path = os.path.join(download_path, file)
                download_file(source_file_path, destination_file_path)
            st.success("Files downloaded successfully.")
        else:
            st.warning("Please enter a valid download path.")

if __name__ == "__main__":
    main()






# new changes


import streamlit as st
import os
from pathlib import Path
import shutil
import subprocess

def switch_user(user_id, access):
    """Switch user using su command."""
    command = f"su -tr '{access}' {user_id}"
    return subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def list_files(directory):
    """List all files and folders in the given directory."""
    files = []
    folders = []
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            files.append(item)
        elif os.path.isdir(os.path.join(directory, item)):
            folders.append(item)
    return files, folders

def download_file(source_path, destination_path):
    """Download file from source path to destination path."""
    shutil.copy(source_path, destination_path)

def main():
    st.title("NAS File Downloader")

    user_id = st.text_input("Enter user ID:")
    if not user_id:
        st.warning("Please enter a valid user ID.")
        return

    access = st.text_input("Enter access type (optional, e.g., -p):")

    nas_path = st.text_input("Enter NAS path:")
    if not nas_path:
        st.warning("Please enter a valid NAS path.")
        return

    if not os.path.exists(nas_path):
        st.warning("NAS path does not exist.")
        return

    # Switch user
    if user_id and access:
        switch_user(user_id, access)

    st.write(f"Listing files and folders in {nas_path}:")
    files, folders = list_files(nas_path)

    selected_folder = st.selectbox("Select Folder:", folders)
    selected_folder_path = os.path.join(nas_path, selected_folder)

    selected_files = st.multiselect("Select Files:", files)

    download_button = st.button("Download Selected Files")
    if download_button:
        download_path = st.text_input("Enter download path:")
        if download_path:
            for file in selected_files:
                source_file_path = os.path.join(selected_folder_path, file)
                destination_file_path = os.path.join(download_path, file)
                download_file(source_file_path, destination_file_path)
            st.success("Files downloaded successfully.")
        else:
            st.warning("Please enter a valid download path.")

if __name__ == "__main__":
    main()





# test new changes

import os
import streamlit as st

def list_files(directory):
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            files.append(filename)
    return files

def download_file(directory, filename):
    filepath = os.path.join(directory, filename)
    with open(filepath, "rb") as f:
        data = f.read()
    return data

def main():
    st.title("NAS File Downloader")

    # Define NAS path
    nas_path = "/path/to/nas"

    # List folders in NAS path
    folders = [folder for folder in os.listdir(nas_path) if os.path.isdir(os.path.join(nas_path, folder))]

    # Display dropdown to select folder
    selected_folder = st.selectbox("Select Folder", folders)

    # List files in selected folder
    selected_folder_path = os.path.join(nas_path, selected_folder)
    files = list_files(selected_folder_path)

    # Display checkbox for file selection
    selected_files = st.multiselect("Select Files", files)

    # Download selected files
    if st.button("Download Selected Files"):
        for file in selected_files:
            file_data = download_file(selected_folder_path, file)
            st.download_button(label=f"Download {file}", data=file_data, file_name=file)

if __name__ == "__main__":
    main()




#system changes

import os
import streamlit as st

def list_files(directory):
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            files.append(filename)
    return files

def download_file(directory, filename):
    filepath = os.path.join(directory, filename)
    with open(filepath, "rb") as f:
        data = f.read()
    return data

def main():
    st.title("NAS File Downloader")

    # Input NAS path
    nas_path = st.text_input("Enter NAS Path")

    # Check if NAS path is valid
    if not os.path.isdir(nas_path):
        st.error("Invalid NAS path. Please provide a valid directory path.")
        return

    # List folders in NAS path
    folders = [folder for folder in os.listdir(nas_path) if os.path.isdir(os.path.join(nas_path, folder))]

    # Display dropdown to select folder
    selected_folder = st.selectbox("Select Folder", folders)

    # List files in selected folder
    selected_folder_path = os.path.join(nas_path, selected_folder)
    files = list_files(selected_folder_path)

    # Display checkbox for file selection
    selected_files = st.multiselect("Select Files", files)

    # Download selected files
    if st.button("Download Selected Files"):
        for file in selected_files:
            file_data = download_file(selected_folder_path, file)
            st.download_button(label=f"Download {file}", data=file_data, file_name=file)

if __name__ == "__main__":
    main()
