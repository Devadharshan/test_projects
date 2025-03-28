import re

def parse_autorep_output(output):
    """Parse autorep output correctly with dynamic column extraction."""
    jobs = {}

    found_header = False
    for line in output:
        # Ignore headers (detect "---" line which separates headers from data)
        if "---" in line:
            found_header = True
            continue  
        
        if not found_header:  # Skip lines before header
            continue

        parts = re.split(r'\s+', line.strip())  # Split by spaces

        if len(parts) < 5:  # Ensure there are enough columns
            continue

        job_name = parts[0]  # First column is Job Name
        last_start = parts[1] if parts[1] != "-" else "N/A"
        last_end = parts[2] if parts[2] != "-" else "N/A"
        status = parts[3]  # `ST/Ex` column (4th position)

        jobs[job_name] = {
            "last_start": last_start,
            "last_end": last_end,
            "status": status
        }

    return jobs