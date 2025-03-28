from fastapi import FastAPI, HTTPException
import subprocess
import re
from datetime import datetime, timedelta

app = FastAPI()

# Define time ranges for stats calculation
TIME_RANGES = {
    "past_3_months": 90,
    "past_2_months": 60,
    "past_1_month": 30,
    "last_week": 7,
    "last_5_days": 5
}

# Function to run autorep command with history
def run_autorep(job_patterns, history=False):
    command = f"module load jobsched/QNA && autorep -J {job_patterns}"
    if history:
        command += " -r 90"  # Retrieve past 90 days of history
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Error running autorep")
    
    return result.stdout.split("\n")

# Function to parse autorep output dynamically
def parse_autorep_output(output):
    jobs = {}

    found_header = False
    for line in output:
        if "---" in line:
            found_header = True
            continue  
        
        if not found_header:
            continue

        match = re.match(r"(\S+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\-)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\-)\s+(\S+)", line)

        if match:
            job_name, last_start, last_end, status = match.groups()
            jobs.setdefault(job_name, []).append({
                "last_start": last_start if last_start != "-" else "N/A",
                "last_end": last_end if last_end != "-" else "N/A",
                "status": status
            })

    return jobs

# Function to process job statistics over time ranges
def process_job_stats(jobs):
    job_stats = {}

    for job, runs in jobs.items():
        job_stats[job] = {k: {"failures": 0, "other_statuses": {}} for k in TIME_RANGES}

        for run in runs:
            last_start = run["last_start"]
            status = run["status"]

            if last_start == "N/A":
                continue  # Skip if there's no valid last start time

            try:
                job_date = datetime.strptime(last_start, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue  # Skip invalid date formats

            for period, days in TIME_RANGES.items():
                if job_date >= datetime.now() - timedelta(days=days):
                    if status in ["FA", "FAILURE"]:  # Failure statuses
                        job_stats[job][period]["failures"] += 1
                    else:  # Other statuses
                        job_stats[job][period]["other_statuses"][status] = job_stats[job][period]["other_statuses"].get(status, 0) + 1

    return job_stats

# Existing API: Retrieve job details
@app.post("/jobs/")
def get_jobs(job_patterns: list):
    try:
        output = run_autorep(",".join(job_patterns))
        jobs = parse_autorep_output(output)

        return {"jobs": jobs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New API: Retrieve job statistics using autorep history
@app.post("/stats/")
def get_job_statistics(job_patterns: list):
    try:
        output = run_autorep(",".join(job_patterns), history=True)
        jobs = parse_autorep_output(output)
        job_stats = process_job_stats(jobs)

        return {"job_statistics": job_stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))