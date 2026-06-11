#!/usr/bin/env python3
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the local Douyin link -> video -> transcript -> storyboard draft pipeline."
    )
    parser.add_argument("--url", required=True, help="Douyin video/profile/short link")
    parser.add_argument("--downloader-root", required=True, help="Path to jiji262/douyin-downloader")
    parser.add_argument("--out", required=True, help="Run output directory, preferably on E: drive")
    parser.add_argument("--limit", type=int, default=3, help="Max profile posts to process")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--frame-step", type=float, default=6.0, help="Seconds between sampled frames when visual mode is enabled")
    parser.add_argument("--visual-samples", type=int, default=10, help="Max visual checkpoints per video")
    parser.add_argument("--comments", type=int, default=20, help="Max comments per video")
    parser.add_argument("--include-replies", action="store_true", help="Try to fetch comment replies")
    parser.add_argument("--skip-download", action="store_true", help="Reuse existing downloaded videos")
    parser.add_argument("--skip-transcribe", action="store_true", help="Reuse existing transcripts")
    parser.add_argument("--cache-home", default=r"E:\AIModels", help="Whisper cache root")
    parser.add_argument("--no-simplified", action="store_true", help="Do not pass --sc to transcribe script")
    parser.add_argument(
        "--visual-mode",
        choices=["none", "temp", "keep"],
        default="none",
        help="none=fast transcript timeline only, temp=sample frames then delete, keep=keep frames/contact sheets",
    )
    return parser.parse_args()


def run(cmd, cwd=None, env=None):
    if os.environ.get("DOUYIN_PIPELINE_VERBOSE"):
        try:
            print("+ " + " ".join(str(part) for part in cmd), flush=True)
        except OSError:
            pass
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def run_capture(cmd):
    return subprocess.check_output(cmd, text=True, encoding="utf-8")


