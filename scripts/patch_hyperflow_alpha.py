#!/usr/bin/env python3
"""Repair the fused-QKV alpha in the HyperFlow MiniMax-H3 LoRA.

ComfyUI applies a LoRA at ``alpha / lora_A.shape[0]``. A fused ``qkv_proj``
adapter stacks three projections, so its ``alpha`` must equal the fused row
count (3 x rank) for a 1.0 scale. The upstream HyperFlow ComfyUI conversion
writes 256 for a 768-row fused A, which applies the qkv adapters at 1/3
strength.

This script rewrites only those scalar alpha tensors; no weight values are
touched. It is idempotent: an already-correct file reports zero changes.

Usage:
    python scripts/patch_hyperflow_alpha.py --comfyui C:/ComfyUI
    python scripts/patch_hyperflow_alpha.py --comfyui ~/ComfyUI --write
    python scripts/patch_hyperflow_alpha.py --file /path/to/lora.safetensors --write

Without ``--write`` the script only reports what it would change.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

DEFAULT_REL = Path("models/loras/minimax/minimax_h3_hyperflow_8step_v1.0_comfyui_bf16.safetensors")
DTYPE_SIZE = {"F32": 4, "F16": 2, "BF16": 2}


def read_header(path: Path) -> tuple[dict, int]:
    with path.open("rb") as f:
        raw = f.read(8)
        if len(raw) != 8:
            raise ValueError("not a safetensors file: missing header length")
        (header_len,) = struct.unpack("<Q", raw)
        header = json.loads(f.read(header_len).decode("utf-8"))
    header.pop("__metadata__", None)
    return header, header_len


def decode_scalar(blob: bytes, dtype: str) -> float:
    if dtype == "F32":
        return struct.unpack("<f", blob)[0]
    if dtype == "F16":
        return struct.unpack("<e", blob)[0]
    if dtype == "BF16":
        bits = struct.unpack("<H", blob)[0]
        return struct.unpack("<f", struct.pack("<I", bits << 16))[0]
    raise ValueError(f"unsupported alpha dtype: {dtype}")


def encode_scalar(value: float, dtype: str) -> bytes:
    if dtype == "F32":
        return struct.pack("<f", value)
    if dtype == "F16":
        return struct.pack("<e", value)
    if dtype == "BF16":
        bits = struct.unpack("<I", struct.pack("<f", value))[0]
        return struct.pack("<H", (bits >> 16) & 0xFFFF)
    raise ValueError(f"unsupported alpha dtype: {dtype}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--comfyui", type=Path, help="ComfyUI root; resolves the standard HyperFlow path")
    target.add_argument("--file", type=Path, help="explicit path to the HyperFlow safetensors file")
    parser.add_argument("--write", action="store_true", help="rewrite the alpha tensors in place")
    args = parser.parse_args()

    if args.file:
        path = args.file
    elif args.comfyui:
        path = args.comfyui / DEFAULT_REL
    else:
        path = Path.cwd() / DEFAULT_REL

    if not path.is_file():
        print(f"missing: {path}", file=sys.stderr)
        print("Pass --comfyui <root> or --file <path>.", file=sys.stderr)
        return 1

    header, header_len = read_header(path)
    data_start = 8 + header_len
    targets = []
    for key, info in header.items():
        if not key.endswith(".qkv_proj.alpha"):
            continue
        base = key[: -len(".alpha")]
        a_weight = header.get(base + ".lora_A.weight")
        if a_weight is None:
            continue
        expected = float(a_weight["shape"][0])
        dtype = info.get("dtype", "F32")
        if dtype not in DTYPE_SIZE:
            print(f"skip {key}: unsupported dtype {dtype}", file=sys.stderr)
            continue
        offset = data_start + info["data_offsets"][0]
        targets.append((key, offset, expected, dtype))

    if not targets:
        print(f"no fused-qkv alpha tensors found in {path}", file=sys.stderr)
        return 1

    changes = 0
    with path.open("r+b") as f:
        for key, offset, expected, dtype in targets:
            f.seek(offset)
            current = decode_scalar(f.read(DTYPE_SIZE[dtype]), dtype)
            if abs(current - expected) > 1e-6:
                changes += 1
                if changes <= 4:
                    print(f"  {key}: {current:g} -> {expected:g}")
                if args.write:
                    f.seek(offset)
                    f.write(encode_scalar(expected, dtype))

    print(f"file: {path}")
    print(f"qkv alpha tensors: {len(targets)}; {'patched' if args.write else 'would patch'}: {changes}")
    if changes and not args.write:
        print("Re-run with --write to apply.")
        return 0

    if args.write:
        header, header_len = read_header(path)
        data_start = 8 + header_len
        bad = 0
        with path.open("rb") as f:
            for key, info in header.items():
                if not key.endswith(".qkv_proj.alpha"):
                    continue
                base = key[: -len(".alpha")]
                expected = float(header[base + ".lora_A.weight"]["shape"][0])
                dtype = info.get("dtype", "F32")
                f.seek(data_start + info["data_offsets"][0])
                value = decode_scalar(f.read(DTYPE_SIZE[dtype]), dtype)
                if abs(value - expected) > 1e-6:
                    bad += 1
        print(f"verify: qkv alphas not equal to fused rank: {bad}")
        return 1 if bad else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
