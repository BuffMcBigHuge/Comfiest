# COMFY-SETUP — Install ComfyUI and the Comfiest stack

This file is written for an AI agent (or a patient human) setting up a machine from scratch. Follow it
in order. Every command is meant to be run by the agent, with the user's confirmation before large
downloads or package changes.

**Target:** a Linux or Windows machine with an NVIDIA GPU (24 GB class or better) and about **200 GB
of free disk**. AMD, Apple Silicon, and CPU-only setups are not supported by this exact graph set:
the workflows use CUDA `int8_convrot` models, TensorRT depth, and NVIDIA-oriented custom nodes.

**What gets installed**

1. ComfyUI (latest stable) + a Python 3.12 environment.
2. PyTorch built for CUDA 13.0 (required by the `int8_convrot` checkpoints).
3. 17 required custom-node packs (plus 2 optional), including the MiniMax H3 compatibility/acceleration

   nodes.
4. About 185 GB of model files, downloaded from Hugging Face into the right folders.
5. A TensorRT depth engine for the character-replacement workflows.
6. Optionally, the `comfy-mcp` bridge from [`MCP-SETUP.md`](MCP-SETUP.md) so an agent can submit jobs.

Set these two variables for the rest of the guide:

```bash
# Linux/macOS shell
export COMFYUI="$HOME/ComfyUI"
export VENV="$HOME/venvs/comfyui"
```

```powershell
# Windows PowerShell
$env:COMFYUI = "$env:USERPROFILE\ComfyUI"
$env:VENV = "$env:USERPROFILE\venvs\comfyui"
```

---

## 1. Install ComfyUI

### Option A — comfy-cli (recommended)

```bash
python -m venv "$VENV"
# Linux/macOS
source "$VENV/bin/activate"
# Windows PowerShell
# & "$VENV\Scripts\Activate.ps1"

python -m pip install --upgrade pip
pip install comfy-cli

# CUDA 13.0 is the supported path for int8_convrot models.
comfy --skip-prompt install --nvidia --cuda-version 13.0 --version latest
```

`comfy install` clones ComfyUI, installs PyTorch, installs core requirements, and installs
ComfyUI-Manager. Use `comfy which` to confirm the workspace path; it is normally `~/ComfyUI`.

Start it in the background:

```bash
comfy launch --background
```

The web UI is at `http://127.0.0.1:8188`. `comfy logs` shows the captured log.

If CUDA 13.0 is not available for the installed driver, use `--cuda-version 12.9` (or 12.8) and read
the `int8_convrot` fallback note in section 7. A driver update is usually the better fix. For Krea 2,
use a recent ComfyUI build with native Krea 2 support (0.42+; latest master is safest).

