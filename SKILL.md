---
name: douyin-link-storyboard
description: Extract complete spoken copy, copy-writing structure, and screenshot/timecode storyboards from a Douyin profile or video link using a free local workflow. Use when the user provides a Douyin short link, profile link, or video link and asks to抓取对标账号, 提取视频文案, 拆文案结构, 还原分镜表, 抽截图时间轴, or prepare JSONL outputs for a backend knowledge base.
---

# Douyin Link Storyboard

Use this skill to turn a Douyin profile/video link into reusable creative research artifacts:

```text
Douyin link -> video files -> full spoken copy -> copy structure -> screenshots/timecodes -> storyboard table
```

Work only with the user's own browser login state or cookies. Do not attempt to bypass platform protections, CAPTCHA, account gates, or rate limits. If anonymous requests fail, ask the user to scan-login once and reuse the local cookie file.

## Local Defaults

- Skill path: `E:\CodexSkills\douyin-link-storyboard`
- Whisper model cache: `E:\AIModels`
- Suggested run output root: `E:\DouyinRuns`
- Preferred crawler/downloader repo: `douyin-downloader`, usually at `...\work\douyin-downloader`

## Quick Workflow

1. Resolve the link type.
   - Profile links and `v.douyin.com` profile shares should run account mode.
   - Single video links should run single-video mode.
2. Ensure login state exists.
   - If `downloader-root\config\cookies.json` exists and has required Douyin cookies, continue.
   - Otherwise run `scripts/start_douyin_chrome.ps1`, ask the user to scan-login, then run `scripts/export_douyin_cookies.py`.
3. Run `scripts/douyin_storyboard_pipeline.py`.
   - Use a small limit first, usually `--limit 3`.
   - Use `--model small` for normal Chinese product口播.
4. Inspect contact sheets with `view_image`.
5. Produce final deliverables:
   - Complete copy only
   - Copy structure
   - Storyboard table
   - JSONL files for backend ingestion

## Main Command

From any workspace, run:

```powershell
python E:\CodexSkills\douyin-link-storyboard\scripts\douyin_storyboard_pipeline.py `
  --url "https://v.douyin.com/..." `
  --downloader-root "C:\path\to\work\douyin-downloader" `
  --out "E:\DouyinRuns\sample-run" `
  --limit 3 `
  --model small
```

The script creates:

```text
downloaded/                  # mp4, data.json, comments.json
transcripts/                 # .txt and .srt
storyboard/                  # frames, contact sheets
artifacts/transcripts.jsonl  # raw ASR transcript rows
artifacts/timeline-draft.jsonl
artifacts/frame-summary.json
```

## Login Helpers

Start a visible Chrome session for scan-login:

```powershell
E:\CodexSkills\douyin-link-storyboard\scripts\start_douyin_chrome.ps1
```

After the user says login is complete, export cookies:

```powershell
python E:\CodexSkills\douyin-link-storyboard\scripts\export_douyin_cookies.py `
  --downloader-root "C:\path\to\work\douyin-downloader"
```

Never print cookie values. Only report cookie count and whether required keys exist.

## Output Rules

When the user says “先提取完整文案”, only output complete spoken copy. Do not summarize, infer problems, or拆结构.

When the user asks “拆分组合/怎么写文案”, output:

```text
opening_type
opening
process_steps
ending_type
ending
core_formula
reusable_template
```

When the user asks for “截图/时间轴/分镜表”, output:

```text
time_range
frame_path
visual
voiceover
shot_purpose
```

Use screenshots as evidence. Do not invent visual details that are not visible.

## Copy Cleaning

Keep both raw ASR and cleaned copy when possible.

Correct obvious ASR errors only when supported by product title, metadata, subtitles, or repeated context. Common product-video corrections:

```text
下凉贝/下凉杯 -> 夏凉被
备套 -> 被套
贴身水/贴时 -> 贴身睡
裸碎 -> 裸睡
排施 -> 排湿
机器/机系 -> 机洗
冰杆灭料/冰感灭料 -> 冰感面料
```

If uncertain, mark `needs_review: true` in JSONL or mention that the line needs manual confirmation.

## Storyboard Method

Default to rough storyboard:

```text
sample one frame every 2 seconds
read SRT timecodes
align overlapping speech with the nearest frame interval
create a contact sheet for each video
inspect the contact sheet and representative frames
write final storyboard rows
```

For higher precision, rerun with a smaller `--frame-step` or add scene-detection before finalizing.

## References

- Read `references/output-schema.md` when preparing backend JSONL fields.
- Read `references/local-setup.md` when the local environment, cookie capture, or E-drive model cache needs repair.
