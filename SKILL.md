---
name: douyin-link-storyboard
description: Extract complete spoken copy, copy-writing structure, and lightweight timecode storyboards from a Douyin profile or video link using a free local workflow. Use when the user provides a Douyin short link, profile link, or video link and asks to抓取对标账号, 提取视频文案, 拆文案结构, 还原分镜表, or prepare JSONL outputs for a backend knowledge base.
---

# Douyin Link Storyboard

Use this skill to turn a Douyin profile/video link into reusable creative research artifacts:

```text
Douyin link -> video files -> full spoken copy -> copy structure -> timecodes -> storyboard table
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
   - For competitor-account replication, use `--limit 5` by default.
   - Use a small limit such as `--limit 3` only for quick smoke tests.
   - Use `--model small` for normal Chinese product口播.
4. For visual sanity-checks, sample at most 10 checkpoints per video, inspect them internally, then delete them.
5. Produce final deliverables:
   - Account profile and video data
   - Complete copy for 5 videos
   - Copywriting analysis for each video
   - Detailed remake-grade storyboard for each video
   - Account-level remake playbook
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

When the user's goal is to learn from or replicate a competitor account, do not output only a rough storyboard. Produce a complete competitor-account research package:

```text
account-profile.md
full-copy-5-videos.md
copywriting-analysis-5-videos.md
detailed-storyboard-5-videos.md
remake-playbook.md
```

The storyboard must be detailed enough for shooting a similar video, with:

```text
time_range
voiceover
subtitles_screen_text
base_visual
code_blocks
motion_effects
remake_tip
shot_purpose
```

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
visual
code_blocks
motion_effects
subtitles_screen_text
voiceover
shot_purpose
```

Default to text-only outputs. If screenshots/frames are needed for checking, sample at most 10 per video, inspect them internally, then delete them. Do not present image grids or embed screenshots unless the user explicitly asks to see them. Final user-facing storyboard output should be a clean text table.

For Codex/Remotion-style videos, do not stop at “真人口播”. Extract the coded layer separately:

```text
text blocks / data blocks / UI screenshot blocks / card blocks / highlight labels
subtitles / bilingual subtitles / title text / data text / UI text / CTA text
entrance animation / slide / scale / fade / mask / glow / emphasis / subtitle sync
```

Do not invent visual details that are not visible.

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
read SRT timecodes
split by speech/timecode segments
optionally sample 10 visual checkpoints per video
delete visual checkpoints after inspection
write final storyboard rows
```

For higher precision, rerun with a smaller speech/scene interval or add scene-detection before finalizing.

## References

- Read `references/output-schema.md` when preparing backend JSONL fields.
- Read `references/local-setup.md` when the local environment, cookie capture, or E-drive model cache needs repair.
