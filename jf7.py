import re

def parse_autorep_output(output):
    """Parse autorep output dynamically based on column lengths."""
    jobs = {}

    found_header = False
    for line in output:
        # Ignore headers (detect "---" line which separates headers from data)
        if "---" in line:
            found_header = True
            continue  
        
        if not found_header:  # Skip lines before header
            continue

        # Match: Job Name | Last Start | Last End | Status (ST/Ex)
        match = re.match(r"(\S+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\-)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\-)\s+(\S+)", line)

        if match:
            job_name, last_start, last_end, status = match.groups()

            jobs[job_name] = {
                "last_start": last_start if last_start != "-" else "N/A",
                "last_end": last_end if last_end != "-" else "N/A",
                "status": status
            }

    return jobs