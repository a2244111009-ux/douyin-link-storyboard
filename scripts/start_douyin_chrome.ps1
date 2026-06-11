param(
  [int]$Port = 9222,
  [string]$ProfileDir = "E:\CodexBrowserProfiles\douyin",
  [string]$Url = "https://www.douyin.com/"
)

$ErrorActionPreference = "Stop"

$candidates = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
  "$env:LocalAppData\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe"
)

$browser = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) {
  throw "Chrome/Edge executable not found."
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

Start-Process -FilePath $browser -ArgumentList @(
  "--remote-debugging-port=$Port",
  "--remote-allow-origins=*",
  "--user-data-dir=$ProfileDir",
  "--new-window",
  "--no-first-run",
  "--disable-default-apps",
  $Url
)

Write-Output "Started browser on CDP port $Port with profile $ProfileDir"
