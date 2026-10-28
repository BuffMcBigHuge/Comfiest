#!/usr/bin/env python3
"""Install or update the ComfyUI custom-node packs used by Comfiest.

Run this with the SAME Python interpreter that runs ComfyUI, after ComfyUI's own
requirements are installed:

    python scripts/install_nodes.py --comfyui C:/ComfyUI
    python scripts/install_nodes.py --comfyui C:/ComfyUI --skip-pip
    python scripts/install_nodes.py --comfyui C:/ComfyUI --include-optional

The script clones each pack into ComfyUI/custom_nodes, installs its
requirements.txt with pip, and runs install.py where a pack needs it (SAM3).
Restart ComfyUI after it finishes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# name, repo URL, needs install.py, optional
NODES = [
    ("rgthree-comfy", "https://github.com/rgthree/rgthree-comfy.git", False, False),
    ("ComfyUI-GGUF", "https://github.com/city96/ComfyUI-GGUF.git", False, False),
    ("RES4LYF", "https://github.com/ClownsharkBatwing/RES4LYF.git", False, False),
    ("was-node-suite-comfyui", "https://github.com/WASasquatch/was-node-suite-comfyui.git", False, False),
    ("ComfyUI-Easy-Use", "https://github.com/yolain/ComfyUI-Easy-Use.git", False, False),
    ("comfyui-various", "https://github.com/jamesWalker55/comfyui-various.git", False, False),
    ("ComfyUI-KJNodes", "https://github.com/kijai/ComfyUI-KJNodes.git", False, False),
    ("ComfyUI-VideoHelperSuite", "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git", False, False),
    ("ComfyUI-Frame-Interpolation", "https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git", False, True),
    ("ComfyUI-Drama3", "https://github.com/PedroMarinhoDev/ComfyUI-Drama3.git", False, False),
    ("comfyui-krea2edit", "https://github.com/lbouaraba/comfyui-krea2edit.git", False, False),
    ("ComfyUI-ConditioningKrea2Rebalance",
     "https://github.com/TuZZiL/ComfyUI-ConditioningKrea2Rebalance.git", False, False),
    ("ComfyUI-PlagueKind-Nodes", "https://github.com/PlagueKind/ComfyUI-PlagueKind-Nodes.git", False, False),
    ("ComfyUI_Fill-Nodes", "https://github.com/filliptm/ComfyUI_Fill-Nodes.git", False, False),
    ("ComfyUI-Spectrum-MiniMax-H3",
     "https://github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3.git", False, False),
    ("ComfyUI-Impact-Pack", "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git", False, False),
    ("ComfyUI-Depth-Anything-Tensorrt",
     "https://github.com/yuvraj108c/ComfyUI-Depth-Anything-Tensorrt.git", False, False),
    ("ComfyUI-SAM3", "https://github.com/PozzettiAndrea/ComfyUI-SAM3.git", True, False),
    ("Comfyui_Minimax_h3_latent_Upscaler",
     "https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler.git", False, True),
]


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    print("  $", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"  WARNING: command failed ({exc.returncode}); continuing", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--comfyui", default=str(Path.home() / "ComfyUI"))
    ap.add_argument("--skip-pip", action="store_true", help="Do not install requirements.txt")
    ap.add_argument("--skip-installers", action="store_true", help="Do not run install.py")
    ap.add_argument("--no-update", action="store_true", help="Do not git pull existing packs")
    ap.add_argument("--include-optional", action="store_true")
    args = ap.parse_args()

    comfy = Path(args.comfyui).expanduser().resolve()
    nodes_dir = comfy / "custom_nodes"
    if not nodes_dir.exists():
        print(f"ERROR: {nodes_dir} does not exist; install ComfyUI first.", file=sys.stderr)
        return 2

    selected = [n for n in NODES if args.include_optional or not n[3]]
    ok = 0
    failed = []

    for name, url, installer, optional in selected:
        dest = nodes_dir / name
        print(f"\n== {name} ==")
        try:
            if dest.exists():
                if args.no_update:
                    print("  exists; skipping update")
                else:
                    print("  exists; git pull --ff-only")
                    run(["git", "pull", "--ff-only"], cwd=dest)
            else:
                run(["git", "clone", "--depth", "1", url, str(dest)])
            if not dest.exists():
                raise FileNotFoundError("clone did not create the directory")

            req = dest / "requirements.txt"
            if req.exists() and not args.skip_pip:
                print("  installing requirements")
                run([sys.executable, "-m", "pip", "install", "-r", str(req)], cwd=dest)

            inst = dest / "install.py"
            if installer and inst.exists() and not args.skip_installers:
                print("  running install.py")
                run([sys.executable, str(inst)], cwd=dest)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}", file=sys.stderr)
            failed.append(name)

    print(f"\ninstalled/updated: {ok}/{len(selected)}")
    if failed:
        print("failed: " + ", ".join(failed))
        print("Restart ComfyUI and check the console for import errors.")
        return 1
    print("Restart ComfyUI, then verify node classes with /object_info.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
