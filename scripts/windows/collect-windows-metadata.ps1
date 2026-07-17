param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

# This script only orchestrates existing read-only metadata collectors.
# Collected command, service path, and task action values remain inert metadata.

Set-StrictMode -Version 2.0
. (Join-Path $PSScriptRoot "collector-compat.ps1")

$destination = Assert-PcgExplicitLocalPath -Path $OutputDirectory -Purpose "collector output"
if ([System.IO.Directory]::Exists($destination)) {
    if ([System.IO.Directory]::GetFileSystemEntries($destination).Count -ne 0) {
        throw "collector output directory must be new or empty"
    }
}
else {
    [void][System.IO.Directory]::CreateDirectory($destination)
}

$definitions = @(
    [PSCustomObject][ordered]@{
        name = "installed_apps"
        script = "collect_installed_apps.ps1"
        output = "installed_apps.json"
        required_command = "Get-ItemProperty"
    }
    [PSCustomObject][ordered]@{
        name = "startup_items"
        script = "collect_startup_items.ps1"
        output = "startup_items.json"
        required_command = "Get-ItemProperty"
    }
    [PSCustomObject][ordered]@{
        name = "services"
        script = "collect_services.ps1"
        output = "services.json"
        required_command = "Get-CimInstance"
    }
    [PSCustomObject][ordered]@{
        name = "scheduled_tasks"
        script = "collect_scheduled_tasks.ps1"
        output = "scheduled_tasks.json"
        required_command = "Get-ScheduledTask"
    }
)

$collectorStatus = [ordered]@{}
$collectorErrors = New-Object System.Collections.ArrayList

foreach ($definition in $definitions) {
    $outputPath = Join-Path $destination $definition.output
    $scriptPath = Join-Path $PSScriptRoot $definition.script
    $status = "success"
    $errorCode = $null
    $message = $null
    $records = @()

    if ($null -eq (Get-Command $definition.required_command -ErrorAction SilentlyContinue)) {
        $status = "unsupported"
        $errorCode = "cmdlet_unavailable"
        $message = "$($definition.required_command) is unavailable in this PowerShell host"
    }
    elseif (-not [System.IO.File]::Exists($scriptPath)) {
        $status = "failed"
        $errorCode = "collector_script_missing"
        $message = "collector script is missing"
    }
    else {
        try {
            $rawOutput = @(& {
                param($collectorScript)
                Set-StrictMode -Off
                & $collectorScript
            } $scriptPath)
            if (-not $?) {
                throw "collector returned an unsuccessful status"
            }
            $jsonText = [string]::Join([Environment]::NewLine, [string[]]$rawOutput)
            if (-not [string]::IsNullOrWhiteSpace($jsonText)) {
                $parsed = ConvertFrom-Json -InputObject $jsonText -ErrorAction Stop
                $records = @($parsed)
            }
        }
        catch {
            $status = "failed"
            $errorCode = "collector_failed"
            $message = [string]$_.Exception.Message
            $records = @()
        }
    }

    Write-PcgUtf8Json -Path $outputPath -Value $records
    $statusRecord = [ordered]@{
        status = $status
        file = $definition.output
        record_count = [int]$records.Count
    }
    if ($null -ne $errorCode) {
        $statusRecord.error_code = $errorCode
        $statusRecord.message = $message
        [void]$collectorErrors.Add([PSCustomObject][ordered]@{
            collector = $definition.name
            error_code = $errorCode
            message = $message
        })
    }
    $collectorStatus[$definition.name] = [PSCustomObject]$statusRecord
}

$manifest = [PSCustomObject][ordered]@{
    schema_version = "0.4.1"
    source_kind = "windows_powershell_collector"
    generated_at = Get-PcgUtcTimestamp
    powershell = Get-PcgPowerShellMetadata
    execution_policy_bypass_scope = "process_only_when_supplied_by_caller"
    collectors = [PSCustomObject]$collectorStatus
    system_modified = $false
    runtime_network_access = $false
}

Write-PcgUtf8Json -Path (Join-Path $destination "collector_errors.json") -Value @($collectorErrors)
Write-PcgUtf8Json -Path (Join-Path $destination "collector_manifest.json") -Value $manifest

[PSCustomObject][ordered]@{
    output_directory = $destination
    collector_manifest = (Join-Path $destination "collector_manifest.json")
    collector_errors = (Join-Path $destination "collector_errors.json")
    system_modified = $false
    runtime_network_access = $false
} | ConvertTo-Json -Depth 4 -Compress
