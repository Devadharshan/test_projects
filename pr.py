import csv
import os

# Path to CSV file
csv_file = r"C:\data\files.csv"

# Windows Exporter textfile folder
prom_dir = r"C:\custom_metrics"

# Output .prom file
prom_file = os.path.join(prom_dir, "csv_metrics.prom")

# Minimum requirement: ensure folder exists
os.makedirs(prom_dir, exist_ok=True)

lines = []
lines.append("# HELP custom_file_size_bytes File size in bytes")
lines.append("# TYPE custom_file_size_bytes gauge")

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        filename = row['filename'].replace('\\', '\\\\')  # escape backslashes
        size = row['size_bytes']
        lines.append(f'custom_file_size_bytes{{filename="{filename}"}} {size}')

# Write to .prom file
with open(prom_file, 'w', encoding='ascii') as f:
    f.write("\n".join(lines))

print(f"Prometheus file generated at {prom_file}")