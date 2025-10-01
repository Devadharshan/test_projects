# Folder to scan
$ScanFolder = "C:\data"

# Windows Exporter textfile directory
$TextfileDir = "C:\custom_metrics"

# Output file
$PromFile = Join-Path $TextfileDir "large_files.prom"

# Minimum size in bytes (5 GB)
$MinSize = 5GB

# Get all files larger than 5 GB recursively
$Files = Get-ChildItem -Path $ScanFolder -File -Recurse | Where-Object { $_.Length -gt $MinSize }

# Prepare Prometheus metrics lines
$Lines = @()
$Lines += "# HELP custom_file_size_bytes File size in bytes"
$Lines += "# TYPE custom_file_size_bytes gauge"

foreach ($file in $Files) {
    # Escape backslashes
    $EscapedPath = $file.FullName -replace '\\', '\\\\'
    $Lines += "custom_file_size_bytes{filename=`"$EscapedPath`"} $($file.Length)"
}

# Write to .prom file
$Lines -join "`n" | Out-File $PromFile -Encoding ascii

Write-Output "Prometheus file generated at $PromFile"