import streamlit as st
import psutil

def get_nas_space(path):
    try:
        usage = psutil.disk_usage(path)
        total_space = usage.total / (1024 ** 3)  # Convert bytes to gigabytes
        free_space = usage.free / (1024 ** 3)
        used_space = usage.used / (1024 ** 3)
        return total_space, free_space, used_space
    except Exception as e:
        return str(e)

def main():
    st.title("NAS Space Viewer")
    
    nas_path = st.text_input("Enter NAS path:")
    
    if st.button("Check Space"):
        if nas_path:
            total, free, used = get_nas_space(nas_path)
            st.write(f"Total Space: {total:.2f} GB")
            st.write(f"Free Space: {free:.2f} GB")
            st.write(f"Used Space: {used:.2f} GB")
        else:
            st.warning("Please enter a valid NAS path.")

if __name__ == "__main__":
    main()






import os
import streamlit as st

def get_disk_space(path):
    total, used, free = map(int, os.statvfs(path).fuse_blocks[:3])
    return total * 4, used * 4, free * 4  # Convert from 1k blocks to MB

def main():
    st.title("Disk Space Viewer")

    directory_path = st.text_input("Enter Directory Path:", "/your/directory/path")
    if not os.path.exists(directory_path):
        st.error("Invalid path. Please enter a valid directory path.")
        return

    total_space, used_space, free_space = get_disk_space(directory_path)

    st.write(f"Total Space in {directory_path}: {total_space} MB")
    st.write(f"Used Space in {directory_path}: {used_space} MB")
    st.write(f"Free Space in {directory_path}: {free_space} MB")

if __name__ == "__main__":
    main()





# changes

def get_disk_space(path):
    disk_usage = psutil.disk_usage(path)
    total_space = disk_usage.total
    used_space = disk_usage.used
    free_space = disk_usage.free
    return total_space, used_space, free_space