from fastapi import FastAPI
from pydantic import BaseModel
from job_parser import get_matching_jobs, get_job_history

app = FastAPI()

class JobPatternRequest(BaseModel):
    job_pattern: str
    months: list

@app.post("/job-patterns")
def get_jobs_by_pattern(data: JobPatternRequest):
    """Fetch all jobs matching a pattern and their failure history."""
    matching_jobs = get_matching_jobs(data.job_pattern)
    
    if not matching_jobs:
        return {"error": "No matching jobs found"}

    summary = []
    for job in matching_jobs:
        history = get_job_history(job)
        failures = sum(1 for entry in history if entry["status"] == "FA")
        summary.append({"job": job, "failures": failures})

    return summary