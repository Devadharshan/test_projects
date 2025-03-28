import os
import subprocess
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# Initialize FastAPI
app = FastAPI()

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load the Job Scheduler module once (avoids redundant loading)
os.system("module load jobsched/QNA")


class JobRequest(BaseModel):
    job_patterns: List[str]


def run_autorep_command(command: str) -> List[str]:
    """Run autorep command and return output lines."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode != 0:
            logging.error(f"❌ Error running command: {command}\n{result.stderr}")
            raise HTTPException(status_code=500, detail="Autorep command failed.")
        return result.stdout.split("\n")
    except Exception as e:
        logging.error(f"❌ Exception running autorep: {str(e)}")
        raise HTTPException(status_code=500, detail="Error executing autorep command.")


def parse_autorep_output(output: List[str]) -> Dict[str, Dict]:
    """Parse autorep output and handle missing fields gracefully."""
    jobs = {}

    for line in output:
        parts = line.split()

        if len(parts) < 6:  # Skip invalid lines
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


@app.post("/get_jobs/")
def get_matching_jobs(request: JobRequest):
    """Fetch job details for multiple patterns."""
    job_patterns = request.job_patterns

    if not job_patterns:
        logging.warning("⚠️ Received empty job_patterns list!")
        raise HTTPException(status_code=400, detail="Job patterns cannot be empty.")

    logging.info(f"🔍 Fetching jobs for patterns: {job_patterns}")

    jobs = {}
    for pattern in job_patterns:
        command = f"autorep -J \"{pattern}\""
        output = run_autorep_command(command)
        parsed_jobs = parse_autorep_output(output)
        jobs.update(parsed_jobs)

    if not jobs:
        logging.warning("⚠️ No jobs found for given patterns!")
        return {"message": "No matching jobs found."}

    logging.info(f"✅ Found {len(jobs)} jobs matching patterns.")
    return jobs