#!/usr/bin/env python3
"""Validate an API-format ComfyUI workflow, statically or against a live target.

Static checks need no server and are what CI runs:

    python scripts/validate_workflow.py <workflow.api.json> --static [--strict]

They cover graph integrity — link targets that exist, tensor inputs that are
actually linked rather than carrying a filename, dead nodes, and save prefixes.
They cannot check node classes, required inputs, or loader option lists, because
those live in the target's `/object_info`.

Live checks add those, against a running ComfyUI:

    python scripts/validate_workflow.py <workflow.api.json> --url http://127.0.0.1:8188

Pass several files to check a directory's worth in one call. For a UI-format
export, convert it first (this also does not queue a job):

    comfy run --workflow <workflow.json> --print-prompt --json --host <host> --port <port>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

# A media filename as a literal input value. Loaders are the only classes that
# legitimately carry one; everywhere else it means a tensor link was overwritten
# by a filename, which is the exact damage a placeholder-sanitization pass causes.
MEDIA_FILENAME = re.compile(
    r"\.(png|jpe?g|webp|gif|bmp|tiff?|mp4|mov|mkv|webm|avi|wav|mp3|flac|ogg|m4a)$",
    re.IGNORECASE,
)

# Input schema types that only ever accept a link `[source_node_id, slot]`.
# A literal here is always a bug: ComfyUI coerces it late (or not at all) and the
# node fails at execution with a type error. IMAGEUPLOAD is deliberately absent:
# it is a widget that carries a filename string.
LINK_ONLY_TYPES = frozenset(
    {
        "IMAGE",
        "LATENT",
        "MASK",
        "AUDIO",
        "VIDEO",
        "MODEL",
        "CLIP",
        "VAE",
        "CONDITIONING",
        "CONTROL_NET",
        "SIGMAS",
        "GUIDER",
        "SAMPLER",
        "NOISE",
        "CLIP_VISION",
        "CLIP_VISION_OUTPUT",
        "UPSCALE_MODEL",
        "STYLE_MODEL",
        "AUDIO_ENCODER",
        "LATENT_OPERATION",
        "TIMESTEP",
    }
)

# Terminal classes used when no target is available (--static). The live target
# answers this authoritatively through `output_node` in /object_info, so this is
# only the fallback: every shipped terminal is a Save*/Preview* node, plus the
# VideoHelperSuite combiner. Do not enumerate save formats here — SaveAudioAdvanced,
# SaveAudioMP3 and SaveAudioOpus are all matched by the prefix rule.
STATIC_OUTPUT_PREFIXES = ("Save", "Preview")
STATIC_OUTPUT_CLASSES = frozenset({"VHS_VideoCombine", "VHS_VideoCombineFFmpeg"})


def is_output_class(class_type: str, object_info: dict | None = None) -> bool:
    """True when a node terminates the graph rather than feeding another node."""
    if object_info is not None:
        schema = object_info.get(class_type)
        if isinstance(schema, dict) and "output_node" in schema:
            return bool(schema["output_node"])
    return class_type.startswith(STATIC_OUTPUT_PREFIXES) or class_type in STATIC_OUTPUT_CLASSES


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


def is_link_only(spec) -> str | None:
    """Return the tensor type name when an input schema accepts links only."""
    if not isinstance(spec, list) or not spec:
        return None
    kind = spec[0]
    if isinstance(kind, str) and kind in LINK_ONLY_TYPES:
        return kind
    return None


def is_link(value) -> bool:
    return isinstance(value, list) and len(value) == 2 and isinstance(value[0], str)


def is_loader(class_type: str) -> bool:
    """Loader nodes take a filename where every other node takes a link."""
    return class_type.startswith(("Load", "VHS_Load"))


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


def loader_options(object_info: dict, class_name: str, input_name: str) -> list | None:
    schema = object_info.get(class_name) or {}
    spec = ((schema.get("input") or {}).get("required") or {}).get(input_name)
    return combo_options(spec)


def check_save_prefix(node_id: str, class_type: str, inputs: dict) -> tuple[list[str], list[str]]:
    """Validate a save node's filename_prefix.

    An empty prefix is an error: ComfyUI rejects the node, and provenance is lost
    because the run can no longer be identified by prompt_id alone. A token or
    absolute path is a warning, since it still runs but breaks collection.
    """
    errors: list[str] = []
    warnings: list[str] = []
    prefix = inputs.get("filename_prefix")
    if not prefix:
        errors.append(f"[{node_id}] {class_type}: empty filename_prefix")
    elif "%" in str(prefix):
        warnings.append(f"[{node_id}] {class_type}: filename_prefix has a date/token: {prefix}")
    elif len(str(prefix)) > 1 and str(prefix)[1] == ":":
        warnings.append(f"[{node_id}] {class_type}: absolute filename_prefix: {prefix}")
    return errors, warnings


def unreachable_nodes(graph: dict, object_info: dict | None = None) -> list[str]:
    """Nodes that cannot reach a terminal node, found by backward traversal.

    A one-hop "nothing consumes my output" test only names the leaf of a dead
    chain: in `#146 -> #147`, deleting #147 promotes #146 to the next run's
    leaf. Walking upstream from the output nodes finds the whole chain at once.
    """
    reachable: set[str] = {
        node_id
        for node_id, node in graph.items()
        if is_output_class(node.get("class_type") or "?", object_info)
    }
    stack = list(reachable)
    while stack:
        node = graph[stack.pop()]
        for value in (node.get("inputs") or {}).values():
            if is_link(value) and value[0] in graph and value[0] not in reachable:
                reachable.add(value[0])
                stack.append(value[0])

    return sorted((set(graph) - reachable), key=lambda node_id: (len(node_id), node_id))


def check_graph_integrity(
    graph: dict,
    errors: list[str],
    warnings: list[str],
    object_info: dict | None = None,
) -> None:
    """Checks that need no target: link shape, tensor literals, dead nodes."""
    for node_id, node in graph.items():
        class_type = node.get("class_type") or "?"
        for key, value in (node.get("inputs") or {}).items():
            if not is_link(value):
                # A media filename on a non-loader input is a link that a
                # sanitization pass replaced with a placeholder.
                if (
                    isinstance(value, str)
                    and MEDIA_FILENAME.search(value)
                    and not is_loader(class_type)
                    and not key.endswith("_prefix")
                ):
                    errors.append(
                        f"[{node_id}] {class_type}.{key}: media filename on a non-loader input; "
                        f"expected a link, got {value!r}"
                    )
                continue
            source_id, slot = value
            if source_id not in graph:
                errors.append(f"[{node_id}] {class_type}.{key}: link to missing node {source_id}")
                continue
            if not isinstance(slot, int):
                errors.append(f"[{node_id}] {class_type}.{key}: link slot is not an int: {slot!r}")

    for node_id in unreachable_nodes(graph, object_info):
        class_type = graph[node_id].get("class_type") or "?"
        warnings.append(f"[{node_id}] {class_type}: unreachable (does not feed an output node)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate API-format ComfyUI workflows. Use --static for graph integrity "
        "with no server (what CI runs), or --url for node classes and model files against a live target.",
        epilog=(
            "examples:\n"
            "  python scripts/validate_workflow.py --static workflows/ltx/api/*.api.json\n"
            "  python scripts/validate_workflow.py graph.api.json --url http://127.0.0.1:8188\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("workflow", type=Path, nargs="+")
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--static",
        action="store_true",
        help="graph integrity only; no server needed",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero on warnings as well as errors (use in CI)",
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")
    object_info: dict | None = None
    if not args.static:
        try:
            object_info = get_json(base, "/object_info", args.timeout)
        except Exception as exc:
            print(f"ERROR: cannot read {base}/object_info: {exc}")
            print("  (use --static to check graph integrity without a server)")
            return 2

    failed = 0
    for path in args.workflow:
        try:
            graph = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"ERROR: cannot parse {path}: {exc}")
            return 2

        if not isinstance(graph, dict) or "nodes" in graph:
            print(f"ERROR: {path} is a UI-format workflow. Convert it first:")
            print("  comfy run --workflow <file> --print-prompt --json --host <host> --port <port>")
            print("  then inspect the prompt_preview and save an API-format copy under work/scratch/.")
            return 2

        errors: list[str] = []
        warnings: list[str] = []

        check_graph_integrity(graph, errors, warnings, object_info)

        for node_id, node in graph.items():
            class_type = node.get("class_type")
            if not class_type:
                errors.append(f"[{node_id}] missing class_type")
                continue
            inputs = node.get("inputs") or {}

            # Any node carrying a prefix gets it checked, so no save format
            # (SaveAudioAdvanced, SaveAudioMP3, SaveAudioOpus, custom packs) is
            # missed by a hardcoded class list.
            if "filename_prefix" in inputs:
                prefix_errors, prefix_warnings = check_save_prefix(node_id, class_type, inputs)
                errors.extend(prefix_errors)
                warnings.extend(prefix_warnings)

            if object_info is None:
                continue

            if class_type not in object_info:
                errors.append(f"[{node_id}] missing node class: {class_type}")
                continue

            schema = object_info[class_type]
            required = (schema.get("input") or {}).get("required") or {}
            optional = (schema.get("input") or {}).get("optional") or {}
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

                if is_link(value):
                    source_id, slot = value
                    source_outputs = object_info.get(graph[source_id].get("class_type"), {}).get("output") or []
                    if not isinstance(slot, int) or slot >= len(source_outputs):
                        errors.append(
                            f"[{node_id}] {class_type}.{key}: {source_id} has no output {slot} "
                            f"(has {len(source_outputs)})"
                        )
                    continue

                tensor = is_link_only(spec)
                if tensor is not None:
                    errors.append(
                        f"[{node_id}] {class_type}.{key}: expected a link for type {tensor}, "
                        f"got {type(value).__name__}: {value!r}"
                    )
                    continue

                options = combo_options(spec)
                if options is not None and value not in options:
                    if isinstance(value, str) and value.startswith("example."):
                        warnings.append(
                            f"[{node_id}] {class_type}.{key}: placeholder '{value}' is not in the loader options yet"
                        )
                    else:
                        errors.append(f"[{node_id}] {class_type}.{key}: '{value}' not in loader options ({len(options)})")

            # rgthree's loader stores slots as objects instead of links. Its slot
            # names are not in the node schema, so compare against the core LoRA
            # loader's option list.
            if class_type == "Power Lora Loader (rgthree)":
                lora_list = loader_options(object_info, "LoraLoaderModelOnly", "lora_name")
                if lora_list is None:
                    lora_list = loader_options(object_info, "LoraLoader", "lora_name")
                loras = set(lora_list or [])
                for key, value in inputs.items():
                    if not key.startswith("lora_") or not isinstance(value, dict):
                        continue
                    name = value.get("lora")
                    if not name or name == "None" or not value.get("on", True):
                        continue
                    if loras and name not in loras:
                        errors.append(f"[{node_id}] {class_type}.{key}: LoRA not in loader options: {name}")

        mode = "static" if object_info is None else "live"
        print(f"{path}: {len(graph)} nodes, {len(errors)} errors, {len(warnings)} warnings ({mode})")
        for error in errors:
            print("  ERROR  ", error)
        for warning in warnings:
            print("  warn   ", warning)
        if errors or (args.strict and warnings):
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
