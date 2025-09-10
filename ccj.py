import os
import psutil

def find_large_files(root_dir, top_n=20):
    file_sizes = []

    # Walk through all folders/files
    for folder, _, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(folder, file)
            try:
                size = os.path.getsize(file_path)
                file_sizes.append((file_path, size))
            except Exception as e:
                print(f"Skipping {file_path}: {e}")

    # Sort by size (largest first)
    file_sizes.sort(key=lambda x: x[1], reverse=True)

    # Print disk usage of the share
    usage = psutil.disk_usage(root_dir)
    print(f"\nDisk usage for {root_dir}:")
    print(f"  Total: {usage.total/1024/1024/1024:.2f} GB")
    print(f"  Used : {usage.used/1024/1024/1024:.2f} GB")
    print(f"  Free : {usage.free/1024/1024/1024:.2f} GB\n")

    # Print top N largest files
    print(f"Top {top_n} largest files:\n")
    for path, size in file_sizes[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {path}")


# Example usage
root_directory = r"\\your\shared\folder"   # network share or local path
find_large_files(root_directory, top_n=20)