import os
import datetime
from collections import defaultdict

def scan_large_items(root_dir, min_size_mb=250, top_n=10):
    min_size_bytes = min_size_mb * 1024 * 1024
    large_files = []
    folder_sizes = defaultdict(int)

    print(f"\nScanning {root_dir} (including all subfolders) for items > {min_size_mb} MB...\n")

    # Walk once, accumulate file and folder sizes
    for folder, subfolders, files in os.walk(root_dir):
        folder_total = 0
        for file in files:
            try:
                file_path = os.path.join(folder, file)
                size = os.path.getsize(file_path)
                folder_total += size

                if size >= min_size_bytes:
                    mtime = os.path.getmtime(file_path)
                    last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    size_mb = size / 1024 / 1024
                    large_files.append((file_path, size_mb, last_modified))
            except Exception:
                pass

        # accumulate size into current folder
        folder_sizes[folder] += folder_total

        # also bubble size up into parent folders
        parent = os.path.dirname(folder)
        while parent and parent.startswith(root_dir):
            folder_sizes[parent] += folder_total
            new_parent = os.path.dirname(parent)
            if new_parent == parent:
                break
            parent = new_parent

    # Show large files
    if large_files:
        print(f"\nFiles > {min_size_mb} MB:\n")
        for path, size_mb, last_modified in sorted(large_files, key=lambda x: x[1], reverse=True):
            print(f"{size_mb:.2f} MB  |  {last_modified}  |  {path}")
    else:
        print("\nNo files above threshold.\n")

    # Show largest folders
    print(f"\nTop {top_n} largest folders:\n")
    for folder, size in sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {folder}")

    return large_files, folder_sizes


# ✅ Example usage
root_directory = r"\\server\share\folder"   # <-- change this
scan_large_items(root_directory, min_size_mb=250, top_n=10)