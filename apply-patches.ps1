<#
.SYNOPSIS
    Re-applies the taint-reduction patches to WoW retail addons after a CurseForge update.

.DESCRIPTION
    Finds your retail WoW install, then for each patch in ./patches/:
      - Skips it if already applied (detected via git apply --check -R)
      - Applies it if the target file matches the expected "original" state
      - Reports a clear error if the addon has changed in a way that makes the patch stale

    Run this after updating any of the patched addons. Safe to run any time; idempotent.

.NOTES
    Requires `git` in PATH (just for `git apply`). No network access. No elevation required
    unless WoW is installed under Program Files and your user lacks write access to the
    AddOns folder (in which case re-run PowerShell as admin).
#>

param(
    [string]$WoWPath = $null
)

$ErrorActionPreference = 'Stop'

# --- Locate WoW retail install ---------------------------------------------

function Find-WoWRetail {
    $candidates = @(
        "${env:ProgramFiles(x86)}\World of Warcraft\_retail_",
        "${env:ProgramFiles}\World of Warcraft\_retail_",
        "C:\World of Warcraft\_retail_",
        "D:\World of Warcraft\_retail_",
        "D:\Games\World of Warcraft\_retail_",
        "C:\Games\World of Warcraft\_retail_"
    )
    foreach ($c in $candidates) {
        if (Test-Path "$c\Interface\AddOns") { return $c }
    }
    return $null
}

if (-not $WoWPath) { $WoWPath = Find-WoWRetail }
if (-not $WoWPath -or -not (Test-Path "$WoWPath\Interface\AddOns")) {
    Write-Error "Could not find World of Warcraft retail install. Pass -WoWPath explicitly."
}

$addonsDir = Join-Path $WoWPath "Interface\AddOns"
Write-Host "WoW retail AddOns: $addonsDir" -ForegroundColor Cyan

# --- Find patches ----------------------------------------------------------

$patchDir = Join-Path $PSScriptRoot "patches"
if (-not (Test-Path $patchDir)) { Write-Error "No patches/ directory found next to this script." }

$patches = Get-ChildItem -Path $patchDir -Filter "*.patch" | Sort-Object Name
if (-not $patches) { Write-Warning "No .patch files in $patchDir"; return }

# --- Apply each patch ------------------------------------------------------

$applied = 0; $skipped = 0; $failed = 0

foreach ($patch in $patches) {
    # Derive the addon folder name from the patch's diff --git header.
    $firstLine = (Get-Content $patch.FullName -TotalCount 1)
    if ($firstLine -notmatch 'diff --git a/([^/]+)/') {
        Write-Warning "[$($patch.Name)] could not parse addon name from header — skipping"
        continue
    }
    $addonName = $Matches[1]
    $addonPath = Join-Path $addonsDir $addonName

    Write-Host ""
    Write-Host "--- $($patch.Name) → $addonName" -ForegroundColor Yellow

    if (-not (Test-Path $addonPath)) {
        Write-Host "  ! addon not installed — skipping" -ForegroundColor DarkGray
        $skipped++; continue
    }

    # Probe: would reverse-applying succeed? If yes, patch is already in place.
    & git -C $addonsDir apply --check -R $patch.FullName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ already applied (skipping)" -ForegroundColor Green
        $skipped++; continue
    }

    # Probe: does forward-apply work cleanly?
    & git -C $addonsDir apply --check $patch.FullName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ does not apply cleanly — the addon has changed since this patch was written" -ForegroundColor Red
        Write-Host "    You'll need to regenerate the patch against the new version." -ForegroundColor Red
        $failed++; continue
    }

    # Apply it for real.
    & git -C $addonsDir apply $patch.FullName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ applied" -ForegroundColor Green
        $applied++
    } else {
        Write-Host "  ✗ apply failed after check passed (unexpected)" -ForegroundColor Red
        $failed++
    }
}

# --- Summary ---------------------------------------------------------------

Write-Host ""
Write-Host ("Summary: applied={0}  skipped={1}  failed={2}" -f $applied, $skipped, $failed) -ForegroundColor Cyan
if ($failed -gt 0) { exit 1 }
