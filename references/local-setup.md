# Local Setup

## Required Local Components

- `jiji262/douyin-downloader` cloned locally.
- Valid Douyin browser login state exported to `douyin-downloader/config/cookies.json`.
- Python environment for `douyin-downloader`.
- `ffmpeg` and `ffprobe` available on PATH.
- `openai-whisper` installed in the downloader Python environment.
- Optional `OpenCC` for simplified Chinese conversion.

## E Drive Defaults

Use E drive for large files:

```powershell
$env:XDG_CACHE_HOME = "E:\AIModels"
```

Whisper model files will live under:

```text
E:\AIModels\whisper
```

Suggested run outputs:

```text
E:\DouyinRuns\<account-or-date>
```

## Cookie Workflow

Start Chrome:

```powershell
E:\CodexSkills\douyin-link-storyboard\scripts\start_douyin_chrome.ps1
```

Ask the user to complete Douyin login. Then export cookies:

```powershell
python E:\CodexSkills\douyin-link-storyboard\scripts\export_douyin_cookies.py --downloader-root "C:\path\to\douyin-downloader"
```

Do not print cookie values.

## Common Fixes

If `openai-whisper` is missing:

```powershell
.\.venv\Scripts\python.exe -m pip install openai-whisper OpenCC
```

If `playwright` is missing for cookie export:

```powershell
python -m pip install playwright
```

If Douyin returns empty 200 responses, refresh cookies by scan-login. Do not attempt to bypass CAPTCHA or platform protections.
