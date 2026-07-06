# Read-only collector.
# Observes scheduled task metadata only; does not run, disable, modify, or upload.

$collectedAt = (Get-Date).ToUniversalTime().ToString("o")
$tasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
    ForEach-Object {
        $actionsSummary = ConvertTo-Json -InputObject @(
            $_.Actions | Select-Object Execute, Arguments, WorkingDirectory
        ) -Depth 3 -Compress
        $triggersSummary = ConvertTo-Json -InputObject @(
            $_.Triggers | Select-Object StartBoundary, EndBoundary, Enabled
        ) -Depth 3 -Compress
        [PSCustomObject][ordered]@{
            task_name         = if ($null -eq $_.TaskName) { $null } else { [string]$_.TaskName }
            task_path         = if ($null -eq $_.TaskPath) { $null } else { [string]$_.TaskPath }
            state             = if ($null -eq $_.State) { $null } else { [string]$_.State }
            author            = if ($null -eq $_.Author) { $null } else { [string]$_.Author }
            description       = if ($null -eq $_.Description) { $null } else { [string]$_.Description }
            uri               = if ($null -eq $_.URI) { $null } else { [string]$_.URI }
            actions_summary   = $actionsSummary
            triggers_summary  = $triggersSummary
            principal_user_id = if ($null -eq $_.Principal.UserId) { $null } else { [string]$_.Principal.UserId }
            run_level         = if ($null -eq $_.Principal.RunLevel) { $null } else { [string]$_.Principal.RunLevel }
            source            = "windows_scheduled_task"
            collected_at      = $collectedAt
        }
    }

Write-Output (ConvertTo-Json -InputObject @($tasks) -Depth 5 -Compress)
