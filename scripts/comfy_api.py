#!/usr/bin/env python3
"""Shared ComfyUI HTTP helpers for the standalone scripts.

`history_entry` exists because ComfyUI 0.43+ can return `{}` from
`GET /history/<prompt_id>` for a job that is present and complete in
`GET /history?max_items=N`. Both `wait_job.py` and `fetch_output.py` relied on
the per-ID endpoint alone and reported "not found" for successful jobs.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

# Enough to cover a busy shared target without pulling megabytes of history.
HISTORY_PAGE = 50


def get_json(base: str, path: str, timeout: int):
    with urllib.request.urlopen(base + path, timeout=timeout) as response:
        return json.load(response)


def history_entry(base: str, prompt_id: str, timeout: int = 30) -> dict | None:
    """Return a prompt's history entry, falling back to the paginated listing.

    Returns None when the prompt is genuinely absent (pruned, or a different
    target). Raises only on transport errors.
    """
    quoted = urllib.parse.quote(prompt_id)
    entry = get_json(base, f"/history/{quoted}", timeout)
    if isinstance(entry, dict):
        found = entry.get(prompt_id)
        if found:
            return found

    page = get_json(base, f"/history?max_items={HISTORY_PAGE}", timeout)
    if isinstance(page, dict):
        return page.get(prompt_id)
    return None
