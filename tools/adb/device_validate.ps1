<#
.SYNOPSIS
    Continuum IDR — Android Device Validation & Automation Suite.
.DESCRIPTION
    Automates Android test device readiness verification, APK installation,
    device hardware & sensor profiling, trip pulling, and diagnostic logcat capture.
.PARAMETER Action
    Target operation: check, info, install, pull, logcat, all. Default is "all".
.PARAMETER ApkPath
    Path to debug APK. Default: "android/app/build/outputs/apk/debug/app-debug.apk".
.PARAMETER OutputDir
    Directory for collected validation artifacts. Default: "artifacts/device_validation".
.PARAMETER DeviceId
    Specific ADB device serial (optional if only one device is connected).
#>

[CmdletBinding()]
param(
    [ValidateSet("check", "info", "install", "pull", "logcat", "all")]
    [string]$Action = "all",

    [string]$ApkPath = "android/app/build/outputs/apk/debug/app-debug.apk",
    [string]$OutputDir = "artifacts/device_validation",
    [string]$PackageName = "ai.continuum.idr",
    [string]$DeviceId = ""
)

$ErrorActionPreference = "Stop"

function Find-Adb {
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        "C:\Android\platform-tools\adb.exe",
        "C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) { return $cand }
    }
    throw "ADB executable not found. Please ensure Android SDK platform-tools is installed and in PATH."
}

$AdbExe = Find-Adb
Write-Host "[Continuum IDR] Using ADB: $AdbExe" -ForegroundColor Cyan

function Invoke-AdbArgs {
    param([string[]]$Arguments)
    if ($DeviceId -ne "") {
        $fullArgs = @("-s", $DeviceId) + $Arguments
    } else {
        $fullArgs = $Arguments
    }
    & $AdbExe $fullArgs
}

function Invoke-AdbOutput {
    param([string[]]$Arguments)
    if ($DeviceId -ne "") {
        $fullArgs = @("-s", $DeviceId) + $Arguments
    } else {
        $fullArgs = $Arguments
    }
    $res = & $AdbExe $fullArgs
    return $res
}

function Test-DeviceConnection {
    Write-Host "`n=== 1. Checking Connected Devices ===" -ForegroundColor Yellow
    $devicesOut = Invoke-AdbOutput @("devices", "-l")
    $deviceLines = $devicesOut | Where-Object { $_ -match "\bdevice\b" -and $_ -notmatch "List of devices" }
    
    if (-not $deviceLines -or $deviceLines.Count -eq 0) {
        Write-Warning "No connected Android devices detected in 'device' state."
        Write-Host "Troubleshooting:"
        Write-Host "  1. Ensure USB Debugging is enabled in Developer Options."
        Write-Host "  2. Accept the 'Allow USB Debugging' authorization prompt on the phone screen."
        Write-Host "  3. Run: adb devices"
        return $false
    }

    Write-Host "Found $($deviceLines.Count) connected device(s):" -ForegroundColor Green
    $deviceLines | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
    return $true
}

function Get-DeviceMetadata {
    Write-Host "`n=== 2. Device Hardware & Sensor Diagnostics ===" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

    $model = (Invoke-AdbOutput @("shell", "getprop", "ro.product.model")).Trim()
    $manufacturer = (Invoke-AdbOutput @("shell", "getprop", "ro.product.manufacturer")).Trim()
    $brand = (Invoke-AdbOutput @("shell", "getprop", "ro.product.brand")).Trim()
    $androidVer = (Invoke-AdbOutput @("shell", "getprop", "ro.build.version.release")).Trim()
    $sdkVer = (Invoke-AdbOutput @("shell", "getprop", "ro.build.version.sdk")).Trim()
    $abi = (Invoke-AdbOutput @("shell", "getprop", "ro.product.cpu.abi")).Trim()

    Write-Host "  Device: $manufacturer $model ($brand)" -ForegroundColor Cyan
    Write-Host "  Android: $androidVer (API $sdkVer), ABI: $abi" -ForegroundColor Cyan

    # Check sensors via dumpsys
    $sensorsRaw = Invoke-AdbOutput @("shell", "dumpsys", "sensorservice")
    $hasGyro = ($sensorsRaw -match "Gyroscope|gyro") -ne $null
    $hasAccel = ($sensorsRaw -match "Accelerometer|accel") -ne $null
    $hasLinear = ($sensorsRaw -match "Linear Acceleration") -ne $null
    $hasGravity = ($sensorsRaw -match "Gravity") -ne $null

    Write-Host "  Sensors: Accel=$hasAccel, Gyro=$hasGyro, LinearAccel=$hasLinear, Gravity=$hasGravity" -ForegroundColor Cyan

    $meta = [PSCustomObject]@{
        timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
        manufacturer = $manufacturer
        model = $model
        brand = $brand
        android_version = $androidVer
        sdk_version = $sdkVer
        cpu_abi = $abi
        sensor_support = [PSCustomObject]@{
            accelerometer = [bool]$hasAccel
            gyroscope = [bool]$hasGyro
            linear_acceleration = [bool]$hasLinear
            gravity = [bool]$hasGravity
        }
    }

    $jsonFile = Join-Path $OutputDir "device_profile.json"
    $meta | ConvertTo-Json -Depth 4 | Set-Content -Path $jsonFile -Encoding UTF8
    Write-Host "  Saved device profile to: $jsonFile" -ForegroundColor Green
}

