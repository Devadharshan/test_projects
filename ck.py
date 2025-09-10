import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Shares / root folders to scan
shares = [
    r"\\SERVER\Share1",
    r"\\SERVER\Share2",
    r"D:\LocalFolder"
]

# Minimum file size in MB
min_size_mb = 250
min_size_bytes = min_size_mb * 1024 * 1024

# Function to scan a single folder
def scan_folder(folder_path):
    large_files = []
    folder_total_size = 0

    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file():
                    try:
                        size = entry.stat().st_size
                        folder_total_size += size
                        if size >= min_size_bytes:
                            large_files.append({
                                "file": entry.path,
                                "size_mb": round(size / (1024*1024), 2),
                                "last_modified": datetime.fromtimestamp(entry.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            })
                    except:
                        continue
                elif entry.is_dir():
                    # Return the subfolder path to be scanned in a thread
                    yield entry.path
    except:
        pass

    yield {"large_files": large_files, "folder_size": folder_total_size}

# Main scanning function with threading
def scan_share_multithreaded(share_path, max_workers=8):
    all_large_files = []
    folder_sizes = {}

    # Queue of folders to scan
    folders_to_scan = [share_path]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        while folders_to_scan or futures:
            # Submit new folder scans
            while folders_to_scan:
                folder = folders_to_scan.pop()
                futures[executor.submit(scan_folder, folder)] = folder

            # Process completed futures
            for future in as_completed(futures):
                result = future.result()
                folder = futures[future]

                # Result can be a dict (folder summary) or generator of subfolders
                if isinstance(result, dict):
                    all_large_files.extend(result.get("large_files", []))
                    folder_sizes[folder] = round(result.get("folder_size", 0) / (1024*1024), 2)
                else:
                    for item in result:
                        if isinstance(item, str):
                            folders_to_scan.append(item)
                        else:
                            all_large_files.extend(item.get("large_files", []))
                            folder_sizes[folder] = round(item.get("folder_size", 0) / (1024*1024), 2)

                del futures[future]
                break  # Break to allow adding more folders to executor

    return all_large_files, folder_sizes

# Scan all shares
for share in shares:
    print(f"\nScanning share: {share}\n{'='*50}")
    files, folders = scan_share_multithreaded(share, max_workers=8)

    print(f"\nFiles > {min_size_mb} MB:\n")
    for f in files:
        print(f"{f['file']} | Size: {f['size_mb']} MB | Last Modified: {f['last_modified']}")

    print("\nTop 10 largest folders:\n")
    top_folders = sorted(folders.items(), key=lambda x: x[1], reverse=True)[:10]
    for folder, size in top_folders:
        print(f"{folder} | Size: {size} MB")