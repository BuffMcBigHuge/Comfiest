#!/usr/bin/env python3
"""Download a prompt's outputs directly from ComfyUI's /history and /view.

Use this when `fetch_outputs` returns `download_job_not_found` or falls back to a
local address because the prompt ID was submitted elsewhere.

    python scripts/fetch_output.py <prompt_id> --url http://<host>:<port> --out-dir work/outputs/<project>/<date>/<prompt_id>

The out-dir is written as given; preserve the remote filename and the
`<project>/<date>/<prompt_id>` layout from the run-log rules.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def history(base: str, prompt_id: str, timeout: int) -> dict:
    url = f"{base}/history/{urllib.parse.quote(prompt_id)}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def download(base: str, item: dict, destination: Path, timeout: int) -> Path:
    query = urllib.parse.urlencode(
        {
            "filename": item.get("filename", ""),
            "subfolder": item.get("subfolder", ""),
            "type": item.get("type", "output"),
        }
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"{base}/view?{query}", timeout=timeout) as response:
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                handle.write(chunk)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_id")
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    base = args.url.rstrip("/")
    try:
        entry = history(base, args.prompt_id, 30).get(args.prompt_id)
    except Exception as exc:
        print(f"ERROR: cannot read history: {exc}")
        return 2
    if not entry:
        print(f"ERROR: {args.prompt_id} is not in /history (pruned, or a different target)")
        return 1

    outputs = entry.get("outputs") or {}
    if not outputs:
        print("ERROR: history has no outputs yet; poll the job first")
        return 1

    count = 0
    for node_id, output in outputs.items():
        for key in ("images", "gifs", "audio", "video"):
            for item in output.get(key) or []:
                filename = Path(str(item.get("filename", ""))).name
                if not filename:
                    continue
                target = download(base, {**item, "filename": filename}, args.out_dir / filename, args.timeout)
                print(f"{node_id}  {target}  {target.stat().st_size} bytes")
                count += 1

    if not count:
        print("ERROR: no downloadable files in the history output")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
