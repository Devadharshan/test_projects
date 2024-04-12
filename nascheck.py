import streamlit as st
import os

def download_file(file_path):
    # Implement your download logic here
    # For example, you can use shutil.copy or requests.get to download the file
    pass

def list_files(directory):
    return os.listdir(directory)

def main():
    st.title("NAS File Downloader")

    nas_path = st.text_input("Enter NAS Path:")
    if nas_path:
        if os.path.exists(nas_path):
            st.write(f"Files in {nas_path}:")
            files = list_files(nas_path)
            for file in files:
                st.write(file)
            selected_file = st.selectbox("Select a file to download:", files)
            if st.button("Download"):
                download_file(os.path.join(nas_path, selected_file))
                st.success("File downloaded successfully!")
        else:
            st.error("Invalid path. Please enter a valid NAS path.")

if __name__ == "__main__":
    main()







import streamlit as st
import os
import shutil

def download_file(file_path):
    try:
        # Get the filename from the file path
        file_name = os.path.basename(file_path)
        # Construct the destination path in the local download folder
        destination_path = os.path.join(os.path.expanduser("~"), "Downloads", file_name)
        # Copy the file from the NAS path to the local download folder
        shutil.copy(file_path, destination_path)
        return True, destination_path
    except Exception as e:
        return False, str(e)

def list_files(directory):
    return os.listdir(directory)

def main():
    st.title("NAS File Downloader")

    nas_path = st.text_input("Enter NAS Path:")
    if nas_path:
        if os.path.exists(nas_path):
            st.write(f"Files in {nas_path}:")
            files = list_files(nas_path)
            for file in files:
                st.write(file)
            selected_file = st.selectbox("Select a file to download:", files)
            if st.button("Download"):
                download_success, download_path = download_file(os.path.join(nas_path, selected_file))
                if download_success:
                    st.success(f"File downloaded successfully! Download path: {download_path}")
                else:
                    st.error(f"Error downloading file: {download_path}")
        else:
            st.error("Invalid path. Please enter a valid NAS path.")

if __name__ == "__main__":
    main()