param(
    [string]$Config = ""
)

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
chcp 65001 | Out-Null
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$cli = Join-Path $root "tools\cli.py"

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python launcher not found. Please install py.exe or python.exe on Windows."
}

$pythonCmd = Resolve-PythonCommand

if (-not $Config -and $args.Count -eq 0) {
    $resolved = & $pythonCmd[0] $cli resolve-active-workspace --print-path
    if ($LASTEXITCODE -ne 0 -or -not $resolved) {
        throw "Failed to resolve active workspace config."
    }
    $Config = ($resolved | Select-Object -Last 1).Trim()
}

$forward = @()
if ($Config) {
    $forward += "--config"
    $forward += $Config
}
$forward += $args

& $pythonCmd[0] $cli postprocess @forward
exit $LASTEXITCODE
