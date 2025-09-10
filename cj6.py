import os
import datetime

def find_large_files(root_dir, min_size_mb=250):
    min_size_bytes = min_size_mb * 1024 * 1024

    print(f"\nScanning for files > {min_size_mb} MB in {root_dir}...\n")
    large_files = []

    for folder, _, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(folder, file)
            try:
                size = os.path.getsize(file_path)
                if size >= min_size_bytes:
                    # Get last modified time
                    mtime = os.path.getmtime(file_path)
                    last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                    size_mb = size / 1024 / 1024
                    print(f"{size_mb:.2f} MB  |  {last_modified}  |  {file_path}")

                    large_files.append((file_path, size_mb, last_modified))
            except Exception:
                pass

    if not large_files:
        print("No files larger than threshold found.")
    return large_files


# ✅ Example usage
root_directory = r"\\your\shared\folder"
find_large_files(root_directory, min_size_mb=250)