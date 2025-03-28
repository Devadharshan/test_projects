import re

def parse_autorep_output(output):
    """Parse autorep output correctly, handling misaligned columns."""
    jobs = {}

    for line in output:
        parts = re.split(r'\s+', line.strip())  # Split on any whitespace

        if len(parts) < 4:  # Skip headers or invalid lines
            continue

        job_name = parts[0]
        last_start = parts[1] if parts[1] and parts[1] != "-" else "N/A"
        last_end = parts[2] if len(parts) > 2 and parts[2] != "-" else "N/A"
        status = parts[3] if len(parts) > 3 else "Unknown"

        jobs[job_name] = {
            "last_start": last_start,
            "last_end": last_end,
            "status": status
        }

    return jobs