# Read-only collector.
# Observes startup metadata only; does not disable, delete, execute, or upload.

$registryPaths = @(
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run"
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
    "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
    "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"
)

$startupFolders = @(
    Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
    Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\Startup"
)

$collectedAt = (Get-Date).ToUniversalTime().ToString("o")
$registryItems = $registryPaths | ForEach-Object {
    $registryPath = $_
    if (Test-Path -Path $registryPath) {
        $properties = Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue
        $properties.PSObject.Properties |
            Where-Object { $_.Name -notmatch "^PS" } |
            ForEach-Object {
                [PSCustomObject][ordered]@{
                    item_id              = $null
                    name                 = [string]$_.Name
                    command              = if ($null -eq $_.Value) { $null } else { [string]$_.Value }
                    location_type        = "registry_run"
                    registry_path        = $registryPath
                    registry_value_name  = [string]$_.Name
                    startup_folder_path  = $null
                    file_path            = $null
                    publisher            = $null
                    enabled_state        = "observed"
                    source               = "windows_registry_run"
                    collected_at         = $collectedAt
                }
            }
    }
}

$folderItems = $startupFolders | ForEach-Object {
    $startupFolder = $_
    if (Test-Path -Path $startupFolder) {
        Get-ChildItem -Path $startupFolder -File -ErrorAction SilentlyContinue |
            ForEach-Object {
                [PSCustomObject][ordered]@{
                    item_id              = $null
                    name                 = [string]$_.BaseName
                    command              = $null
                    location_type        = "startup_folder"
                    registry_path        = $null
                    registry_value_name  = $null
                    startup_folder_path  = $startupFolder
                    file_path            = [string]$_.FullName
                    publisher            = $null
                    enabled_state        = "observed"
                    source               = "windows_startup_folder"
                    collected_at         = $collectedAt
                }
            }
    }
}

Write-Output (ConvertTo-Json -InputObject @($registryItems + $folderItems) -Depth 4 -Compress)