### Option B — manual install

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI"
cd "$COMFYUI"
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
```

Start with:

```bash
python main.py --listen 127.0.0.1 --port 8188
```

### Verify

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

Expect a CUDA 13 build and `True`. If it prints a CPU build, stop and reinstall PyTorch before
downloading models.

---

## 2. Install the custom-node packs

From the Comfiest repository root, run the installer with the **same Python** that runs ComfyUI:

```bash
python scripts/install_nodes.py --comfyui "$COMFYUI"
```

The script clones each pack into `ComfyUI/custom_nodes`, installs its `requirements.txt` with pip, and
runs `install.py` where the pack needs it (currently SAM3). It is safe to re-run; existing packs are
updated with `git pull --ff-only`.

Useful flags:

```bash
python scripts/install_nodes.py --comfyui "$COMFYUI" --skip-pip          # clone/update only
python scripts/install_nodes.py --comfyui "$COMFYUI" --skip-installers   # skip install.py
python scripts/install_nodes.py --comfyui "$COMFYUI" --include-optional  # latent upscaler
```

### Packs and what they provide

| Pack                                              | Source                                                             | Comfiest nodes                                                                                                                                           | Notes                                                                                                 |
| ------------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `rgthree-comfy`                                   | <https://github.com/rgthree/rgthree-comfy>                         | `Power Lora Loader (rgthree)`, `Any Switch`                                                                                                              | Core to every H3/TTS graph.                                                                           |
| `ComfyUI-GGUF`                                    | <https://github.com/city96/ComfyUI-GGUF>                           | `CLIPLoaderGGUF`                                                                                                                                         | Loads the Flux Qwen3 GGUF text encoder.                                                               |
| `RES4LYF`                                         | <https://github.com/ClownsharkBatwing/RES4LYF>                     | `ClownSampler_Beta`, `SharkSampler_Beta`, `SharkOptions_Beta`                                                                                            | Flux.2 Klein 4-step branch.                                                                           |
| `was-node-suite-comfyui`                          | <https://github.com/WASasquatch/was-node-suite-comfyui>            | `Text Multiline`, `Seed`                                                                                                                                 | Text and seed widgets used by Krea/Flux/H3.                                                           |
| `ComfyUI-Easy-Use`                                | <https://github.com/yolain/ComfyUI-Easy-Use>                       | `easy seed`                                                                                                                                              | H3 seed control.                                                                                      |
| `comfyui-various`                                 | <https://github.com/jamesWalker55/comfyui-various>                 | `JWInteger`                                                                                                                                              | Integer plumbing in H3.                                                                               |
| `ComfyUI-KJNodes`                                 | <https://github.com/kijai/ComfyUI-KJNodes>                         | `PathchSageAttentionKJ`, `ImageResizeKJv2`, `INTConstant`, `MiniMaxChunkFeedForward`, `MiniMaxH3MemoryEfficientSageAttentionPatch`, `SimpleCalculatorKJ` | Also used for first-frame conditioning.                                                               |
| `ComfyUI-VideoHelperSuite`                        | <https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite>          | `VHS_LoadVideo`, `VHS_VideoCombine`                                                                                                                      | Video input and MP4 output.                                                                           |
| `ComfyUI-Frame-Interpolation` *(optional)*        | <https://github.com/Fannovel16/ComfyUI-Frame-Interpolation>        | RIFE helpers                                                                                                                                             | Not used by the shipped H3 graphs (`FL_RIFE` comes from Fill-Nodes); enable only for other workflows. |
| `ComfyUI-Drama3`                                  | <https://github.com/PedroMarinhoDev/ComfyUI-Drama3>                | `Drama3Loader`, `Drama3CodecLoader`, `Drama3Generate`, `Drama3Decode`, `Drama3EncodeVoice`                                                               | Requires ComfyUI 0.40+.                                                                               |
| `comfyui-krea2edit`                               | <https://github.com/lbouaraba/comfyui-krea2edit>                   | `Krea2EditModelPatch`, `Krea2EditGroundedEncode`                                                                                                         | Krea 2 identity edit.                                                                                 |
| `ComfyUI-ConditioningKrea2Rebalance`              | <https://github.com/TuZZiL/ComfyUI-ConditioningKrea2Rebalance>     | `ConditioningKrea2Rebalance`                                                                                                                             | Krea 2 conditioning taps.                                                                             |
| `ComfyUI-PlagueKind-Nodes`                        | <https://github.com/PlagueKind/ComfyUI-PlagueKind-Nodes>           | `H3AdaLNLoRAFix`, `H3SLAAttention`                                                                                                                       | Required by the H3 variants.                                                                          |
| `ComfyUI_Fill-Nodes`                              | <https://github.com/filliptm/ComfyUI_Fill-Nodes>                   | `FL_RIFE`                                                                                                                                                | Frame interpolation to 48 fps.                                                                        |
| `ComfyUI-Spectrum-MiniMax-H3`                     | <https://github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3>            | `SpectrumApplyMiniMaxH3`                                                                                                                                 | H3 sampler acceleration.                                                                              |
| `ComfyUI-Impact-Pack`                             | <https://github.com/ltdrdata/ComfyUI-Impact-Pack>                  | `ImpactSwitch`                                                                                                                                           | Switch used in the H3 graph.                                                                          |
| `ComfyUI-SAM3`                                    | <https://github.com/PozzettiAndrea/ComfyUI-SAM3>                   | `F`                                                                                                                                                      | Character-replacement workflows.                                                                      |
| `ComfyUI-Depth-Anything-Tensorrt`                 | <https://github.com/yuvraj108c/ComfyUI-Depth-Anything-Tensorrt>    | `DepthAnythingTensorrt`                                                                                                                                  | Character-replacement motion guide; needs TensorRT.                                                   |
| `Comfyui_Minimax_h3_latent_Upscaler` *(optional)* | <https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler> | 2nd-pass latent upscaler                                                                                                                                 | Only for the bypassed 2nd-pass branch.                                                                |

If a clone or pip install fails, install that pack from ComfyUI-Manager by searching its name, then
restart ComfyUI. SAM3 in particular uses the experimental `comfy-env`/pixi installer; Manager is the
more reliable route if `python install.py` fails.

### Restart and check imports

Restart ComfyUI after installing nodes. Watch the console for `IMPORT FAILED` lines:

```bash
comfy stop
comfy launch --background
comfy logs
```

---

## 3. Download the models

Install the Hugging Face client once:

```bash
python -m pip install --upgrade huggingface_hub
```

Then run the downloader from the repository root:

```bash
python scripts/download_models.py --comfyui "$COMFYUI"
```

It downloads into a temporary staging folder inside ComfyUI, moves each file to its final path, skips
files that already exist, and prints the source repo for every file. Use `--dry-run` to see the plan,
`--only krea,flux,h3` to download one family, and `--verify` to check an existing install.

**Gated model.** `black-forest-labs/FLUX.2-klein-9b-fp8` requires accepting the license on Hugging
Face and logging in:

```bash
hf auth login
```

### Required files and Hugging Face sources

Paths are relative to `ComfyUI/`. Sizes are approximate.

| Family | Hugging Face repo | File in repo | Destination | Size |
| - | - | - | - | - |
| Krea | <https://huggingface.co/lodestones/Kroma> | `kroma-v0.3.1-turbo-opd.safetensors` | `models/diffusion_models/krea/kroma-v0.3.1-turbo-opd.safetensors` | 26.3 GB |
| Krea | <https://huggingface.co/Comfy-Org/Krea-2> | `text_encoders/qwen3vl_4b_fp8_scaled.safetensors` | `models/text_encoders/qwen3vl_4b_fp8_scaled.safetensors` | 5.2 GB |
| Krea | <https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged> | `split_files/vae/wan_2.1_vae.safetensors` | `models/vae/wan/Wan2_1_VAE_bf16.safetensors` | 0.3 GB |
| Flux | <https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8> | `flux-2-klein-9b-fp8.safetensors` | `models/diffusion_models/flux/flux-2-klein-9b-fp8.safetensors` | 9.4 GB |
| Flux | <https://huggingface.co/DreamFast/qwen3-8b-heretic> | `gguf/qwen3-8b-heretic-Q6_K.gguf` | `models/text_encoders/Qwen3-8B-heretic.Q6_K.gguf` | 6.7 GB |
| Flux | <https://huggingface.co/Comfy-Org/Flux-2-Klein-9B> | `split_files/vae/flux2-vae.safetensors` | `models/vae/flux2-vae.safetensors` | 0.3 GB |
| MOSS | <https://huggingface.co/lodestones/Kromoss> | `diffusion_models/kromoss_int8_convrot.safetensors` | `models/diffusion_models/moss/kromoss_int8_convrot.safetensors` | 5.4 GB |
| MOSS | <https://huggingface.co/Comfy-Org/MOSS-Image> | `text_encoders/qwen3.5_9b_int8_convrot.safetensors` | `models/text_encoders/qwen3.5_9b_int8_convrot.safetensors` | 9.7 GB |
| MOSS | <https://huggingface.co/lodestones/MOSS-Image-Base-8-steps-dmd> | `lora.safetensors` | `models/loras/moss/MOSS-Image-Base-8-steps-dmd.safetensors` | 1.2 GB |
| YuE2 | <https://huggingface.co/Comfy-Org/YuE2> | `checkpoints/yue2_3b_int8_convrot.safetensors` | `models/checkpoints/yue2_3b_int8_convrot.safetensors` | 4.0 GB |
| YuE2 | <https://huggingface.co/Comfy-Org/YuE2> | `audio_encoders/sheetsage2_bf16.safetensors` | `models/audio_encoders/sheetsage2_bf16.safetensors` | 1.4 GB |
| Music 3 | <https://huggingface.co/Comfy-Org/MiniMax-Music-3> | `diffusion_models/minimax_music3_dit_fp16.safetensors` | `models/diffusion_models/minimax/minimax_music3_dit_fp16.safetensors` | 4.9 GB |
| Music 3 | <https://huggingface.co/Comfy-Org/MiniMax-Music-3> | `text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors` | `models/text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors` | 9.2 GB |
| Music 3 | <https://huggingface.co/Comfy-Org/MiniMax-Music-3> | `vae/minimax_music3_dav.safetensors` | `models/vae/minimax/minimax_music3_dav.safetensors` | 0.2 GB |
| Drama 3 | <https://huggingface.co/PedroMarinhoDev/Drama-3-ComfyUI> | `drama3_fp8experts_bf16.safetensors` | `models/diffusion_models/drama3_fp8experts_bf16.safetensors` | 38.6 GB |
| Drama 3 | <https://huggingface.co/PedroMarinhoDev/Drama-3-ComfyUI> | `drama3_codec.safetensors` | `models/vae/drama3_codec.safetensors` | 1.6 GB |
| H3 | <https://huggingface.co/Kijai/MiniMax-H3-experimental> | `minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors` | `models/diffusion_models/minimax/minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors` | 22.9 GB |
| H3 | <https://huggingface.co/Comfy-Org/MiniMax-H3> | `text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | `models/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27.1 GB |
| H3 | <https://huggingface.co/Comfy-Org/MiniMax-H3> | `vae/minimax_h3_video_vae_fp16.safetensors` | `models/vae/minimax/minimax_h3_video_vae_fp16.safetensors` | 5.2 GB |
| H3 | <https://huggingface.co/Comfy-Org/MiniMax-H3> | `vae/minimax_h3_audio_vae_fp32.safetensors` | `models/vae/minimax/minimax_h3_audio_vae_fp32.safetensors` | 0.6 GB |
| H3 | <https://huggingface.co/Comfy-Org/MiniMax-H3> | `loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | `models/loras/minimax/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | 2.0 GB |
| SAM3 | <https://huggingface.co/Comfy-Org/sam3.1> | `checkpoints/sam3.1_multiplex_fp16.safetensors` | `models/checkpoints/sam3.1_multiplex_fp16.safetensors` | 1.7 GB |
| Optional | <https://huggingface.co/akatz-ai/MiniMax-H3-Character-Swap-LoRA> | `h3_character_swap_v1.5.safetensors` | `models/loras/minimax/h3_character_swap_v1.5.safetensors` | 0.2 GB |

The optional character-swap LoRA is **not** in the shipped char-replace graphs; add it to a scratch
copy if you want stronger identity transfer.

MOSS-Image uses the same `flux2-vae.safetensors` as Flux. The downloader includes it in the `moss`
family too, so `--only moss` works without a separate Flux download.

### Notes on filenames

The workflows load models by exact filename, including subfolders. The downloader performs these
renames for you:

- `wan_2.1_vae.safetensors` → `Wan2_1_VAE_bf16.safetensors` (Krea's VAELoader expects this name).
- `qwen3-8b-heretic-Q6_K.gguf` → `Qwen3-8B-heretic.Q6_K.gguf`.
- MiniMax files keep the `minimax/` subfolder used by the graphs.

If you prefer `hf download` manually, download into a temporary folder and move the file to the
destination above; do not let the repo's own subfolders stack up (for example,
`models/vae/vae/...`).

---

## 4. Build the TensorRT depth engine (character replacement only)

The three `charreplace-*` workflows use `DepthAnythingTensorrt` with:

```text
depth_anything_v2_vitl-fp16.engine
```

Skip this section if you only need images, music, TTS, or plain H3 video.

1. Download the ONNX model from

   <https://huggingface.co/yuvraj108c/Depth-Anything-2-Onnx>:

    The file is 1.3 GB. Put it under `ComfyUI/models/tensorrt/depth-anything/` if you download it
    manually.
2. Build the engine on the same GPU:
   ```bash
    cd "$COMFYUI/custom_nodes/ComfyUI-Depth-Anything-Tensorrt"
    python export_trt.py \
      --onnx-path "$COMFYUI/models/tensorrt/depth-anything/depth_anything_v2_vitl.onnx" \
      --trt-path "$COMFYUI/models/tensorrt/depth-anything/depth_anything_v2_vitl-fp16.engine"
   ```

    Alternatively, use the **Depth Anything Engine Builder** node in ComfyUI: choose v2, size
    `large`, FP16, name the engine `depth_anything_v2_vitl-fp16`, and run it once.

TensorRT engines are tied to the GPU architecture, TensorRT version, and driver. Rebuild after a
major driver or TensorRT upgrade.

---

## 5. Update packages later

Update in this order so ComfyUI's pins win over a node pack's older pins:

```bash
# 1. core ComfyUI
comfy update comfy
# or: cd "$COMFYUI" && git pull && python -m pip install -r requirements.txt

