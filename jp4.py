import os
import datetime

AUTOREP_PATH = "C:\\Program Files\\AutoSys\\bin\\autorep.exe"  # Update this

def get_matching_jobs(job_patterns):
    """Fetch all jobs matching the given patterns using autorep."""
    jobs = set()

    for pattern in job_patterns:
        try:
            command = f'"{AUTOREP_PATH}" -J {pattern}'
            result = os.popen(command).read()  # Run command and capture output
            output_lines = result.splitlines()

            for line in output_lines:
                parts = line.split()
                if parts:
                    jobs.add(parts[0])  # Collect unique job names

        except Exception as e:
            print(f"ERROR: Could not fetch jobs for pattern {pattern}: {e}")

    return list(jobs)

def get_job_history(job_name):
    """Fetch success/failure history for a specific job."""
    try:
        command = f'"{AUTOREP_PATH}" -J {job_name} -r'
        result = os.popen(command).read()
        output_lines = result.splitlines()

        history = []
        for line in output_lines:
            parts = line.split()
            if len(parts) >= 3 and parts[1] in ["SU", "FA"]:
                history.append({"date": parts[0], "status": parts[1]})

        return history

    except Exception as e:
        print(f"ERROR: Could not fetch job history for {job_name}: {e}")
        return []

def filter_by_date(history, days):
    """Filter history by the past N days."""
    cutoff_date = datetime.datetime.today() - datetime.timedelta(days=days)
    return [entry for entry in history if datetime.datetime.strptime(entry["date"], "%Y-%m-%d") >= cutoff_date]

def analyze_job_failures(jobs):
    """Get job failures for various time ranges."""
    job_stats = {}

    for job in jobs:
        history = get_job_history(job)

        job_stats[job] = {
            "last_3_months": len(filter_by_date(history, 90)),
            "last_2_months": len(filter_by_date(history, 60)),
            "last_1_month": len(filter_by_date(history, 30)),
            "last_1_week": len(filter_by_date(history, 7)),
            "last_5_days": len(filter_by_date(history, 5)),
        }

    return job_stats