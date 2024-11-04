SELECT COUNT(*) AS incident_count
FROM your_view_name
WHERE sys_created_on >= DATEADD(year, -1, GETDATE())