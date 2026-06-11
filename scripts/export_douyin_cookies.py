#!/usr/bin/env python3
import argparse
import asyncio
import json
from pathlib import Path

REQUIRED = {"ttwid", "odin_tt", "passport_csrf_token"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export Douyin cookies from a Chrome/Edge CDP session into douyin-downloader."
    )
    parser.add_argument("--cdp", default="http://127.0.0.1:9222", help="Chrome DevTools endpoint")
    parser.add_argument("--downloader-root", required=True, help="Path to jiji262/douyin-downloader")
    parser.add_argument("--output", default="", help="Override cookie JSON path")
    return parser.parse_args()


async def main():
    args = parse_args()
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise SystemExit(
            "Missing playwright. Install it in the Python environment used for this script: "
            "python -m pip install playwright"
        ) from exc

    downloader_root = Path(args.downloader_root).expanduser().resolve()
    if not downloader_root.exists():
        raise SystemExit(f"downloader-root does not exist: {downloader_root}")

    output = Path(args.output).expanduser().resolve() if args.output else downloader_root / "config" / "cookies.json"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(args.cdp)
        if not browser.contexts:
            raise SystemExit("No browser contexts found. Start Chrome with remote debugging first.")
        context = browser.contexts[0]
        pages = context.pages
        page = next((candidate for candidate in pages if "douyin.com" in candidate.url), None)
        if page is None:
            page = pages[0] if pages else await context.new_page()
            await page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=30000)

        cookies = await context.cookies(["https://www.douyin.com", "https://douyin.com"])
        picked = {}
        for cookie in cookies:
            domain = cookie.get("domain") or ""
            name = cookie.get("name") or ""
            value = cookie.get("value") or ""
            if "douyin.com" in domain and name and value:
                picked[name] = value

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(picked, ensure_ascii=False, indent=2), encoding="utf-8")

        missing = sorted(key for key in REQUIRED if not picked.get(key))
        title = ""
        try:
            title = await page.title()
        except Exception:
            title = ""
        print(
            json.dumps(
                {
                    "page_url": page.url,
                    "page_title": title,
                    "cookie_count": len(picked),
                    "has_required": not missing,
                    "missing_required": missing,
                    "output": str(output),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
