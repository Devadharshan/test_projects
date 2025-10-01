import csv
import os
import re

# -------------------------------
# Configuration
# -------------------------------
csv_file = r"C:\data\files.csv"           # Path to your CSV file
prom_dir = r"C:\custom_metrics"           # Windows Exporter textfile folder
prom_file = os.path.join(prom_dir, "csv_metrics.prom")  # Output .prom file

# -------------------------------
# Helpers
# -------------------------------
def sanitize_label_name(name):
    """Sanitize column name to valid Prometheus label"""
    name = name.strip()
    name = re.sub(r'\W', '_', name)  # replace non-alphanumeric chars
    if not re.match(r'[a-zA-Z_]', name[0]):
        name = '_' + name
    return name

def is_numeric(value):
    try:
        float(value)
        return True
    except:
        return False

# Ensure output folder exists
if not os.path.exists(prom_dir):
    os.makedirs(prom_dir)

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
        numeric_cols = []

        for h in reader.fieldnames:
            value = row.get(h, "").strip().replace('\\', '\\\\')
            label_name = sanitize_label_name(h)

            if is_numeric(value):
                numeric_cols.append((label_name, value))
            else:
                labels.append('{0}="{1}"'.format(label_name, value))

        label_str = ",".join(labels)

        # If there are numeric columns, create separate metrics
        if numeric_cols:
            for col_name, col_value in numeric_cols:
                metric_line = 'csv_metric_{0}{{{1}}} {2}'.format(col_name, label_str, col_value)
                lines.append(metric_line)
        else:
            # No numeric columns: use dummy value 1
            lines.append('csv_metric{{{0}}} 1'.format(label_str))

# -------------------------------
# Safe write: atomic + ASCII + final newline
# -------------------------------
tmp_file = prom_file + ".tmp"
with open(tmp_file, 'wb') as f:
    f.write("\n".join(lines).encode('ascii', 'replace') + "\n")
os.rename(tmp_file, prom_file)

print("Prometheus file generated at {}".format(prom_file))