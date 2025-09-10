import os

def get_folder_sizes(root_dir, top_n=20):
    """Find top N folders by total size (including subfiles)."""
    folder_sizes = {}

    for folder, _, files in os.walk(root_dir):
        total_size = 0
        for file in files:
            try:
                file_path = os.path.join(folder, file)
                total_size += os.path.getsize(file_path)
            except Exception:
                pass
        folder_sizes[folder] = folder_sizes.get(folder, 0) + total_size

    # Sort by size
    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop {top_n} largest folders in {root_dir}:\n")
    for folder, size in sorted_folders[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {folder}")

    return sorted_folders


def get_large_files(folder, top_n=20, min_size_mb=10):
    """Find top N files in a specific folder (recursively)."""
    file_sizes = []
    min_size_bytes = min_size_mb * 1024 * 1024

    for root, _, files in os.walk(folder):
        for file in files:
            try:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                if size >= min_size_bytes:
                    file_sizes.append((file_path, size))
            except Exception:
                pass

    # Sort by size
    file_sizes.sort(key=lambda x: x[1], reverse=True)

    print(f"\nTop {top_n} largest files in {folder} (> {min_size_mb} MB):\n")
    for path, size in file_sizes[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {path}")

    return file_sizes


# ✅ Example usage
root_directory = r"\\your\shared\folder"

# Step 1: find heavy folders
top_folders = get_folder_sizes(root_directory, top_n=10)

# Step 2: drill into the heaviest folder
if top_folders:
    biggest_folder = top_folders[0][0]
    get_large_files(biggest_folder, top_n=20, min_size_mb=10)