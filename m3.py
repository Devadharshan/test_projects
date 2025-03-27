from fastapi import FastAPI
from pydantic import BaseModel
from job_parser import get_matching_jobs, analyze_job_failures

app = FastAPI()

class JobPatternRequest(BaseModel):
    job_patterns: list

@app.post("/job-failures")
def get_failures(data: JobPatternRequest):
    """Fetch all jobs matching patterns and show failure stats."""
    matching_jobs = get_matching_jobs(data.job_patterns)
    
    if not matching_jobs:
        return {"error": "No matching jobs found"}

    stats = analyze_job_failures(matching_jobs)
    return stats