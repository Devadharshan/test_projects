from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from job_parser.py import get_job_history
import pandas as pd

app = FastAPI()

class JobRequest(BaseModel):
    jobs: list
    months: list

@app.get("/jobs")
def get_jobs():
    """Mock job names list."""
    return ["JobA", "JobB", "JobC", "JobD"]

@app.get("/months")
def get_months():
    """Mock month list."""
    return ["Last 3 Months", "Last 2 Months", "Last Month", "Last Week", "This Week"]

@app.post("/summary")
def get_summary(data: JobRequest):
    """Fetch failure summary for selected jobs and months."""
    summary = []
    
    for job in data.jobs:
        history = get_job_history(job)
        failures = sum(1 for entry in history if entry["status"] == "FA")
        summary.append({"job": job, "failures": failures})
    
    return summary

@app.post("/job-stats")
def get_job_stats(data: JobRequest):
    """Fetch job success/failure history."""
    job_data = []
    
    for job in data.jobs:
        history = get_job_history(job)
        failures = sum(1 for entry in history if entry["status"] == "FA")
        job_data.append({"job": job, "failures": failures})
    
    return job_data