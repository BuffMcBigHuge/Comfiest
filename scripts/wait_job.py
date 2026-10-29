#!/usr/bin/env python3
"""Poll a ComfyUI prompt until it finishes.

The MCP `job(action="wait")` call can fail at the tool layer while the server job
is still running. `/history/<prompt_id>` is authoritative; this script polls it
and exits on success, error, or timeout.

    python scripts/wait_job.py <prompt_id> --url http://127.0.0.1:8188
    python scripts/wait_job.py <prompt_id> --url http://<host>:<port> --timeout 3600
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def history(base: str, prompt_id: str, timeout: int) -> dict:
    url = f"{base}/history/{urllib.parse.quote(prompt_id)}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_id")
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()

    base = args.url.rstrip("/")
    started = time.time()
    last_report = 0.0

    while True:
        try:
            entry = history(base, args.prompt_id, 30).get(args.prompt_id)
        except Exception as exc:
            print(f"poll error: {exc}", flush=True)
            entry = None

        if entry:
            status = (entry.get("status") or {}).get("status_str", "unknown")
            messages = (entry.get("status") or {}).get("messages", []) or []
            failures = [
                message
                for message in messages
                if any(token in str(message[0]).lower() for token in ("error", "fail"))
            ]
            print(f"done: {status} after {time.time() - started:.0f}s", flush=True)
            for message in failures:
                print("ERROR", message[0], str(message[1])[:800], flush=True)
            if status != "success":
                return 1
            for node_id, output in (entry.get("outputs") or {}).items():
                for key in ("images", "gifs", "audio", "video"):
                    for item in output.get(key) or []:
                        name = item.get("filename")
                        if name:
                            print(f"output {node_id}: {name}", flush=True)
            return 0

        elapsed = time.time() - started
        if elapsed > args.timeout:
            print(f"timeout after {elapsed:.0f}s", flush=True)
            return 2
        if elapsed - last_report >= 60:
            last_report = elapsed
            print(f"running... {elapsed:.0f}s", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
