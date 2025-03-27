import subprocess
import pandas as pd

def get_job_history(job_name):
    """Runs autorep command and fetches job history for the given job name."""
    try:
        result = subprocess.run(
            ["autorep", "-J", job_name, "-r"],
            capture_output=True,
            text=True,
            check=True
        )
        output_lines = result.stdout.splitlines()
        
        history = []
        for line in output_lines:
            parts = line.split()
            if len(parts) >= 3 and parts[1] in ["SU", "FA"]:
                history.append({"date": parts[0], "status": parts[1]})
        
        return history

    except subprocess.CalledProcessError as e:
        print(f"Error running autorep: {e}")
        return []