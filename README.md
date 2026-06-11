# Douyin Link Storyboard

Codex skill for analyzing Douyin competitor accounts and turning recent videos into a remake-ready research package.

This skill is designed for creators who want to study an AI/knowledge creator account and produce similar videos with the same copywriting structure, subtitle rhythm, coded visual blocks, motion cues, and shooting plan.

## What It Does

Given a Douyin profile, share, or video link, the skill helps Codex produce a five-video competitor analysis package:

- Account profile and recent video data
- Full spoken copy for 5 videos
- Copywriting analysis for each video
- Detailed remake-grade storyboard for each video
- Account-level remake playbook
- JSONL artifacts for backend knowledge-base ingestion

The storyboard is not a rough summary. It is meant to be detailed enough to shoot a similar video.

## Output Package

For competitor-account research, the standard output is:

```text
account-profile.md
full-copy-5-videos.md
copywriting-analysis-5-videos.md
detailed-storyboard-5-videos.md
remake-playbook.md
```

The detailed storyboard includes:

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

## Typical Use Case

Example user intent:

> Here is a Douyin account. I also make AI videos. Get the account info, 5 complete videos, all copywriting, detailed storyboard scripts, and tell me how this creator writes hooks, openings, endings, subtitles, blocks, and motion effects so I can shoot similar videos.

## Local Workflow

The skill uses a local Douyin downloader, local browser/cookie state, and local Whisper transcription.

Default scale:

- 5 videos per competitor account
- Whisper `small` model
- Up to 15 temporary visual checkpoints per video
- Screenshots/frames are inspected internally and deleted
- Final output is text/JSON only unless the user explicitly asks to see screenshots

## Main Command

```powershell
python E:\CodexSkills\douyin-link-storyboard\scripts\douyin_storyboard_pipeline.py `
  --url "https://v.douyin.com/..." `
  --downloader-root "C:\path\to\work\douyin-downloader" `
  --out "E:\DouyinRuns\sample-run" `
  --limit 5 `
  --model small `
  --visual-mode none
```

## Requirements

- Windows PowerShell
- Python environment for the Douyin downloader
- `ffmpeg` and `ffprobe`
- OpenAI Whisper installed locally
- A working Douyin downloader repo
- User-owned Douyin browser login/cookies when Douyin requires login

The skill does not bypass Douyin protections, CAPTCHA, login gates, or rate limits. It works with the user's own browser login state or cookies.

## Install As A Codex Skill

Clone this repository into your Codex skills folder, or place it under a custom skills directory and point Codex to it.

Example:

```powershell
git clone https://github.com/a2244111009-ux/douyin-link-storyboard.git E:\CodexSkills\douyin-link-storyboard
```

Then use it when asking Codex to analyze Douyin competitor accounts.

## Notes

- Use E drive for large outputs and model cache.
- Do not save visual frames by default.
- Keep raw ASR transcripts separate from cleaned editorial copy.
- For Codex/Remotion-style creator videos, always separate subtitles/screen text from voiceover.
- For creator replication, the final deliverable should be a remake-ready package, not only a storyboard table.