# 2. Python tooling
python -m pip install --upgrade pip setuptools wheel

# 3. custom nodes (git pull + requirements + installers)
python scripts/install_nodes.py --comfyui "$COMFYUI"

# 4. restart
comfy stop
comfy launch --background
```

`comfy node update all` is an alternative to step 3 for packs installed through the Manager, but it
does not run a pack's `install.py`.

Do not upgrade PyTorch casually. The `int8_convrot` checkpoints need the CUDA 13 build; a CPU or CUDA
12 wheel may load but fail at sampling. If you must change it:

```bash
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
```

---

## 6. Verify the install

### File check

```bash
python scripts/download_models.py --comfyui "$COMFYUI" --verify
```

### Node check

```bash
curl http://127.0.0.1:8188/system_stats
```

Then confirm the custom classes exist. URL-encode spaces in class names:

```bash
curl "http://127.0.0.1:8188/object_info/Power%20Lora%20Loader%20(rgthree)"
curl "http://127.0.0.1:8188/object_info/CLIPLoaderGGUF"
curl "http://127.0.0.1:8188/object_info/H3AdaLNLoRAFix"
curl "http://127.0.0.1:8188/object_info/SpectrumApplyMiniMaxH3"
curl "http://127.0.0.1:8188/object_info/DepthAnythingTensorrt"
curl "http://127.0.0.1:8188/object_info/SAM3_Detect"
```

A 200 response with a node definition means the class loaded. A 404 means the pack is missing or
failed to import; check `comfy logs`.

### Workflow conversion check

From the Comfiest repository root:

```bash
comfy run --workflow workflows/text2image-krea.json \
  --print-prompt --host 127.0.0.1 --port 8188
