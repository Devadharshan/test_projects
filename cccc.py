import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Shares / root folders to scan
shares = [
    r"\\SERVER\Share1",
    r"\\SERVER\Share2",
    r"D:\LocalFolder"
]

# Minimum size in MB
min_size_mb = 250
min_size_bytes = min_size_mb * 1024 * 1024

def get_folder_size(folder_path):
    """Calculate total size of a folder (recursive)"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
                except:
                    continue
    except:
        pass
    return total_size

def scan_large_files(folder_path):
    """Scan for files >= min_size_bytes"""
    large_files = []
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                size = os.path.getsize(fp)
                if size >= min_size_bytes:
                    large_files.append({
                        "file": fp,
                        "size_mb": round(size / (1024*1024), 2),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M:%S")
                    })
            except:
                continue
    return large_files

def scan_share_optimized(share_path, max_workers=4):
    # First, list immediate subfolders
    try:
        subfolders = [os.path.join(share_path, f) for f in os.listdir(share_path) if os.path.isdir(os.path.join(share_path, f))]
    except:
        subfolders = []

    folder_sizes = {}
    large_files = []

    # Step 1: Calculate folder sizes in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_folder_size, f): f for f in subfolders}
        for future in as_completed(futures):
            folder = futures[future]
            size = future.result()
            folder_sizes[folder] = round(size / (1024*1024), 2)

    # Step 2: Only scan folders larger than min_size_mb
    folders_to_scan = [f for f, size in folder_sizes.items() if size >= min_size_mb]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_large_files, f): f for f in folders_to_scan}
        for future in as_completed(futures):
            files = future.result()
            large_files.extend(files)

    # Include root folder if big enough
    root_size = get_folder_size(share_path)
    folder_sizes[share_path] = round(root_size / (1024*1024), 2)
    if root_size >= min_size_bytes:
        large_files.extend(scan_large_files(share_path))

    return large_files, folder_sizes

# Scan all shares
for share in shares:
    print(f"\nScanning share: {share}\n{'='*50}")
    files, folders = scan_share_optimized(share, max_workers=8)

    print(f"\nFiles > {min_size_mb} MB:\n")
    for f in files:
        print(f"{f['file']} | Size: {f['size_mb']} MB | Last Modified: {f['last_modified']}")

    print("\nTop 10 largest folders:\n")
    top_folders = sorted(folders.items(), key=lambda x: x[1], reverse=True)[:10]
    for folder, size in top_folders:
        print(f"{folder} | Size: {size} MB")