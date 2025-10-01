import csv
import os

csv_file = r"C:\data\files.csv"
prom_dir = r"C:\custom_metrics"
prom_file = os.path.join(prom_dir, "csv_metrics.prom")

if not os.path.exists(prom_dir):
    os.makedirs(prom_dir)

lines = []
lines.append("# HELP csv_metric Generic CSV metric")
lines.append("# TYPE csv_metric gauge")

with open(csv_file, 'rb') as f:
    reader = csv.DictReader(f)
    headers = [h.strip() for h in reader.fieldnames]

    # Identify numeric columns
    numeric_cols = []
    for h in headers:
        try:
            float(next(reader)[h])
            numeric_cols.append(h)
            f.seek(0)
            next(reader)  # skip header
        except:
            f.seek(0)
            next(reader)
            continue

    f.seek(0)
    next(reader)  # skip header

    for row in reader:
        # Use non-numeric columns as labels
        labels = []
        for h in headers:
            if h not in numeric_cols:
                value = row[h].strip().replace('\\', '\\\\')
                labels.append('{0}="{1}"'.format(h, value))
        label_str = ",".join(labels)

        # Add numeric metrics
        for col in numeric_cols:
            try:
                value = float(row[col].strip())
                line = 'csv_metric{{{0},column="{1}"}} {2}'.format(label_str, col, value)
                lines.append(line)
            except:
                continue

with open(prom_file, 'wb') as f:
    f.write("\n".join(lines))

print("Prometheus file generated at {}".format(prom_file))