import csv
import os
import re

# -------------------------------
# Configuration
# -------------------------------
csv_file = r"C:\data\files.csv"          # Your CSV file
prom_dir = r"C:\custom_metrics"          # Windows Exporter textfile folder
prom_file = os.path.join(prom_dir, "csv_metrics.prom")  # Output .prom file

# Ensure output folder exists
if not os.path.exists(prom_dir):
    os.makedirs(prom_dir)

# -------------------------------
# Helper function to sanitize Prometheus label names
# -------------------------------
def sanitize_label_name(name):
    # Prometheus label names: [a-zA-Z_][a-zA-Z0-9_]*
    name = name.strip()
    name = re.sub(r'\W', '_', name)  # replace non-alphanumeric with _
    if not re.match(r'[a-zA-Z_]', name[0]):
        name = '_' + name
    return name

# -------------------------------
# Read CSV and generate .prom
# -------------------------------
lines = []
lines.append("# HELP csv_metric Generic CSV metric")
lines.append("# TYPE csv_metric gauge")

with open(csv_file, 'rb') as f:  # Python 2.7
    reader = csv.DictReader(f)
    headers = [h.strip() for h in reader.fieldnames]

    for row in reader:
        labels = []
        for h in reader.fieldnames:
            value = row.get(h, "").strip().replace('\\', '\\\\')
            label_name = sanitize_label_name(h)
            labels.append('{0}="{1}"'.format(label_name, value))
        label_str = ",".join(labels)

        # Numeric dummy value
        line = 'csv_metric{{{0}}} 1'.format(label_str)
        lines.append(line)

# Write to .prom file
with open(prom_file, 'wb') as f:
    f.write("\n".join(lines))

print("Prometheus file generated at {}".format(prom_file))