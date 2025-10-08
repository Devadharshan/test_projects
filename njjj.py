import os
import csv
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIG ===
WATCH_FOLDER = r"C:\windows_exporter\csv_input"        # Folder where new CSV files appear
PROM_FOLDER  = r"C:\windows_exporter\textfiles"        # Windows Exporter textfile collector folder
ROW_LABEL    = "row"                                   # Label name for row number


class CSVtoPromHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".csv"):
            return
        print(f"[+] New CSV detected: {event.src_path}")
        self.convert_csv_to_prom(event.src_path)

    def convert_csv_to_prom(self, csv_path):
        filename = os.path.basename(csv_path)
        prom_path = os.path.join(PROM_FOLDER, filename.replace(".csv", ".prom"))

        print(f"[*] Converting {filename} → {prom_path}")

        try:
            lines = []
            with open(csv_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                columns = reader.fieldnames

                if not columns:
                    print(f"[!] No columns found in {filename}. Skipping.")
                    return

                for idx, row in enumerate(reader, start=1):
                    for col in columns:
                        col_clean = col.strip().replace(" ", "_").replace("-", "_")
                        value = row.get(col, "").strip()

                        if value == "":
                            # empty cell → skip
                            continue

                        metric_name = f"csv_{col_clean}"

                        try:
                            # Try numeric
                            num_val = float(value)
                            line = f'{metric_name}{{{ROW_LABEL}="{idx}"}} {num_val}'
                        except ValueError:
                            # Non-numeric → use as label, set dummy value 1
                            line = f'{metric_name}{{{ROW_LABEL}="{idx}", value="{value}"}} 1'

                        lines.append(line)

            if not lines:
                print(f"[!] No valid data found in {filename}")
                return

            # Write to .prom file
            with open(prom_path, 'w', encoding='utf-8') as promfile:
                promfile.write("\n".join(lines))

            print(f"[✓] Created: {prom_path} ({len(lines)} metrics)")

        except Exception as e:
            print(f"[x] Error processing {csv_path}: {e}")


if __name__ == "__main__":
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    os.makedirs(PROM_FOLDER, exist_ok=True)

    print(f"🔍 Watching folder: {WATCH_FOLDER}")
    print(f"📊 Output folder: {PROM_FOLDER}")
    print("🚀 Waiting for new CSV files...\n")

    handler = CSVtoPromHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 Stopped watching.")
    observer.join()