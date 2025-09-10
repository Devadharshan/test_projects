import os
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_file_size(file_path, min_size_bytes):
    try:
        size = os.path.getsize(file_path)
        if size >= min_size_bytes:
            return (file_path, size)
    except Exception:
        pass
    return None

def find_large_files(root_dir, top_n=20, min_size_mb=10, max_workers=8):
    min_size_bytes = min_size_mb * 1024 * 1024
    file_sizes = []

    # Collect all file paths first
    file_paths = []
    for folder, _, files in os.walk(root_dir):
        for file in files:
            file_paths.append(os.path.join(folder, file))

    print(f"Scanning {len(file_paths)} files...")

    # Use ThreadPoolExecutor for parallel scanning
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_file_size, fp, min_size_bytes) for fp in file_paths]
        for future in as_completed(futures):
            result = future.result()
            if result:
                file_sizes.append(result)

    # Sort and take top N
    file_sizes.sort(key=lambda x: x[1], reverse=True)

    # Disk usage
    usage = psutil.disk_usage(root_dir)
    print(f"\nDisk usage for {root_dir}:")
    print(f"  Total: {usage.total/1024/1024/1024:.2f} GB")
    print(f"  Used : {usage.used/1024/1024/1024:.2f} GB")
    print(f"  Free : {usage.free/1024/1024/1024:.2f} GB\n")

    # Print results
    print(f"Top {top_n} largest files (> {min_size_mb} MB):\n")
    for path, size in file_sizes[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {path}")


# ✅ Example usage
root_directory = r"\\your\shared\folder"
find_large_files(root_directory, top_n=20, min_size_mb=10, max_workers=12)