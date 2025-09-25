# Directories to scan
$scanPaths = @("C:\", "D:\")  

# Threshold (1 GB in bytes)
$threshold = 1GB  

# Output file for Prometheus textfile collector
$outputFile = "C:\Program Files\windows_exporter\textfile\large_files.prom"

# Collect metrics
$metrics = @()

# ---- Per-file metrics (files > threshold) ----
foreach ($path in $scanPaths) {
    Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt $threshold } |
    ForEach-Object {
        $safeName = ($_.FullName -replace "[:\\]", "_") # sanitize
        $metrics += "windows_large_file_size_bytes{file=`"$($_.FullName)`"} $($_.Length)"
    }
}

# ---- Directory-level aggregation ----
foreach ($path in $scanPaths) {
    Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
    Group-Object { $_.DirectoryName } |
    ForEach-Object {
        $dir = $_.Name
        $total = ($_.Group | Measure-Object Length -Sum).Sum
        if ($total -gt 0) {
            $safeDir = ($dir -replace "[:\\]", "_")
            $metrics += "windows_directory_total_size_bytes{directory=`"$dir`"} $total"
        }
    }
}

# Write all metrics
$metrics | Out-File -Encoding ascii $outputFile