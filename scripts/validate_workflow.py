#!/usr/bin/env python3
"""Validate an API-format ComfyUI workflow against a live target.

Checks node classes, required inputs, combo values, links, model files, and save
prefixes. It does not submit a job and does not modify the workflow.

    python scripts/validate_workflow.py <workflow.api.json> --url http://127.0.0.1:8188

For a UI-format export, convert it first (this also does not queue a job):

    comfy run --workflow <workflow.json> --print-prompt --json --host <host> --port <port>
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MODEL_FOLDERS = {
    "lora_name": "loras",
    "unet_name": "diffusion_models",
    "vae_name": "vae",
    "clip_name": "text_encoders",
    "clip_name1": "text_encoders",
    "clip_name2": "text_encoders",
    "ckpt_name": "checkpoints",
    "control_net_name": "controlnet",
    "style_model_name": "style_models",
}

# model_name is overloaded; a few classes own the folder.
MODEL_NAME_FOLDERS = {
    "LatentUpscaleModelLoader": "latent_upscale_models",
    "UpscaleModelLoader": "upscale_models",
}


def get_json(base: str, path: str, timeout: int) -> dict | list:
    with urllib.request.urlopen(base + path, timeout=timeout) as response:
        return json.load(response)


def combo_options(spec) -> list | None:
    """Return allowed values for a COMBO input schema, else None."""
    if not isinstance(spec, list) or not spec:
        return None
    kind = spec[0]
    config = spec[1] if len(spec) > 1 else {}
    if isinstance(kind, list):
        return kind
    if kind == "COMBO" and isinstance(config, dict):
        return config.get("options")
    return None


def collect_input_names(section) -> set[str]:
    """Collect top-level and nested dynamic-combo input names for a node."""
    names: set[str] = set()
    for key, spec in (section or {}).items():
        names.add(key)
        if isinstance(spec, list) and spec and spec[0] == "COMFY_DYNAMICCOMBO_V3":
            for option in (spec[1] or {}).get("options", []):
                inner = option.get("inputs") or {}
                names |= collect_input_names(inner.get("required"))
                names |= collect_input_names(inner.get("optional"))
    return names


def format_option_names(spec, selected) -> set[str]:
    """VHS-style schemas list per-format widget names under config['formats']."""
    names: set[str] = set()
    if not isinstance(spec, list) or len(spec) < 2 or not isinstance(spec[1], dict):
        return names
    formats = spec[1].get("formats")
    if not isinstance(formats, dict):
        return names
    for entry in formats.get(selected) or []:
        if isinstance(entry, list) and entry:
            names.add(str(entry[0]))
    return names


def model_folder(class_type: str, input_name: str) -> str | None:
    if class_type == "FL_RIFE" and input_name == "ckpt_name":
        # RIFE checkpoints live in the node pack, not models/checkpoints.
        return None
    if input_name in MODEL_FOLDERS:
        return MODEL_FOLDERS[input_name]
    if input_name == "model_name":
        return MODEL_NAME_FOLDERS.get(class_type)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    base = args.url.rstrip("/")
    try:
        graph = json.loads(args.workflow.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: cannot parse {args.workflow}: {exc}")
        return 2

    if not isinstance(graph, dict) or "nodes" in graph:
        print("ERROR: this is a UI-format workflow. Convert it first:")
        print("  comfy run --workflow <file> --print-prompt --json --host <host> --port <port>")
        print("  then inspect the prompt_preview and save an API-format copy under work/scratch/.")
        return 2

    try:
        object_info = get_json(base, "/object_info", args.timeout)
    except Exception as exc:
        print(f"ERROR: cannot read {base}/object_info: {exc}")
        return 2

    model_cache: dict[str, set[str] | None] = {}

    def target_models(folder: str) -> set[str] | None:
        if folder not in model_cache:
            try:
                files = get_json(base, f"/models/{urllib.parse.quote(folder)}", args.timeout)
                model_cache[folder] = {str(x) for x in files}
            except Exception:
                model_cache[folder] = None
        return model_cache[folder]

    errors: list[str] = []
    warnings: list[str] = []

    for node_id, node in graph.items():
        class_type = node.get("class_type")
        if not class_type:
            errors.append(f"[{node_id}] missing class_type")
            continue
        if class_type not in object_info:
            errors.append(f"[{node_id}] missing node class: {class_type}")
            continue

        schema = object_info[class_type]
        required = (schema.get("input") or {}).get("required") or {}
        optional = (schema.get("input") or {}).get("optional") or {}
        outputs = schema.get("output") or []
        inputs = node.get("inputs") or {}
        known_inputs = collect_input_names(required) | collect_input_names(optional)
        for name, spec in {**required, **optional}.items():
            if name in inputs:
                known_inputs |= format_option_names(spec, inputs[name])

        # Dynamic combos expose extra required inputs under the selected key.
        dynamic_required: dict = {}
        for key, spec in required.items():
            if isinstance(spec, list) and spec and spec[0] == "COMFY_DYNAMICCOMBO_V3":
                selected = inputs.get(key)
                for option in (spec[1] or {}).get("options", []):
                    if option.get("key") == selected:
                        dynamic_required = (option.get("inputs") or {}).get("required") or {}
                        break
                else:
                    if selected is not None:
                        errors.append(f"[{node_id}] {class_type}.{key}: '{selected}' not in dynamic options")

        all_required = {**required, **dynamic_required}
        for key, spec in all_required.items():
            if key in optional:
                # A dynamic sub-input can also be declared as a top-level
                # optional fallback (for example SaveVideo.codec).
                continue
            if key in dynamic_required and key not in required:
                parent = next(
                    (
                        name
                        for name, parent_spec in required.items()
                        if isinstance(parent_spec, list)
                        and parent_spec
                        and parent_spec[0] == "COMFY_DYNAMICCOMBO_V3"
                        and any(
                            option.get("key") == inputs.get(name)
                            and key in ((option.get("inputs") or {}).get("required") or {})
                            for option in (parent_spec[1] or {}).get("options", [])
                        )
                    ),
                    None,
                )
                if parent is not None and f"{parent}.{key}" in inputs:
                    continue
            if key not in inputs:
                if any(name.startswith(key + ".") for name in inputs):
                    continue
                config = spec[1] if isinstance(spec, list) and len(spec) > 1 else {}
                if not (isinstance(config, dict) and "default" in config):
                    errors.append(f"[{node_id}] {class_type}: missing required input '{key}'")

        for key, value in inputs.items():
            if "." in key and key.split(".", 1)[0] in {**required, **optional}:
                continue
            spec = required.get(key) or optional.get(key)
            if spec is None:
                if key in known_inputs:
                    continue
                if class_type == "Any Switch (rgthree)" and key.startswith("any_"):
                    continue
                if not key.startswith(("PowerLora", "lora_", "➕")):
                    warnings.append(f"[{node_id}] {class_type}: input '{key}' not in schema")
                continue

            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str):
                source_id, slot = value
                if source_id not in graph:
                    errors.append(f"[{node_id}] {class_type}.{key}: link to missing node {source_id}")
                    continue
                source_outputs = object_info.get(graph[source_id].get("class_type"), {}).get("output") or []
                if not isinstance(slot, int) or slot >= len(source_outputs):
                    errors.append(
                        f"[{node_id}] {class_type}.{key}: {source_id} has no output {slot} "
                        f"(has {len(source_outputs)})"
                    )
                continue

            options = combo_options(spec)
            if options is not None and value not in options:
                if isinstance(value, str) and value.startswith("example."):
                    warnings.append(
                        f"[{node_id}] {class_type}.{key}: placeholder '{value}' is not on the target yet"
                    )
                else:
                    errors.append(f"[{node_id}] {class_type}.{key}: '{value}' not in combo ({len(options)} options)")

            folder = model_folder(class_type, key)
            if folder and isinstance(value, str) and value not in ("None", ""):
                files = target_models(folder)
                if files is None:
                    warnings.append(f"[{node_id}] {class_type}.{key}: /models/{folder} unavailable; skipped")
                elif value not in files:
                    errors.append(f"[{node_id}] {class_type}.{key}: file not on target: {value}")

        # rgthree's loader stores slots as objects instead of links.
        if class_type == "Power Lora Loader (rgthree)":
            loras = target_models("loras")
            for key, value in inputs.items():
                if not key.startswith("lora_") or not isinstance(value, dict):
                    continue
                name = value.get("lora")
                if not name or name == "None" or not value.get("on", True):
                    continue
                if loras is not None and name not in loras:
                    errors.append(f"[{node_id}] {class_type}.{key}: LoRA not on target: {name}")

        if class_type in ("SaveImage", "SaveVideo", "VHS_VideoCombine"):
            prefix = inputs.get("filename_prefix")
            if not prefix:
                errors.append(f"[{node_id}] {class_type}: empty filename_prefix")
            elif "%" in str(prefix):
                warnings.append(f"[{node_id}] {class_type}: filename_prefix has a date/token: {prefix}")
            elif len(str(prefix)) > 1 and str(prefix)[1] == ":":
                warnings.append(f"[{node_id}] {class_type}: absolute filename_prefix: {prefix}")

    print(f"{args.workflow}: {len(graph)} nodes, {len(errors)} errors, {len(warnings)} warnings")
    for error in errors:
        print("  ERROR  ", error)
    for warning in warnings:
        print("  warn   ", warning)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
