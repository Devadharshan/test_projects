import csv
import os

# Path to CSV file
csv_file = r"C:\data\files.csv"

# Windows Exporter textfile folder
prom_dir = r"C:\custom_metrics"

# Output .prom file
prom_file = os.path.join(prom_dir, "csv_metrics.prom")

# Ensure folder exists
if not os.path.exists(prom_dir):
    os.makedirs(prom_dir)

lines = []
lines.append("# HELP custom_csv_metric Generic CSV metric")
lines.append("# TYPE custom_csv_metric gauge")

with open(csv_file, 'rb') as f:
    reader = csv.DictReader(f)
    headers = [h.strip() for h in reader.fieldnames]  # strip spaces

    # Use first two columns: label and value
    label_col = headers[0]
    value_col = headers[1]

    for row in reader:
        label = row[label_col].strip().replace('\\', '\\\\')
        value = row[value_col].strip()
        line = 'custom_csv_metric{{label="{0}"}} {1}'.format(label, value)
        lines.append(line)

with open(prom_file, 'wb') as f:
    f.write("\n".join(lines))

print("Prometheus file generated at {}".format(prom_file))