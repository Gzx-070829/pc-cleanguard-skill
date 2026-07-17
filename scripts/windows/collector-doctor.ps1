param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

# Doctor performs capability checks only. A caller-supplied process-level
# ExecutionPolicy Bypass does not modify user or machine policy or the registry.

Set-StrictMode -Version 2.0
. (Join-Path $PSScriptRoot "collector-compat.ps1")

$destination = Assert-PcgExplicitLocalPath -Path $OutputPath -Purpose "doctor output"
$parent = [System.IO.Path]::GetDirectoryName($destination)
if (-not [string]::IsNullOrWhiteSpace($parent)) {
    [void][System.IO.Directory]::CreateDirectory($parent)
}

$commands = [ordered]@{}
foreach ($commandName in @(
    "Get-ItemProperty",
    "Get-CimInstance",
    "Get-ScheduledTask",
    "Get-ScheduledTaskInfo",
    "Get-ChildItem",
    "ConvertTo-Json"
)) {
    $commands[$commandName] = ($null -ne (Get-Command $commandName -ErrorAction SilentlyContinue))
}

$scripts = [ordered]@{}
foreach ($scriptName in @(
    "collect_installed_apps.ps1",
    "collect_startup_items.ps1",
    "collect_services.ps1",
    "collect_scheduled_tasks.ps1"
)) {
    $scripts[$scriptName] = [System.IO.File]::Exists((Join-Path $PSScriptRoot $scriptName))
}

$doctor = [PSCustomObject][ordered]@{
    schema_version = "0.4.1"
    checked_at = Get-PcgUtcTimestamp
    powershell = Get-PcgPowerShellMetadata
    commands = [PSCustomObject]$commands
    collector_scripts = [PSCustomObject]$scripts
    scheduled_tasks_status = $(if ($commands["Get-ScheduledTask"]) { "supported" } else { "unsupported" })
    execution_policy = [PSCustomObject][ordered]@{
        effective = [string](Get-ExecutionPolicy)
        process = [string](Get-ExecutionPolicy -Scope Process)
        bypass_scope = "process_only_when_supplied_by_caller"
        policy_modified = $false
    }
    utf8_no_bom_output = $true
    system_modified = $false
    runtime_network_access = $false
}

Write-PcgUtf8Json -Path $destination -Value $doctor
[PSCustomObject][ordered]@{
    output = $destination
    compatible = $true
    scheduled_tasks_status = $doctor.scheduled_tasks_status
    system_modified = $false
} | ConvertTo-Json -Depth 4 -Compress
