#!/usr/bin/env python3
"""Download the model files Comfiest needs into a ComfyUI tree.

Usage:
    pip install huggingface_hub
    python scripts/download_models.py --comfyui C:/ComfyUI
    python scripts/download_models.py --comfyui ~/ComfyUI --only krea,flux
    python scripts/download_models.py --comfyui ~/ComfyUI --dry-run
    python scripts/download_models.py --comfyui ~/ComfyUI --verify

The script skips files that already exist and prints the source repository for
every download. Gated repositories (FLUX.2 Klein) require `hf auth login` and
accepting the license on huggingface.co first.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# family, repo, remote path, local path (relative to ComfyUI), approx size, optional
MODELS = [
    # Krea 2
    ("krea", "lodestones/Kroma", "kroma-v0.3.1-turbo-opd.safetensors",
     "models/diffusion_models/krea/kroma-v0.3.1-turbo-opd.safetensors", 26.3, False),
    ("krea", "Comfy-Org/Krea-2", "text_encoders/qwen3vl_4b_fp8_scaled.safetensors",
     "models/text_encoders/qwen3vl_4b_fp8_scaled.safetensors", 5.2, False),
    ("krea", "Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/vae/wan_2.1_vae.safetensors",
     "models/vae/wan/Wan2_1_VAE_bf16.safetensors", 0.3, False),

    # Flux.2 Klein
    ("flux", "black-forest-labs/FLUX.2-klein-9b-fp8", "flux-2-klein-9b-fp8.safetensors",
     "models/diffusion_models/flux/flux-2-klein-9b-fp8.safetensors", 9.4, False),
    ("flux", "Comfy-Org/Flux-2-Klein-9B", "split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors",
     "models/text_encoders/qwen_3_8b_fp8mixed.safetensors", 8.7, False),
    ("flux", "Comfy-Org/Flux-2-Klein-9B", "split_files/vae/flux2-vae.safetensors",
     "models/vae/flux2-vae.safetensors", 0.3, False),

    # MOSS-Image (shares flux2-vae with Flux)
    ("moss", "lodestones/Kromoss", "diffusion_models/kromoss_int8_convrot.safetensors",
     "models/diffusion_models/moss/kromoss_int8_convrot.safetensors", 5.4, False),
    ("moss", "Comfy-Org/MOSS-Image", "text_encoders/qwen3.5_9b_int8_convrot.safetensors",
     "models/text_encoders/qwen3.5_9b_int8_convrot.safetensors", 9.7, False),
    ("moss", "lodestones/MOSS-Image-Base-8-steps-dmd", "lora.safetensors",
     "models/loras/moss/MOSS-Image-Base-8-steps-dmd.safetensors", 1.2, False),
    ("moss", "Comfy-Org/MOSS-Image", "vae/flux2-vae.safetensors",
     "models/vae/flux2-vae.safetensors", 0.3, False),

    # YuE2
    ("yue2", "Comfy-Org/YuE2", "checkpoints/yue2_3b_int8_convrot.safetensors",
     "models/checkpoints/yue2_3b_int8_convrot.safetensors", 4.0, False),
    ("yue2", "Comfy-Org/YuE2", "audio_encoders/sheetsage2_bf16.safetensors",
     "models/audio_encoders/sheetsage2_bf16.safetensors", 1.4, False),

    # MiniMax Music 3
    ("music3", "Comfy-Org/MiniMax-Music-3", "diffusion_models/minimax_music3_dit_fp16.safetensors",
     "models/diffusion_models/minimax/minimax_music3_dit_fp16.safetensors", 4.9, False),
    ("music3", "Comfy-Org/MiniMax-Music-3",
     "text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors",
     "models/text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors", 9.2, False),
    ("music3", "Comfy-Org/MiniMax-Music-3", "vae/minimax_music3_dav.safetensors",
     "models/vae/minimax/minimax_music3_dav.safetensors", 0.2, False),

    # Fish Audio Drama 3
    ("drama3", "PedroMarinhoDev/Drama-3-ComfyUI", "drama3_fp8experts_bf16.safetensors",
     "models/diffusion_models/drama3_fp8experts_bf16.safetensors", 38.6, False),
    ("drama3", "PedroMarinhoDev/Drama-3-ComfyUI", "drama3_codec.safetensors",
     "models/vae/drama3_codec.safetensors", 1.6, False),

    # MiniMax H3
    ("h3", "Kijai/MiniMax-H3-experimental",
     "minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors",
     "models/diffusion_models/minimax/minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors",
     22.9, False),
    ("h3", "Comfy-Org/MiniMax-H3", "text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
     "models/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors", 27.1, False),
    ("h3", "Comfy-Org/MiniMax-H3", "vae/minimax_h3_video_vae_fp16.safetensors",
     "models/vae/minimax/minimax_h3_video_vae_fp16.safetensors", 5.2, False),
    ("h3", "Comfy-Org/MiniMax-H3", "vae/minimax_h3_audio_vae_fp32.safetensors",
     "models/vae/minimax/minimax_h3_audio_vae_fp32.safetensors", 0.6, False),
    ("h3", "Comfy-Org/MiniMax-H3", "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
     "models/diffusion_models/minimax/minimax_h3_fl2va_pruned_int8_convrot.safetensors", 21.0, False),
    ("h3", "LBH-123-AI/Minimax_h3_latent_Upscaler",
     "minimax_h3_latent_upscaler_3d_conv_v1/minimax_h3_latent_upscaler_3d_conv_v1_bf16.safetensors",
     "models/latent_upscale_models/minimax_h3_latent_upscaler_3d_bf16.safetensors", 0.7, False),
    ("h3", "Kijai/MiniMax-H3-experimental",
     "loras/minimax_h3_open_regenerate_2k_refiner_rank_16_bf16.safetensors",
     "models/loras/minimax/minimax_h3_open_regenerate_2k_refiner_rank_16_bf16.safetensors", 0.2, False),
    ("h3", "lightx2v/Minimax-h3-Turbo",
     "minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors",
     "models/loras/minimax/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors", 2.0, False),
    ("h3", "RunningHubAI/rh-minimax-h3-lms-v1.0-r64.safetensors-lora",
     "minimax_h3_lms_v1.0_r64.safetensors",
     "models/loras/minimax/minimax_h3_lms_v1.0_r64.safetensors", 1.2, False),
    ("h3", "HAOOOOOOO51/Minimax_h3_fl2v_lightx2v_turbo_4to8step_v0.1-v1.0_768p_v4_step600_dareties_fro095_pruned",
     "minimax_h3_fl2v_lightx2v_turbo_4to8step_v0.1-v1.0_768p_v4_step600_dareties_fro095_pruned.safetensors",
     "models/loras/minimax/minimax_h3_fl2v_lightx2v_v0.1_dareties_v4_step600_comfy_fro_fulladaln.safetensors",
     0.9, False),

    # SAM3 (native image/video mattes + character replacement)
    ("sam3", "Comfy-Org/sam3.1", "checkpoints/sam3.1_multiplex_fp16.safetensors",
     "models/checkpoints/sam3.1_multiplex_fp16.safetensors", 1.7, False),

    # Optional: stronger identity transfer for char-replace
    ("optional", "akatz-ai/MiniMax-H3-Character-Swap-LoRA", "h3_character_swap_v1.5.safetensors",
     "models/loras/minimax/h3_character_swap_v1.5.safetensors", 0.2, True),
]


def human_gb(n: float) -> str:
    return f"{n:.1f} GB"


def selected(family: str, only: set[str] | None, include_optional: bool) -> bool:
    if only is not None and family not in only:
        return False
    if family == "optional" and not include_optional:
        return False
    return True


def verify(comfy: Path, rows) -> int:
    missing = 0
    for family, repo, remote, dest, size, optional in rows:
        p = comfy / dest
        if not p.exists():
            print(f"MISSING {dest}  ({repo}/{remote})")
            missing += 1
        elif p.stat().st_size == 0:
            print(f"EMPTY   {dest}")
            missing += 1
        else:
            print(f"ok      {dest}  ({p.stat().st_size / 1e9:.1f} GB)")
    print(f"\nmissing: {missing}")
    return 1 if missing else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--comfyui", default=str(Path.home() / "ComfyUI"),
                    help="Path to the ComfyUI install (default: ~/ComfyUI)")
    ap.add_argument("--only", default=None,
                    help="Comma-separated families: krea,flux,moss,yue2,music3,drama3,h3,sam3")
    ap.add_argument("--include-optional", action="store_true",
                    help="Also download optional extras (character-swap LoRA)")
    ap.add_argument("--force", action="store_true", help="Re-download existing files")
    ap.add_argument("--dry-run", action="store_true", help="Print the plan only")
    ap.add_argument("--verify", action="store_true", help="Check files and exit")
    args = ap.parse_args()

    comfy = Path(args.comfyui).expanduser().resolve()
    only = set(x.strip().lower() for x in args.only.split(",")) if args.only else None
    rows = [r for r in MODELS if selected(r[0], only, args.include_optional)]

    if not comfy.exists():
        print(f"ERROR: ComfyUI path does not exist: {comfy}", file=sys.stderr)
        return 2

    if args.verify:
        return verify(comfy, rows)

    total = sum(r[4] for r in rows)
    print(f"ComfyUI: {comfy}")
    print(f"files: {len(rows)}  approximate download: {human_gb(total)}\n")
    if args.dry_run:
        for family, repo, remote, dest, size, optional in rows:
            print(f"[{family}] {repo}/{remote}\n    -> {dest}  ({human_gb(size)})")
        return 0

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub is not installed.\n"
              "Run: python -m pip install -U huggingface_hub", file=sys.stderr)
        return 2

    staging = comfy / ".comfiest-downloads"
    staging.mkdir(parents=True, exist_ok=True)
    failed = []

    for family, repo, remote, dest, size, optional in rows:
        target = comfy / dest
        if target.exists() and target.stat().st_size > 0 and not args.force:
            print(f"skip    {dest} (exists)")
            continue
        print(f"\n[{family}] {repo}/{remote}  (~{human_gb(size)})")
        try:
            snapshot_download(
                repo_id=repo,
                allow_patterns=[remote],
                local_dir=str(staging),
            )
            src = staging / remote
            if not src.exists():
                raise FileNotFoundError(f"download did not produce {src}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            shutil.move(str(src), str(target))
            print(f"        -> {dest}  ({target.stat().st_size / 1e9:.1f} GB)")
        except Exception as exc:  # noqa: BLE001 - report and continue
            msg = str(exc)
            print(f"FAILED  {repo}/{remote}: {msg}", file=sys.stderr)
            if "gated" in msg.lower() or "401" in msg:
                print("        Accept the model license on huggingface.co, then run "
                      "`hf auth login` and retry.", file=sys.stderr)
            failed.append((repo, remote, msg))

    # remove empty staging directories and HF metadata
    cache_dir = staging / ".cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
    for p in sorted(staging.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    if staging.exists() and not any(staging.iterdir()):
        staging.rmdir()

    print(f"\ndone. failed: {len(failed)}")
    for repo, remote, msg in failed:
        print(f"  {repo}/{remote}: {msg}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