```

Repeat for one workflow per family:

```bash
comfy run --workflow workflows/text2image-fluxklein.json    --print-prompt --host 127.0.0.1 --port 8188
comfy run --workflow workflows/text2image-moss.json         --print-prompt --host 127.0.0.1 --port 8188
comfy run --workflow workflows/minimaxh3/ref2video-minimax-1p.json --print-prompt --host 127.0.0.1 --port 8188
comfy run --workflow workflows/text2music-yue2.json         --print-prompt --host 127.0.0.1 --port 8188
comfy run --workflow workflows/text2music-minimaxmusic3.json --print-prompt --host 127.0.0.1 --port 8188
comfy run --workflow workflows/fishdrama3/tts-fishdrama3-base.json          --print-prompt --host 127.0.0.1 --port 8188
```

A successful conversion returns `"ok": true` and prints the API graph. It does not queue a job.

### First run

1. Stage `example.png`, `example.mp4`, and/or `example.wav` in `ComfyUI/input/` as the chosen workflow
   requires. Every image slot points at `example.png`, every video slot at `example.mp4`, and every
   audio slot at `example.wav`.
2. For Drama 3 clone variants, replace the transcript placeholders so they match the voice clip.
3. Run Krea T2I first; it is the lightest graph.
4. Then run the desired family, one job at a time.

For agent submission, install `comfy-mcp` and register the target with
[`MCP-SETUP.md`](MCP-SETUP.md).

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
| - | - | - |
| `missing_node_type` for `H3AdaLNLoRAFix`, `FL_RIFE`, `SpectrumApplyMiniMaxH3`... | Pack not installed or failed to import | Re-run `scripts/install_nodes.py`; restart; check `comfy logs`. |
| `CLIPLoaderGGUF` missing | ComfyUI-GGUF not installed | Install the pack, restart. |
| `Power Lora Loader (rgthree)` missing | rgthree pack not installed | Install the pack, restart. |
| `int8_convrot` load error, `comfy_kitchen` error, or black output | PyTorch/CUDA mismatch | Install the cu130 PyTorch build; update `comfy-kitchen` via ComfyUI requirements. |
| TensorRT import error | TensorRT not installed or wrong CUDA | Install `tensorrt` for your CUDA; rebuild the engine on the same GPU. |
| `DepthAnythingTensorrt` 404 | Depth pack missing | Install `ComfyUI-Depth-Anything-Tensorrt`; restart. |
| `SAM3_Detect` 404 or SAM3 install fails | SAM3 pack/comfy-env incomplete | Install from Manager, or `pip install -r requirements.txt && python install.py` in the pack. |
| Download 401/403 for FLUX | Gated repo | Accept the license on the model page, `hf auth login`, retry. |
| `hf: command not found` | CLI not installed | `python -m pip install -U huggingface_hub`. |
| CUDA out of memory | 24 GB card + 1.0 MP H3/Drama 3 | Lower H3 to 0.3 MP, run one job at a time, free memory in ComfyUI. |
| Drama 3 stalls or is very slow | Experts loading from system RAM | Use a 128 GB+ RAM host; first run is slower; keep one job. |
| `No module named 'comfy_env'` during SAM3 install | Experimental installer missing | `python -m pip install comfy-env` in the pack, or use Manager. |
| Node works in UI but API run fails | Frontend-only nodes in graph | Use the shipped `api/*.api.json` mirror or strip `Fast Groups Bypasser`/`Label` in `work/scratch`. |

### If you cannot use CUDA 13 / `int8_convrot`

- **Krea, Flux, Drama 3:** these do not depend on `int8_convrot`; only the Krea text encoder is an
fp8 file and works on CUDA 12 builds.
- **MiniMax Music 3:** substitute `minimax_music3_text_encoder_pruned_bf16.safetensors` from the same
Comfy-Org repo for the `int8_convrot` text encoder, and update the `CLIPLoader`.
- **MiniMax H3 text encoder:** `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` is documented by
Comfy-Org as usable without a Blackwell GPU; update the `CLIPLoader` if the int8 file will not load.
- **MiniMax H3 fastvideo model:** there is no drop-in fp8 equivalent of the VSA fastvideo checkpoint
used by these graphs. Either install CUDA 13, or rebuild the H3 graph around the official
`Comfy-Org/MiniMax-H3` `ref2va_pruned_fp8_scaled.safetensors` / `fl2va_pruned_fp8_scaled.safetensors`
files and expect different speed and LoRA behavior.

---

## 8. Model licenses

The repository's MIT license covers its code, workflow JSON, and documentation, **not** the weights.
Check each model card before commercial use:

| Family | License (as published) |
| - | - |
| Krea 2 / Kroma | Krea 2 Community License |
| FLUX.2 Klein | Black Forest Labs license (gated) |
| YuE2 | CC BY-NC 4.0 (non-commercial) |
| MiniMax Music 3 | Apache-2.0 (per Comfy-Org repack) |
| MiniMax H3 | MiniMax H3 Community License |
| Fish Audio Drama 3 | Fish Audio Community License |
| SAM3 | Meta SAM license |
| LightX2V turbo LoRA | See LightX2V model card |

If a use case requires commercial rights, verify the current model card rather than relying on this
table.

---

## 9. Agent checklist

Run in order, stopping to ask the user before the multi-gigabyte steps:

- [ ] Confirm NVIDIA GPU, 24 GB+ VRAM, 200 GB free disk, Python 3.12.
- [ ] Install ComfyUI + CUDA 13 PyTorch (`comfy install --nvidia --cuda-version 13.0 --version latest`).
- [ ] Verify `torch.cuda.is_available()`.
- [ ] Run `python scripts/install_nodes.py --comfyui "$COMFYUI"`.
- [ ] Restart ComfyUI; confirm no `IMPORT FAILED` in `comfy logs`.
- [ ] Run `python scripts/download_models.py --comfyui "$COMFYUI"`.
- [ ] For char-replace: build `depth_anything_v2_vitl-fp16.engine`.
- [ ] Run `python scripts/download_models.py --comfyui "$COMFYUI" --verify`.
- [ ] Confirm key nodes with `/object_info`.
- [ ] Convert one workflow per family with `comfy run --print-prompt`.
- [ ] Run Krea T2I end-to-end and verify the output file size.
- [ ] Register the MCP bridge with [`MCP-SETUP.md`](MCP-SETUP.md) and run the agent smoke test.
