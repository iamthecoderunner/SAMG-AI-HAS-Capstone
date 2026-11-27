$ErrorActionPreference = 'Stop'
Write-Host 'AI-HAS - publish the SOURCE CODE only (not a live hosted application)' -ForegroundColor Cyan
if (-not (Test-Path 'app\main.py') -or -not (Test-Path '.gitignore')) { throw 'Run this helper from the clean extracted AI-HAS folder containing app\main.py and .gitignore.' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is not installed. Install Git for Windows, then run again.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI (gh) is not installed. Install it and reopen PowerShell.' }
& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'GitHub is not authorized. Run gh auth login yourself and retry.' }
$forbidden = @('.env','aihas.db','chroma','venv','.venv')
Write-Host 'Readiness: the file tree may contain private runtime files; only .gitignore-approved source files should be committed.'
$answer = Read-Host 'Make the AI-HAS SOURCE CODE public on GitHub? Type PUBLISH to continue'
if ($answer -cne 'PUBLISH') { Write-Host 'Cancelled. Nothing published.'; exit 0 }
if (-not (Test-Path '.git')) { & git init; if ($LASTEXITCODE -ne 0) { throw 'git init failed.' } }
& git add .
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
$staged = @(& git diff --cached --name-only)
foreach ($f in $staged) {
  $norm = ($f -replace '\\','/').ToLowerInvariant()
  if ($norm -eq '.env' -or $norm -match '(^|/)aihas\.db$' -or $norm -match '(^|/)chroma/' -or $norm -match '(^|/)\.venv/' -or $norm -match '(^|/)venv/' -or $norm -match '(^|/)local_ai_verification\.json$') { throw "PRIVATE FILE STAGED: $f - Aborting. Remove it from staging before retrying." }
}
if ($staged.Count -eq 0 -and -not (Test-Path '.git/HEAD')) { throw 'No project files staged.' }
& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  & git commit -m 'AI-HAS capstone v12 - source and documentation'
  if ($LASTEXITCODE -ne 0) { throw 'Git commit failed. Configure your git user.name/email as prompted and retry.' }
}
$remote = (& git remote get-url origin 2>$null)
if ($LASTEXITCODE -eq 0 -and $remote) { throw "An origin remote already exists: $remote . Review it manually; this helper will not overwrite it." }
& gh repo create AI-HAS-Capstone --public --source . --remote origin --push
if ($LASTEXITCODE -ne 0) { throw 'GitHub publish failed (possible existing repository or branch issue). Nothing is claimed as published.' }
$url = (& gh repo view --json url --jq '.url')
if ($LASTEXITCODE -ne 0 -or -not $url) { throw 'Repository may exist, but its URL could not be verified. Inspect your GitHub account.' }
Write-Host "VERIFIED SOURCE REPOSITORY URL: $url" -ForegroundColor Green
Write-Host 'This is a SOURCE link, not a public running AI-HAS website. Verify it in a private browser window.'
