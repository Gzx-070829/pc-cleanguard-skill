# Shared Windows PowerShell 5.1 / PowerShell 7 helpers for local JSON artifacts.

Set-StrictMode -Version 2.0

function Write-PcgUtf8Json {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [AllowNull()]
        [object]$Value,

        [int]$Depth = 10
    )

    $json = ConvertTo-Json -InputObject $Value -Depth $Depth -Compress
    if ($null -eq $json) {
        $json = "null"
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText(
        $Path,
        ([string]$json + [Environment]::NewLine),
        $utf8NoBom
    )
}

function Get-PcgPowerShellMetadata {
    $edition = "Desktop"
    if ($null -ne (Get-Variable -Name PSEdition -ErrorAction SilentlyContinue)) {
        $edition = [string]$PSVersionTable.PSEdition
    }
    return [PSCustomObject][ordered]@{
        version = [string]$PSVersionTable.PSVersion
        edition = $edition
        process_architecture = [string][Environment]::Is64BitProcess
    }
}

function Get-PcgUtcTimestamp {
    return (Get-Date).ToUniversalTime().ToString("o")
}

function Assert-PcgExplicitLocalPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [string]$Purpose = "output"
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "$Purpose path must be explicit and non-empty"
    }
    if ($Path.StartsWith("\\")) {
        throw "$Purpose path must not be UNC or network-backed"
    }
    return [System.IO.Path]::GetFullPath($Path)
}
