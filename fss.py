import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

init(autoreset=True)

# --- CONFIG ---
FOLDER_PATH = r"\\your\shared\folder\path"  # Change this
MIN_SIZE_GB = 1
MAX_DEPTH = 3  # Limit recursion for speed
THREADS = 10   # Increase if CPU can handle
# ---------------

def get_size_gb(size_bytes):
    return size_bytes / (1024 ** 3)

def color_for_size(size_gb):
    if size_gb >= 10:
        return Fore.RED
    elif size_gb >= 5:
        return Fore.YELLOW
    return Fore.GREEN

def scan_directory(path, depth=0):
    """Recursively scan a folder up to MAX_DEPTH."""
    results = []
    if depth > MAX_DEPTH:
        return results

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_file(follow_symlinks=False):
                        size_bytes = entry.stat().st_size
                        size_gb = get_size_gb(size_bytes)
                        if size_gb >= MIN_SIZE_GB:
                            results.append((entry.path, size_gb))
                    elif entry.is_dir(follow_symlinks=False):
                        results.extend(scan_directory(entry.path, depth + 1))
                except Exception:
                    continue
    except PermissionError:
        pass
    return results

def list_large_files(folder_path):
    large_files = []
    subdirs = []
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    subdirs.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    size_bytes = entry.stat().st_size
                    size_gb = get_size_gb(size_bytes)
                    if size_gb >= MIN_SIZE_GB:
                        large_files.append((entry.path, size_gb))
    except Exception:
        pass

    # Run folder scans in parallel
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(scan_directory, d, 1) for d in subdirs]
        for f in as_completed(futures):
            try:
                large_files.extend(f.result())
            except Exception:
                pass

    large_files.sort(key=lambda x: x[1], reverse=True)
    return large_files

def display_results(files):
    if not files:
        print(Fore.CYAN + "No files larger than threshold.")
        return

    print(f"\n{'File Path':<100} | {'Size (GB)':>10}")
    print("-" * 115)
    for path, size_gb in files:
        color = color_for_size(size_gb)
        print(color + f"{path:<100} | {size_gb:>10.2f}")

if __name__ == "__main__":
    print(f"\nScanning {FOLDER_PATH} for files > {MIN_SIZE_GB} GB (depth ≤ {MAX_DEPTH}) ...\n")
    results = list_large_files(FOLDER_PATH)
    display_results(results)