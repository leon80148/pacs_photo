param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

$pythonExe = "python"
$pythonArgs = @()
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    $pythonExe = "py"
    $pythonArgs = @("-3.11")
}

if (-not (Get-Command $pythonExe -ErrorAction SilentlyContinue)) {
    $venvPython = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
    if (Test-Path $venvPython) {
        $pythonExe = $venvPython
        $pythonArgs = @()
    }
}

$buildVenv = Join-Path $repoRoot ".build-venv"
if (-not (Test-Path $buildVenv)) {
    & $pythonExe @pythonArgs -m venv $buildVenv
}
$pythonExe = Join-Path $buildVenv "Scripts\\python.exe"
$pythonArgs = @()

& $pythonExe @pythonArgs -m pip install --upgrade pip
& $pythonExe @pythonArgs -m pip install ".[packaging]"

$pyArgs = @(
    "--noconfirm",
    "--clean",
    "--name", "PhotoPacs",
    "--add-data", "web;web",
    "--add-data", "config.ini.example;config.ini",
    "--hidden-import", "photo_pacs.main",
    "--exclude-module", "pkg_resources",
    "src\photo_pacs\cli.py"
)

if ($OneFile) {
    $pyArgs += "--onefile"
} else {
    $pyArgs += "--onedir"
}

& $pythonExe @pythonArgs -m PyInstaller @pyArgs

$releaseDir = Join-Path $repoRoot "release"
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

$defaultAppDir = Join-Path $releaseDir "PhotoPacs"
$defaultZip = Join-Path $releaseDir "PhotoPacs-win64.zip"
$useDefault = $true

try {
    if (Test-Path $defaultAppDir) {
        Remove-Item -Recurse -Force $defaultAppDir
    }
} catch {
    $useDefault = $false
}

if ($OneFile) {
    if (-not $useDefault) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $defaultZip = Join-Path $releaseDir "PhotoPacs-win64-$stamp.zip"
    }
    Copy-Item "dist\PhotoPacs.exe" $releaseDir -Force
    Copy-Item "config.ini.example" (Join-Path $releaseDir "config.ini") -Force
    $zipSource = @(
        Join-Path $releaseDir "PhotoPacs.exe",
        Join-Path $releaseDir "config.ini"
    )
} else {
    $appDir = $defaultAppDir
    if (-not $useDefault) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $appDir = Join-Path $releaseDir "PhotoPacs-$stamp"
        $defaultZip = Join-Path $releaseDir "PhotoPacs-win64-$stamp.zip"
    }
    Copy-Item -Recurse "dist\PhotoPacs" $appDir -Force
    Copy-Item "config.ini.example" (Join-Path $appDir "config.ini") -Force
    $zipSource = $appDir
}

Compress-Archive -Path $zipSource -DestinationPath $defaultZip -Force

Write-Host "Release created: $defaultZip"
