import os
import datetime
import concurrent.futures

# 🔹 Load the module ONCE globally
MODULE_LOADED = False

def load_module():
    """Loads the AutoSys module only once."""
    global MODULE_LOADED
    if not MODULE_LOADED:
        os.system("module load jobsched/QNA")
        MODULE_LOADED = True

def run_autorep_command(command):
    """Runs an autorep command and returns the output lines."""
    load_module()  # Ensure module is loaded
    try:
        result = os.popen(command).read()
        return result.splitlines()
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def get_matching_jobs(job_patterns):
    """Fetch job names matching patterns using autorep in parallel."""
    jobs = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        commands = [f"autorep -J \"{pattern}\"" for pattern in job_patterns]  # Wrap pattern in quotes
        results = executor.map(run_autorep_command, commands)

        for result in results:
            for line in result:
                parts = line.split()
                if parts:
                    job_name = parts[0]
                    jobs[job_name] = {"pattern": job_patterns[0]}  # Store job name + pattern

    return jobs

def get_job_history(job_name):
    """Fetch success/failure history for a job in parallel."""
    command = f"autorep -J \"{job_name}\" -r"  # Wrap job name in quotes
    result = run_autorep_command(command)

    history = []
    for line in result:
        parts = line.split()
        if len(parts) >= 3 and parts[1] in ["SU", "FA"]:
            history.append({"date": parts[0], "status": parts[1]})

    return history

def filter_by_date(history, days):
    """Filter history by the past N days."""
    cutoff_date = datetime.datetime.today() - datetime.timedelta(days=days)
    return [entry for entry in history if datetime.datetime.strptime(entry["date"], "%Y-%m-%d") >= cutoff_date]

def analyze_job_failures(job_patterns):
    """Fetch job failures for various time ranges in parallel."""
    jobs = get_matching_jobs(job_patterns)
    job_stats = {}

    # Run job history fetching in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        job_history_results = executor.map(get_job_history, jobs.keys())

    for job, history in zip(jobs.keys(), job_history_results):
        job_stats[job] = {
            "pattern": jobs[job]["pattern"],
            "last_3_months": len(filter_by_date(history, 90)),
            "last_2_months": len(filter_by_date(history, 60)),
            "last_1_month": len(filter_by_date(history, 30)),
            "last_1_week": len(filter_by_date(history, 7)),
            "last_5_days": len(filter_by_date(history, 5)),
        }

    return job_stats