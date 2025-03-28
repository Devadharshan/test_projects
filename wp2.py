from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import subprocess
import re
from datetime import datetime, timedelta

app = FastAPI()

class JobPatternsRequest(BaseModel):
    job_patterns: List[str]

TIME_RANGES = {
    "past_3_months": 90,
    "past_2_months": 60,
    "past_1_month": 30,
    "last_week": 7,
    "last_5_days": 5
}

# ✅ Load Module Once at Startup
def load_jobsched_module():
    """Loads jobsched module once at startup."""
    try:
        subprocess.run("module load jobsched/QNA", shell=True, check=True, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Module Load Failed: {str(e)}")

# ✅ Load module at startup
load_jobsched_module()

def run_autorep(job_patterns, history=False):
    """Runs autorep command using subprocess with multiple job patterns."""
    job_patterns_str = " ".join(job_patterns)  # Convert list to space-separated string

    command = f"autorep -J {job_patterns_str}"
    if history:
        command += " -r 90"

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, executable="/bin/bash")
        output = result.stdout.strip()

        if "ERROR" in output or not output:
            raise Exception("Autorep command failed or returned no data.")

        return output.split("\n")  # Convert output into list of lines

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error running autorep: {str(e)}")

def parse_autorep_output(output):
    """Parses autorep command output correctly for multiple jobs."""
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
            jobs[job_name] = {
                "last_start": last_start if last_start != "-" else "N/A",
                "last_end": last_end if last_end != "-" else "N/A",
                "status": status
            }

    return jobs

def process_job_stats(jobs):
    """Processes job failure statistics."""
    job_stats = {}

    for job, runs in jobs.items():
        job_stats[job] = {k: {"failures": 0, "other_statuses": {}} for k in TIME_RANGES}

        last_start = runs["last_start"]
        status = runs["status"]

        if last_start == "N/A":
            continue  # Ignore jobs with no valid last start time

        try:
            job_date = datetime.strptime(last_start, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue  # Ignore invalid date formats

        for period, days in TIME_RANGES.items():
            if job_date >= datetime.now() - timedelta(days=days):
                if status in ["FA", "FAILURE"]:  # Failure statuses
                    job_stats[job][period]["failures"] += 1
                else:  # Other statuses
                    job_stats[job][period]["other_statuses"][status] = job_stats[job][period]["other_statuses"].get(status, 0) + 1

    return job_stats

@app.post("/jobs/")
def get_jobs(request: JobPatternsRequest):
    try:
        output = run_autorep(request.job_patterns)
        jobs = parse_autorep_output(output)
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stats/")
def get_job_statistics(request: JobPatternsRequest):
    try:
        output = run_autorep(request.job_patterns, history=True)
        jobs = parse_autorep_output(output)
        job_stats = process_job_stats(jobs)
        return {"job_statistics": job_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))