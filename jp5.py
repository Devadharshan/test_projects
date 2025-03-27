import os
import datetime

# Ensure AutoSys environment is available
os.environ["AUTOSYS_ENV"] = "1"

def get_matching_jobs(job_patterns):
    """Fetch all jobs matching the given patterns using autorep."""
    jobs = {}

    for pattern in job_patterns:
        try:
            command = f'autorep -J {pattern}'
            result = os.popen(command).read()
            output_lines = result.splitlines()

            for line in output_lines:
                parts = line.split()
                if parts:
                    job_name = parts[0]
                    jobs[job_name] = {"pattern": pattern}  # Store job name + pattern

        except Exception as e:
            print(f"ERROR: Could not fetch jobs for pattern {pattern}: {e}")

    return jobs

def get_job_history(job_name):
    """Fetch success/failure history for a specific job."""
    try:
        command = f'autorep -J {job_name} -r'
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
            "pattern": jobs[job]["pattern"],
            "last_3_months": len(filter_by_date(history, 90)),
            "last_2_months": len(filter_by_date(history, 60)),
            "last_1_month": len(filter_by_date(history, 30)),
            "last_1_week": len(filter_by_date(history, 7)),
            "last_5_days": len(filter_by_date(history, 5)),
        }

    return job_stats