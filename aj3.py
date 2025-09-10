import os
import psutil

def get_folder_sizes(root_dir, top_n=20):
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

    usage = psutil.disk_usage(root_dir)
    print(f"\nDisk usage for {root_dir}:")
    print(f"  Total: {usage.total/1024/1024/1024:.2f} GB")
    print(f"  Used : {usage.used/1024/1024/1024:.2f} GB")
    print(f"  Free : {usage.free/1024/1024/1024:.2f} GB\n")

    print(f"Top {top_n} largest folders:\n")
    for folder, size in sorted_folders[:top_n]:
        print(f"{size/1024/1024:.2f} MB  -  {folder}")


# ✅ Example usage
root_directory = r"\\your\shared\folder"
get_folder_sizes(root_directory, top_n=20)