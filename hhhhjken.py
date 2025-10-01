import csv
import os
import re

csv_file = r"C:\data\files.csv"
prom_dir = r"C:\custom_metrics"
prom_file = os.path.join(prom_dir, "csv_metrics.prom")

if not os.path.exists(prom_dir):
    os.makedirs(prom_dir)

lines = []
lines.append("# HELP csv_metric Generic CSV metric")
lines.append("# TYPE csv_metric gauge")

def sanitize_label_name(name):
    # Prometheus label names must match [a-zA-Z_][a-zA-Z0-9_]*
    name = name.strip()
    name = re.sub(r'\W', '_', name)  # replace non-alphanumeric with _
    if not re.match(r'[a-zA-Z_]', name[0]):
        name = '_' + name
    return name

with open(csv_file, 'rb') as f:
    reader = csv.DictReader(f)
    headers = [sanitize_label_name(h) for h in reader.fieldnames]

    for row in reader:
        labels = []
        for i, h in enumerate(reader.fieldnames):
            value = row.get(h, "").strip().replace('\\', '\\\\')
            sanitized_h = headers[i]
            labels.append('{0}="{1}"'.format(sanitized_h, value))
        label_str = ",".join(labels)

        # Example numeric metric: just 1 for each row
        line = 'csv_metric{{{0}}} 1'.format(label_str)
        lines.append(line)

with open(prom_file, 'wb') as f:
    f.write("\n".join(lines))

print("Prometheus file generated at {}".format(prom_file))