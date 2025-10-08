import os
import csv

# === CONFIG ===
CSV_FOLDER  = r"C:\windows_exporter\csv_input"         # Folder containing your CSV files
PROM_FOLDER = r"C:\windows_exporter\textfiles"         # Windows Exporter textfile collector folder
ROW_LABEL   = "row"                                   # Label name for row number

def convert_csv_to_prom(csv_path, prom_path):
    """Convert one CSV file to a Prometheus metrics file."""
    print(f"[*] Processing: {os.path.basename(csv_path)}")

    try:
        lines = []
        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            columns = reader.fieldnames

            if not columns:
                print(f"[!] No columns found in {csv_path}, skipping.")
                return

            for idx, row in enumerate(reader, start=1):
                for col in columns:
                    col_clean = col.strip().replace(" ", "_").replace("-", "_")
                    value = (row.get(col) or "").strip()

                    if value == "":
                        continue  # Skip empty cells

                    metric_name = f"csv_{col_clean}"

                    try:
                        # Numeric value
                        num_val = float(value)
                        line = f'{metric_name}{{{ROW_LABEL}="{idx}"}} {num_val}'
                    except ValueError:
                        # Non-numeric -> treat as label
                        val_sanitized = value.replace('"', '\\"')
                        line = f'{metric_name}{{{ROW_LABEL}="{idx}", value="{val_sanitized}"}} 1'

                    lines.append(line)

        if lines:
            with open(prom_path, 'w', encoding='utf-8') as promfile:
                promfile.write("\n".join(lines))
            print(f"[✓] Created: {prom_path} ({len(lines)} metrics)")
        else:
            print(f"[!] No valid data in {csv_path}")

    except Exception as e:
        print(f"[x] Error processing {csv_path}: {e}")

def main():
    os.makedirs(CSV_FOLDER, exist_ok=True)
    os.makedirs(PROM_FOLDER, exist_ok=True)

    csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith('.csv')]
    if not csv_files:
        print("[!] No CSV files found in input folder.")
        return

    for csv_file in csv_files:
        csv_path = os.path.join(CSV_FOLDER, csv_file)
        prom_path = os.path.join(PROM_FOLDER, csv_file.replace(".csv", ".prom"))
        convert_csv_to_prom(csv_path, prom_path)

    print("\n✅ Conversion complete. Metrics ready for Windows Exporter.")

if __name__ == "__main__":
    main()