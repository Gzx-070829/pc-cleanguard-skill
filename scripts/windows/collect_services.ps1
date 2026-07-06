# Read-only collector.
# Observes service metadata only; does not start, stop, disable, modify, or upload.

$collectedAt = (Get-Date).ToUniversalTime().ToString("o")
$services = Get-CimInstance -ClassName Win32_Service -ErrorAction SilentlyContinue |
    ForEach-Object {
        [PSCustomObject][ordered]@{
            service_name = if ($null -eq $_.Name) { $null } else { [string]$_.Name }
            display_name = if ($null -eq $_.DisplayName) { $null } else { [string]$_.DisplayName }
            status       = if ($null -eq $_.Status) { $null } else { [string]$_.Status }
            start_type   = if ($null -eq $_.StartMode) { $null } else { [string]$_.StartMode }
            state        = if ($null -eq $_.State) { $null } else { [string]$_.State }
            path_name    = if ($null -eq $_.PathName) { $null } else { [string]$_.PathName }
            process_id   = if ($null -eq $_.ProcessId) { $null } else { $_.ProcessId }
            service_type = if ($null -eq $_.ServiceType) { $null } else { [string]$_.ServiceType }
            start_name   = if ($null -eq $_.StartName) { $null } else { [string]$_.StartName }
            description  = if ($null -eq $_.Description) { $null } else { [string]$_.Description }
            source       = "windows_cim_service"
            collected_at = $collectedAt
        }
    }

Write-Output (ConvertTo-Json -InputObject @($services) -Depth 4 -Compress)
