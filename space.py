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