def resolve_python(downloader_root: Path) -> Path:
    candidates = [
        downloader_root / ".venv" / "Scripts" / "python.exe",
        downloader_root / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def quote_yaml(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def write_downloader_config(path: Path, url: str, download_dir: Path, limit: int, comments: int, include_replies: bool):
    text = f"""link:
  - {quote_yaml(url)}

path: {quote_yaml(str(download_dir))}

music: false
cover: false
avatar: true
json: true
folderstyle: true
filename_template: "{{date}}_{{id}}"
folder_template: "{{date}}_{{id}}"

mode:
  - post

number:
  post: {max(1, int(limit))}
  like: 0
  allmix: 0
  mix: 0
  music: 0
  collect: 0
  collectmix: 0

increase:
  post: false
  like: false
  allmix: false
  mix: false
  music: false

thread: 2
retry_times: 2
rate_limit: 1
proxy: ""
database: true
database_path: {quote_yaml(str(path.parent / "dy_downloader_run.db"))}

progress:
  quiet_logs: true

browser_fallback:
  enabled: true
  headless: true
  max_scrolls: 20
  idle_rounds: 3
  wait_timeout_seconds: 180

comments:
  enabled: true
  include_replies: {str(bool(include_replies)).lower()}
  max_comments: {max(0, int(comments))}
  page_size: 20

transcript:
  enabled: false

cookies: auto
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_videos(download_dir: Path):
    return sorted(download_dir.rglob("*.mp4"))


def find_transcript(transcript_dir: Path, aweme_id: str, suffix: str):
    matches = sorted(transcript_dir.glob(f"*_{aweme_id}.transcript.{suffix}"))
    if matches:
        return matches[0]
    matches = sorted(transcript_dir.glob(f"*{aweme_id}*.transcript.{suffix}"))
    return matches[0] if matches else None


def parse_srt_time(value: str) -> float:
    hms, ms = value.split(",")
    hours, minutes, seconds = hms.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(ms) / 1000


def parse_srt(path: Path):
    if not path or not path.exists():
        return []
    raw = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").strip()
    if not raw:
        return []
    segments = []
    for block in re.split(r"\n\s*\n", raw):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start_raw, end_raw = [part.strip() for part in lines[1].split("-->", 1)]
        text = "\n".join(lines[2:])
        segments.append({"start": parse_srt_time(start_raw), "end": parse_srt_time(end_raw), "text": text})
    return segments


def overlap_text(segments, start: float, end: float):
    parts = []
    for segment in segments:
        if segment["end"] <= start or segment["start"] >= end:
            continue
        parts.append(segment["text"])
    return "\n".join(parts).strip()


def ffprobe_duration(video: Path) -> float:
    raw = run_capture([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(video),
    ])
    return float(json.loads(raw)["format"]["duration"])


def sample_times(duration: float, step: float):
    times = [0.0]
    t = max(0.5, float(step))
    while t < duration - 0.2:
        times.append(round(t, 3))
        t += max(0.5, float(step))
    end_t = max(0.0, duration - 0.35)
    if end_t - times[-1] > 0.8:
        times.append(round(end_t, 3))
    return times


def sample_checkpoints(duration: float, max_samples: int):
    count = max(1, int(max_samples))
    if duration <= 0:
        return [0.0]
    if count == 1:
        return [round(min(duration - 0.35, duration / 2), 3)]
    last = max(0.0, duration - 0.35)
    return [round((last * idx) / (count - 1), 3) for idx in range(count)]


def extract_storyboard(video: Path, aweme_id: str, storyboard_root: Path, transcript_dir: Path, frame_step: float, visual_mode: str, visual_samples: int):
    duration = ffprobe_duration(video)
    srt = find_transcript(transcript_dir, aweme_id, "srt")
    segments = parse_srt(srt) if srt else []
    if visual_mode == "none":
        draft_rows = []
        source_rows = segments or [
            {"start": start, "end": min(start + frame_step, duration), "text": ""}
            for start in sample_times(duration, frame_step)
        ]
        for idx, segment in enumerate(source_rows):
            start = round(segment["start"], 2)
            end = round(min(segment["end"], duration), 2)
            draft_rows.append(
                {
                    "aweme_id": aweme_id,
                    "shot_index": idx + 1,
                    "time_range": f"{start:.2f}-{end:.2f}s",
                    "frame_path": "",
                    "voiceover": segment.get("text", "").strip(),
                    "visual": "",
                    "shot_purpose": "",
                }
            )
        return {
            "aweme_id": aweme_id,
            "video_path": str(video),
            "duration": round(duration, 2),
            "frames": [],
            "contact_sheet": "",
            "visual_cache": "not_created",
            "timeline_rows": draft_rows,
        }

    temp_context = None
    keep_visual_cache = visual_mode == "keep"
    if keep_visual_cache:
        item_dir = storyboard_root / aweme_id
    else:
        temp_context = tempfile.TemporaryDirectory(prefix=f"douyin_{aweme_id}_")
        item_dir = Path(temp_context.name)
    frames_dir = item_dir / "frames"
    item_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    times = sample_checkpoints(duration, visual_samples)
    frames = []
    for idx, ts in enumerate(times):
        frame = frames_dir / f"{idx:02d}_{ts:05.2f}s.jpg"
        run([
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{ts:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            "scale=480:-1",
            str(frame),
        ])
        frames.append({"index": idx, "time": round(ts, 2), "file": str(frame) if keep_visual_cache else ""})

    contact_sheet = item_dir / f"{aweme_id}_contact.jpg"
    list_file = item_dir / "frames.txt"
    frame_files = sorted(frames_dir.glob("*.jpg"))
    list_file.write_text("\n".join(f"file '{path.as_posix()}'" for path in frame_files), encoding="utf-8")
    rows = max(1, math.ceil(len(frames) / 4))
    run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vf",
        f"scale=240:-1,tile=4x{rows}:padding=8:margin=8:color=white",
        "-frames:v",
        "1",
        str(contact_sheet),
    ])

    draft_rows = []
    for idx, frame in enumerate(frames):
        start = frame["time"]
        end = frames[idx + 1]["time"] if idx + 1 < len(frames) else round(duration, 2)
        draft_rows.append(
            {
                "aweme_id": aweme_id,
                "shot_index": idx + 1,
                "time_range": f"{start:.2f}-{end:.2f}s",
                "frame_path": frame["file"],
                "voiceover": overlap_text(segments, start, end),
                "visual": "",
                "shot_purpose": "",
            }
        )

    result = {
        "aweme_id": aweme_id,
        "video_path": str(video),
        "duration": round(duration, 2),
        "frames": frames if keep_visual_cache else [{"index": row["index"], "time": row["time"], "file": ""} for row in frames],
        "contact_sheet": str(contact_sheet) if keep_visual_cache else "",
        "visual_cache": "kept" if keep_visual_cache else "temporary_deleted",
        "timeline_rows": draft_rows,
    }
    if temp_context:
        temp_context.cleanup()
    return result


def main():
    args = parse_args()
    downloader_root = Path(args.downloader_root).expanduser().resolve()
    out_root = Path(args.out).expanduser().resolve()
    download_dir = out_root / "downloaded"
    transcript_dir = out_root / "transcripts"
    storyboard_dir = out_root / "storyboard"
    artifacts_dir = out_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if not downloader_root.exists():
        raise SystemExit(f"downloader-root does not exist: {downloader_root}")
    if not (downloader_root / "run.py").exists():
        raise SystemExit(f"downloader-root does not look like douyin-downloader: {downloader_root}")

    python = resolve_python(downloader_root)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["XDG_CACHE_HOME"] = args.cache_home

    config_path = artifacts_dir / "douyin_download_config.yml"
    write_downloader_config(config_path, args.url, download_dir, args.limit, args.comments, args.include_replies)

    if not args.skip_download:
        run([str(python), "run.py", "-c", str(config_path), "--show-warnings"], cwd=downloader_root, env=env)

    videos = find_videos(download_dir)
    if not videos:
        raise SystemExit(f"No mp4 files found in {download_dir}")

    if not args.skip_transcribe:
        cmd = [
            str(python),
            "cli\\whisper_transcribe.py" if os.name == "nt" else "cli/whisper_transcribe.py",
            "-d",
            str(download_dir),
            "-m",
            args.model,
            "-l",
            "zh",
            "--srt",
            "-o",
            str(transcript_dir),
        ]
        if not args.no_simplified:
            cmd.insert(-2, "--sc")
        run(cmd, cwd=downloader_root, env=env)

    transcript_rows = []
    summaries = []
    timeline_rows = []

    for video in videos:
        aweme_id = video.stem.split("_")[-1]
        txt = find_transcript(transcript_dir, aweme_id, "txt")
        if txt:
            transcript_rows.append(
                {
                    "aweme_id": aweme_id,
                    "video_path": str(video),
                    "transcript_path": str(txt),
                    "raw_transcript": txt.read_text(encoding="utf-8", errors="replace").strip(),
                    "clean_transcript": "",
                    "needs_review": True,
                }
            )
        summary = extract_storyboard(video, aweme_id, storyboard_dir, transcript_dir, args.frame_step, args.visual_mode, args.visual_samples)
        summaries.append({key: value for key, value in summary.items() if key != "timeline_rows"})
        timeline_rows.extend(summary["timeline_rows"])

    (artifacts_dir / "transcripts.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in transcript_rows) + "\n",
        encoding="utf-8",
    )
    (artifacts_dir / "timeline-draft.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in timeline_rows) + "\n",
        encoding="utf-8",
    )
    (artifacts_dir / "frame-summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "videos": len(videos),
                "download_dir": str(download_dir),
                "transcript_dir": str(transcript_dir),
                "storyboard_dir": str(storyboard_dir),
                "artifacts_dir": str(artifacts_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
