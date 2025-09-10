import os
import datetime

def get_folder_size(folder_path):
    """Calculate total size of a folder recursively."""
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
            except Exception:
                pass
    return total_size

def find_large_files(root_dir, min_size_mb=250):
    """Find all files > min_size_mb in root_dir (including subfolders)."""
    min_size_bytes = min_size_mb * 1024 * 1024
    large_files = []

    print(f"\nScanning {root_dir} (including subfolders) for files > {min_size_mb} MB...\n")

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

def find_large_folders(root_dir, top_n=10):
    """Find top N subfolders by total size."""
    folder_sizes = {}

    for folder, _, files in os.walk(root_dir):
        folder_size = 0
        for file in files:
            try:
                file_path = os.path.join(folder, file)
                folder_size += os.path.getsize(file_path)
            except Exception:
                pass
        folder_sizes[folder] = folder_sizes.get(folder, 0) + folder_size

    # Sort folders by size
    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop {top_n} largest folders under {root_dir}:\n")
    for folder, size in sorted_folders[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {folder}")

    return sorted_folders


# ✅ Example usage
root_directory = r"\\your\shared\folder"

# Step 1: list large files
find_large_files(root_directory, min_size_mb=250)

# Step 2: list heaviest subfolders
find_large_folders(root_directory, top_n=10)