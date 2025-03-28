def parse_autorep_output(output):
    jobs = {}

    for line in output:
        parts = line.split()

        if len(parts) < 6:  # Skip headers or invalid lines
            continue

        job_name = parts[0]
        last_start = parts[1] if parts[1] != "-" else "N/A"  # Handle missing fields
        last_end = parts[2] if parts[2] != "-" else "N/A"
        status = parts[3] if len(parts) > 3 else "Unknown"

        jobs[job_name] = {
            "last_start": last_start,
            "last_end": last_end,
            "status": status
        }

    return jobs