function Install-AppApk {
    Write-Host "`n=== 3. Installing Continuum IDR APK ===" -ForegroundColor Yellow
    if (-not (Test-Path $ApkPath)) {
        throw "APK not found at '$ApkPath'. Run './gradlew.bat assembleDebug' in android/ first."
    }

    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $ApkPath))
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha256.ComputeHash($fileBytes)
    $hashString = [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
    Write-Host "  APK Size: $([math]::Round($fileBytes.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "  APK SHA-256: $hashString" -ForegroundColor Cyan

    Write-Host "  Executing: adb install -r -g $ApkPath" -ForegroundColor White
    $res = Invoke-AdbOutput @("install", "-r", "-g", $ApkPath)
    Write-Host "  $res" -ForegroundColor Green

    if ($res -notmatch "Success") {
        Write-Warning "APK installation did not report Success. Check device screen for prompts."
    }
}

function Pull-TripLogs {
    Write-Host "`n=== 4. Pulling Field Trip Logs ===" -ForegroundColor Yellow
    $remoteDir = "/sdcard/Android/data/$PackageName/files/trips"
    $localTripsDir = Join-Path $OutputDir "trips"
    New-Item -ItemType Directory -Force -Path $localTripsDir | Out-Null

    Write-Host "  Scanning remote trips at: $remoteDir" -ForegroundColor Cyan
    $listOut = Invoke-AdbOutput @("shell", "ls", "-la", "$remoteDir/*.jsonl")

    Write-Host "  Executing: adb pull $remoteDir/. $localTripsDir" -ForegroundColor White
    $pullRes = Invoke-AdbOutput @("pull", "$remoteDir/.", $localTripsDir)
    Write-Host "  $pullRes" -ForegroundColor Green

    $pulledFiles = Get-ChildItem -Path $localTripsDir -Filter "*.jsonl" -ErrorAction SilentlyContinue
    if ($pulledFiles) {
        Write-Host "  Pulled $($pulledFiles.Count) trip log(s):" -ForegroundColor Green
        foreach ($f in $pulledFiles) {
            Write-Host "    $($f.Name) ($([math]::Round($f.Length / 1KB, 1)) KB)" -ForegroundColor White
        }
    } else {
        Write-Host "  No .jsonl trips currently found in $remoteDir" -ForegroundColor Gray
    }
}

function Capture-DiagnosticLogcat {
    Write-Host "`n=== 5. Capturing Diagnostic Logcat ===" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $logFile = Join-Path $OutputDir "logcat_$stamp.txt"

    Write-Host "  Dumping logcat buffer to: $logFile" -ForegroundColor Cyan
    $logLines = Invoke-AdbOutput @("logcat", "-d", "-v", "time", "*:W", "ContinuumLocationEngine:V", "TrackingService:V", "TrafficBle:V")
    $logLines | Set-Content -Path $logFile -Encoding UTF8
    Write-Host "  Logcat captured ($($logLines.Count) lines)." -ForegroundColor Green
}

# Dispatch
switch ($Action) {
    "check" {
        $ok = Test-DeviceConnection
        if (-not $ok) { exit 1 }
    }
    "info" {
        if (-not (Test-DeviceConnection)) { exit 1 }
        Get-DeviceMetadata
    }
    "install" {
        if (-not (Test-DeviceConnection)) { exit 1 }
        Install-AppApk
    }
    "pull" {
        if (-not (Test-DeviceConnection)) { exit 1 }
        Pull-TripLogs
    }
    "logcat" {
        if (-not (Test-DeviceConnection)) { exit 1 }
        Capture-DiagnosticLogcat
    }
    "all" {
        $connected = Test-DeviceConnection
        if ($connected) {
            Get-DeviceMetadata
            Install-AppApk
            Pull-TripLogs
            Write-Host "`n=== Device Ready for Live Road Testing ===" -ForegroundColor Green
            Write-Host "To record a trip:"
            Write-Host "  1. Open 'Continuum IDR' on device."
            Write-Host "  2. Select vehicle profile (e.g. CAR, MOTORCYCLE) and route category."
            Write-Host "  3. Tap 'Start Trip', drive route through target outage."
            Write-Host "  4. Tap 'Stop Trip' and run './tools/adb/device_validate.ps1 -Action pull' to ingest."
        } else {
            Write-Host "Validation completed in offline / device-disconnected mode." -ForegroundColor Yellow
        }
    }
}
