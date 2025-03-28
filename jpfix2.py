def get_matching_jobs(job_patterns):
    """Fetch all job names matching patterns in ONE batch command."""
    jobs = {}

    # 🔹 Convert single string input to a list
    if isinstance(job_patterns, str):
        job_patterns = [job_patterns]

    if not job_patterns or not isinstance(job_patterns, list):  
        print("⚠️ WARNING: job_patterns is empty or invalid!")
        return jobs

    print(f"✅ Processing job patterns: {job_patterns}")  # Debug print

    # 🔹 Combine job patterns into one command
    pattern_str = ",".join([f'"{pattern}"' for pattern in job_patterns])  # Ensure proper escaping
    command = f"autorep -J {pattern_str}"

    result = run_autorep_command(command)

    for line in result:
        parts = line.split()
        if parts:
            job_name = parts[0]
            # 🔹 Assign correct pattern (match the pattern that fetched this job)
            matched_pattern = next((p for p in job_patterns if job_name.startswith(p.rstrip("%"))), "Unknown")
            jobs[job_name] = {"pattern": matched_pattern}

    return jobs