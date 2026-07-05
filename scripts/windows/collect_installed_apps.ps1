# Read-only collector.
# Does not uninstall, delete, modify registry, disable services, or upload data.

$registryPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$collectedAt = (Get-Date).ToUniversalTime().ToString("o")
$items = $registryPaths | ForEach-Object {
    $registryPath = $_
    Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue |
        Where-Object { $null -ne $_.DisplayName -and $_.DisplayName.ToString().Trim() } |
        ForEach-Object {
            [PSCustomObject][ordered]@{
                name                   = if ($null -eq $_.DisplayName) { $null } else { [string]$_.DisplayName }
                publisher              = if ($null -eq $_.Publisher) { $null } else { [string]$_.Publisher }
                version                = if ($null -eq $_.DisplayVersion) { $null } else { [string]$_.DisplayVersion }
                install_location       = if ($null -eq $_.InstallLocation) { $null } else { [string]$_.InstallLocation }
                install_date           = if ($null -eq $_.InstallDate) { $null } else { [string]$_.InstallDate }
                uninstall_string       = if ($null -eq $_.UninstallString) { $null } else { [string]$_.UninstallString }
                quiet_uninstall_string = if ($null -eq $_.QuietUninstallString) { $null } else { [string]$_.QuietUninstallString }
                registry_source        = $registryPath.TrimEnd("*").TrimEnd("\")
                registry_key           = if ($null -eq $_.PSPath) { $null } else { [string]$_.PSPath }
                display_icon           = if ($null -eq $_.DisplayIcon) { $null } else { [string]$_.DisplayIcon }
                estimated_size_kb      = if ($null -eq $_.EstimatedSize) { $null } else { $_.EstimatedSize }
                system_component       = if ($null -eq $_.SystemComponent) { $null } else { $_.SystemComponent }
                windows_installer      = if ($null -eq $_.WindowsInstaller) { $null } else { $_.WindowsInstaller }
                no_remove              = if ($null -eq $_.NoRemove) { $null } else { $_.NoRemove }
                no_modify              = if ($null -eq $_.NoModify) { $null } else { $_.NoModify }
                source                 = "windows_registry_uninstall"
                collected_at           = $collectedAt
            }
        }
}

Write-Output (ConvertTo-Json -InputObject @($items) -Depth 4 -Compress)
