"""TITAN AIO — Kaggle Notebook Generator

Generates ready-to-upload Kaggle notebooks for:
1. Video generation (Wan 2.2 / Hunyuan)
2. Lip sync (Wav2Lip)
3. Image generation (FLUX / SD3.5)

Usage:
    from Workers.kaggle_setup import KaggleNotebookGenerator
    gen = KaggleNotebookGenerator()
    notebook = gen.create_video_notebook(script="...", model="wan-2-2")
    gen.save_notebook(notebook, "/tmp/my_notebook.ipynb")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class KaggleNotebookGenerator:
    """Generate Kaggle notebooks for TITAN AIO GPU tasks."""

    def create_video_notebook(
        self,
        script: str = "Product review, person holding power bank",
        model: str = "wan-2-2",
        resolution: tuple[int, int] = (512, 512),
        num_frames: int = 81,
    ) -> dict:
        """Create a notebook for video generation — anti-OOM for T4."""
        cells = []

        # Title
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# TITAN AIO — {model.upper()} Video Generator (Anti-OOM)\n",
                f"T4 Tesla 16GB VRAM — optimized for memory efficiency\n",
                f"Script: {script[:60]}...\n",
                f"Resolution: {resolution[0]}x{resolution[1]}, Frames: {num_frames}"
            ]
        })

        # Install deps
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "!pip install -q diffusers transformers accelerate torch\n",
                "!pip install -q opencv-python sentencepiece protobuf\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Check GPU + VRAM
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "import torch, gc, os\n",
                "print(f'GPU: {torch.cuda.get_device_name()}')\n",
                "total = torch.cuda.get_device_properties(0).total_mem / 1e9\n",
                "free = torch.cuda.mem_get_info()[0] / 1e9\n",
                "print(f'Total VRAM: {total:.1f}GB')\n",
                "print(f'Free VRAM: {free:.1f}GB')\n",
                "print(f'\\n⚠️ T4 has {total:.0f}GB — Wan 2.2 needs ~14GB with offload')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Load model with anti-OOM
        if model == "wan-2-2":
            cells.append(self._wan_cell_anti_oom(script, resolution, num_frames))
        elif model == "hunyuan":
            cells.append(self._hunyuan_cell_anti_oom(script, resolution, num_frames))

        # Save output
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "import os\n",
                "output_path = '/kaggle/working/titan_video.mp4'\n",
                "if os.path.exists(output_path):\n",
                "    size_mb = os.path.getsize(output_path) / (1024*1024)\n",
                "    print(f'Video saved: {output_path} ({size_mb:.1f} MB)')\n",
                "else:\n",
                "    print('Video generation failed')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        return {
            "cells": cells,
            "metadata": {
                "kaggle": {
                    "accelerator": "GPU T4 x2",
                    "dataSources": [],
                    "isGpuEnabled": True,
                    "isInternetEnabled": True,
                    "language": "python"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 0
        }

    def create_lip_sync_notebook(
        self,
        face_image: str = "",
        audio_path: str = "",
    ) -> dict:
        """Create a notebook for lip sync with Wav2Lip."""
        cells = []

        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TITAN AIO — Lip Sync with Wav2Lip\n",
                f"Face: {face_image or 'Upload face image'}\n",
                f"Audio: {audio_path or 'Upload audio file'}"
            ]
        })

        # Install deps
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "!pip install -q torch torchvision opencv-python\n",
                "!pip install -q librosa soundfile\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Clone Wav2Lip
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "!git clone https://github.com/Rudrabha/Wav2Lip /kaggle/working/Wav2Lip\n",
                "!pip install -r /kaggle/working/Wav2Lip/requirements.txt\n",
                "!wget -q https://huggingface.co/schirrmacher/wav2lip/resolve/main/wav2lip_gan.pth \\\n",
                "    -O /kaggle/working/Wav2Lip/wav2lip_gan.pth\n",
                "print('Wav2Lip ready')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Run lip sync
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "import subprocess\n",
                "\n",
                "# Upload your face image and audio first!\n",
                "face = '/kaggle/working/face.jpg'  # <-- change this\n",
                "audio = '/kaggle/working/audio.wav'  # <-- change this\n",
                "output = '/kaggle/working/lipsync_output.mp4'\n",
                "\n",
                "result = subprocess.run([\n",
                "    'python', '/kaggle/working/Wav2Lip/inference.py',\n",
                "    '--checkpoint_path', '/kaggle/working/Wav2Lip/wav2lip_gan.pth',\n",
                "    '--face', face,\n",
                "    '--audio', audio,\n",
                "    '--outfile', output,\n",
                "    '--nosmooth',\n",
                "], capture_output=True, text=True)\n",
                "\n",
                "if result.returncode == 0:\n",
                "    print(f'Lip sync done: {output}')\n",
                "else:\n",
                "    print(f'Error: {result.stderr[:500]}')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        return {
            "cells": cells,
            "metadata": {
                "kaggle": {
                    "accelerator": "GPU T4 x2",
                    "dataSources": [],
                    "isGpuEnabled": True,
                    "isInternetEnabled": True,
                    "language": "python"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 0
        }

    def create_image_notebook(
        self,
        prompt: str = "Product photography, white background",
        model: str = "flux-schnell",
    ) -> dict:
        """Create a notebook for image generation."""
        cells = []

        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# TITAN AIO — {model.upper()} Image Generator\n",
                f"Prompt: {prompt[:50]}..."
            ]
        })

        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "!pip install -q diffusers transformers accelerate torch\n",
                "!pip install -q sentencepiece protobuf\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        if model == "flux-schnell":
            cells.append({
                "cell_type": "code",
                "metadata": {"accelerator": "GPU T4 x2"},
                "source": [
                    "import torch\n",
                    "from diffusers import FluxPipeline\n",
                    "\n",
                    "pipe = FluxPipeline.from_pretrained(\n",
                    "    'black-forest-labs/FLUX.1-schnell',\n",
                    "    torch_dtype=torch.bfloat16,\n",
                    ")\n",
                    "pipe.to('cuda')\n",
                    "pipe.vae.enable_slicing()\n",
                    "pipe.vae.enable_tiling()\n",
                    "print('FLUX ready')\n",
                    "\n",
                    "img = pipe(\n",
                    f"    '{prompt}',\n",
                    "    guidance_scale=3.5,\n",
                    "    num_inference_steps=4,\n",
                    "    width=1024,\n",
                    "    height=1024,\n",
                    ").images[0]\n",
                    "\n",
                    "img.save('/kaggle/working/titan_image.png')\n",
                    "print('Image saved: /kaggle/working/titan_image.png')\n",
                ],
                "execution_count": None,
                "outputs": []
            })

        return {
            "cells": cells,
            "metadata": {
                "kaggle": {
                    "accelerator": "GPU T4 x2",
                    "dataSources": [],
                    "isGpuEnabled": True,
                    "isInternetEnabled": True,
                    "language": "python"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 0
        }

    def _wan_cell_anti_oom(
        self, script: str, resolution: tuple[int, int], num_frames: int
    ) -> dict:
        """Generate Wan 2.2 notebook cell — anti-OOM for T4."""
        return {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'\n",
                "torch.cuda.empty_cache()\n",
                "gc.collect()\n",
                "\n",
                "from diffusers import WanPipeline\n",
                "\n",
                "print('Loading Wan 2.2 (T4 optimized)...')\n",
                "pipe = WanPipeline.from_pretrained(\n",
                "    'Wan-AI/Wan2.2-T2V-14B-Diffusers',\n",
                "    torch_dtype=torch.float16,\n",
                ")\n",
                "\n",
                "# Anti-OOM: Sequential CPU offload (max memory savings)\n",
                "pipe.enable_sequential_cpu_offload()\n",
                "\n",
                "# Anti-OOM: Attention slicing\n",
                "pipe.enable_attention_slicing(1)\n",
                "\n",
                "# Anti-OOM: VAE slicing + tiling\n",
                "pipe.vae.enable_slicing()\n",
                "pipe.vae.enable_tiling()\n",
                "\n",
                "allocated = torch.cuda.memory_allocated() / 1e9\n",
                "free = torch.cuda.mem_get_info()[0] / 1e9\n",
                "print(f'Model loaded! VRAM: {allocated:.2f}GB allocated, {free:.1f}GB free')\n",
                "\n",
                "print(f'Generating {num_frames} frames...')\n",
                "video = pipe(\n",
                f"    '{script}',\n",
                f"    num_frames={num_frames},\n",
                "    guidance_scale=5.0,\n",
                "    num_inference_steps=25,\n",
                f"    width={resolution[0]},\n",
                f"    height={resolution[1]},\n",
                ").frames[0]\n",
                "\n",
                "import cv2, numpy as np\n",
                "out = cv2.VideoWriter('/kaggle/working/titan_video.mp4',\n",
                "    cv2.VideoWriter_fourcc(*'mp4v'), 8.0, (512, 512))\n",
                "for f in video:\n",
                "    out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))\n",
                "out.release()\n",
                "\n",
                "# Cleanup\n",
                "del video\n",
                "del pipe\n",
                "gc.collect()\n",
                "torch.cuda.empty_cache()\n",
                "\n",
                "size_mb = os.path.getsize('/kaggle/working/titan_video.mp4') / (1024*1024)\n",
                "print(f'✅ Video saved ({size_mb:.1f} MB)')\n",
                "print(f'VRAM freed: {torch.cuda.mem_get_info()[0] / 1e9:.1f}GB available')\n",
            ],
            "execution_count": None,
            "outputs": []
        }

    def _hunyuan_cell_anti_oom(
        self, script: str, resolution: tuple[int, int], num_frames: int
    ) -> dict:
        """Generate Hunyuan notebook cell — anti-OOM for T4."""
        return {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'\n",
                "torch.cuda.empty_cache()\n",
                "gc.collect()\n",
                "\n",
                "from diffusers import HunyuanVideoPipeline\n",
                "\n",
                "print('Loading Hunyuan (T4 optimized)...')\n",
                "pipe = HunyuanVideoPipeline.from_pretrained(\n",
                "    'hunyuanvideo/HunyuanVideo',\n",
                "    torch_dtype=torch.bfloat16,\n",
                ")\n",
                "\n",
                "# Anti-OOM: Sequential CPU offload\n",
                "pipe.enable_sequential_cpu_offload()\n",
                "\n",
                "# Anti-OOM: Attention slicing\n",
                "pipe.enable_attention_slicing(1)\n",
                "\n",
                "# Anti-OOM: VAE slicing + tiling\n",
                "pipe.vae.enable_slicing()\n",
                "pipe.vae.enable_tiling()\n",
                "\n",
                "allocated = torch.cuda.memory_allocated() / 1e9\n",
                "free = torch.cuda.mem_get_info()[0] / 1e9\n",
                "print(f'Model loaded! VRAM: {allocated:.2f}GB allocated, {free:.1f}GB free')\n",
                "\n",
                "print(f'Generating {num_frames} frames...')\n",
                "video = pipe(\n",
                f"    '{script}',\n",
                f"    num_frames={num_frames},\n",
                "    guidance_scale=5.0,\n",
                "    num_inference_steps=30,\n",
                f"    width={resolution[0]},\n",
                f"    height={resolution[1]},\n",
                ").frames[0]\n",
                "\n",
                "import cv2, numpy as np\n",
                "out = cv2.VideoWriter('/kaggle/working/titan_video.mp4',\n",
                "    cv2.VideoWriter_fourcc(*'mp4v'), 8.0, (512, 512))\n",
                "for f in video:\n",
                "    out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))\n",
                "out.release()\n",
                "\n",
                "# Cleanup\n",
                "del video\n",
                "del pipe\n",
                "gc.collect()\n",
                "torch.cuda.empty_cache()\n",
                "\n",
                "size_mb = os.path.getsize('/kaggle/working/titan_video.mp4') / (1024*1024)\n",
                "print(f'✅ Video saved ({size_mb:.1f} MB)')\n",
                "print(f'VRAM freed: {torch.cuda.mem_get_info()[0] / 1e9:.1f}GB available')\n",
            ],
            "execution_count": None,
            "outputs": []
        }

    def save_notebook(self, notebook: dict, path: str):
        """Save notebook to .ipynb file."""
        with open(path, "w") as f:
            json.dump(notebook, f, indent=2)
        print(f"Notebook saved: {path}")
        print("Upload to Kaggle → Enable GPU → Run all cells")
