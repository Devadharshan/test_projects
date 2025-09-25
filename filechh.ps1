# Folders to scan (customize these!)
$scanPaths = @(
    "C:\Users",
    "C:\Windows\Temp",
    "C:\ProgramData",
    "D:\Backups",
    "D:\Logs"
)

# Threshold (1GB)
$threshold = 1GB  

# Output file for Prometheus textfile collector
$outputFile = "C:\Program Files\windows_exporter\textfile\large_files_full.prom"

$metrics = @()

foreach ($path in $scanPaths) {
    if (Test-Path $path) {
        # Top 10 files > 1GB (deep scan inside path)
        Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -gt $threshold } |
        Sort-Object Length -Descending |
        Select-Object -First 10 |
        ForEach-Object {
            $safeName = ($_.FullName -replace "[:\\]", "_")
            $metrics += "windows_large_file_size_bytes{path=`"$path`",file=`"$($_.FullName)`"} $($_.Length)"
        }

        # Directory totals
        Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
        Group-Object { $_.DirectoryName } |
        ForEach-Object {
            $dir = $_.Name
            $total = ($_.Group | Measure-Object Length -Sum).Sum
            if ($total -gt 0) {
                $safeDir = ($dir -replace "[:\\]", "_")
                $metrics += "windows_directory_total_size_bytes{path=`"$path`",directory=`"$dir`"} $total"
            }
        }
    }
}

# Write metrics
$metrics | Out-File -Encoding ascii $outputFile