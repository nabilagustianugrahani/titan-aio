"""TITAN AIO — Kaggle T4 Video Generator (Anti-OOM)

T4 Tesla = 16GB VRAM. Wan 2.2 14B = ~14GB in fp16.
Strategy: CPU offload + sequential + attention slicing + VAE tiling

Deploy as Kaggle notebook. Runs on free T4 GPU.

Usage from Titan:
    from Workers.kaggle_video import KaggleVideoWorker
    worker = KaggleVideoWorker()
    result = await worker.generate(script="...", model="wan-2-2")
"""

from __future__ import annotations

import asyncio
import gc
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VideoResult:
    video_path: str
    model: str
    duration_sec: float
    resolution: tuple[int, int]
    success: bool
    error: Optional[str] = None
    frames_generated: int = 0


class KaggleVideoWorker:
    """Video generation worker for Kaggle T4 GPUs.

    Anti-OOM strategy:
    - CPU offload (model parts stay on CPU, moved to GPU on demand)
    - Sequential CPU offload (max savings, slower)
    - Attention slicing (reduce peak VRAM per attention call)
    - VAE slicing + tiling (process latent in chunks)
    - torch.float16 (half precision)
    - Aggressive cleanup after each generation

    Models:
    - wan-2-2: Wan 2.2 T2V 14B (~14GB with offload, fits T4)
    - hunyuan: Hunyuan Video (~12GB with offload, fits T4)
    - wan-lip: Wan 2.2 + Wav2Lip lip sync (sequential, not parallel)
    """

    KAGGLE_CACHE = Path("/kaggle/working/model_cache")
    KAGGLE_OUTPUT = Path("/kaggle/working/titan_output")
    KAGGLE_MODEL = Path("/kaggle/working/models")

    LOCAL_CACHE = Path("/tmp/titan-cache")
    LOCAL_OUTPUT = Path("/tmp/titan-output")
    LOCAL_MODEL = Path("/tmp/titan-models")

    def __init__(self):
        self._is_kaggle = Path("/kaggle").exists()
        if self._is_kaggle:
            self.CACHE_DIR = self.KAGGLE_CACHE
            self.OUTPUT_DIR = self.KAGGLE_OUTPUT
            self.MODEL_DIR = self.KAGGLE_MODEL
        else:
            self.CACHE_DIR = self.LOCAL_CACHE
            self.OUTPUT_DIR = self.LOCAL_OUTPUT
            self.MODEL_DIR = self.LOCAL_MODEL

        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        script: str,
        model: str = "wan-2-2",
        duration_sec: int = 30,
        resolution: tuple[int, int] = (512, 512),
        num_frames: int = 81,
        face_image: Optional[str] = None,
        audio_path: Optional[str] = None,
        use_sequential_offload: bool = True,
    ) -> VideoResult:
        """Generate video on Kaggle T4.

        Args:
            script: Text prompt for video generation
            model: "wan-2-2" | "hunyuan" | "wan-lip"
            duration_sec: Target duration
            resolution: Output resolution (w, h) — 512x512 recommended for T4
            num_frames: Number of frames (81 for ~10s at 8fps)
            face_image: Face image for lip sync (wan-lip mode)
            audio_path: Audio file for lip sync (wan-lip mode)
            use_sequential_offload: Use sequential CPU offload (slower but saves ~4GB VRAM)
        """
        if model == "wan-2-2":
            return await self._generate_wan(script, resolution, num_frames, use_sequential_offload)
        elif model == "hunyuan":
            return await self._generate_hunyuan(script, resolution, num_frames, use_sequential_offload)
        elif model == "wan-lip":
            return await self._generate_wan_lip(script, face_image, audio_path, resolution, use_sequential_offload)
        else:
            return VideoResult(
                video_path="", model=model, duration_sec=0,
                resolution=resolution, success=False,
                error=f"Unknown model: {model}",
            )

    async def _generate_wan(
        self, script: str, resolution: tuple[int, int], num_frames: int,
        use_sequential: bool = True,
    ) -> VideoResult:
        """Generate video using Wan 2.2 on T4 — anti-OOM."""
        output_name = f"wan-{uuid.uuid4().hex[:8]}"
        output_path = self.OUTPUT_DIR / f"{output_name}.mp4"

        # Aggressive memory optimization for T4 16GB
        offload_mode = "sequential" if use_sequential else "model"
        gen_script = f'''
import torch
import gc
import os
os.environ["HF_HOME"] = "{self.CACHE_DIR}"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

print(f"GPU: {{torch.cuda.get_device_name()}}")
print(f"VRAM: {{torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}}GB")
print(f"Free VRAM: {{torch.cuda.mem_get_info()[0] / 1e9:.1f}}GB")

# Clear cache
torch.cuda.empty_cache()
gc.collect()

from diffusers import WanPipeline

print("Loading Wan 2.2 (T4 optimized)...")
pipe = WanPipeline.from_pretrained(
    "Wan-AI/Wan2.2-T2V-14B-Diffusers",
    torch_dtype=torch.float16,
    variant="fp16" if torch.cuda.is_available() else None,
)

# Anti-OOM: CPU offload (model parts stay on CPU, moved to GPU on demand)
if "{offload_mode}" == "sequential":
    print("Using SEQUENTIAL CPU offload (max memory savings, slower)")
    pipe.enable_sequential_cpu_offload()
else:
    print("Using MODEL CPU offload (faster, slightly more VRAM)")
    pipe.enable_model_cpu_offload()

# Anti-OOM: attention slicing (reduce peak VRAM per attention call)
pipe.enable_attention_slicing(1)

# Anti-OOM: VAE slicing + tiling (process latent in chunks)
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()

print(f"VRAM after load: {{torch.cuda.memory_allocated() / 1e9:.2f}}GB allocated")
print(f"Free VRAM: {{torch.cuda.mem_get_info()[0] / 1e9:.1f}}GB")

print(f"Generating {{'{num_frames}'}} frames...")
video = pipe(
    "{script}",
    num_frames={num_frames},
    guidance_scale=5.0,
    num_inference_steps=25,
    width={resolution[0]},
    height={resolution[1]},
).frames[0]

# Save video
import cv2
import numpy as np
out_path = "{output_path}"
h, w = video[0].shape[:2]
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(out_path, fourcc, 8.0, (w, h))
for f in video:
    out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))
out.release()

# Cleanup
del video
del pipe
gc.collect()
torch.cuda.empty_cache()

print(f"DONE: {{out_path}}")
print(f"Final VRAM: {{torch.cuda.memory_allocated() / 1e9:.2f}}GB allocated")
'''
        return await self._run_gen_script(gen_script, "wan-2-2", output_path, resolution)

    async def _generate_hunyuan(
        self, script: str, resolution: tuple[int, int], num_frames: int,
        use_sequential: bool = True,
    ) -> VideoResult:
        """Generate video using Hunyuan Video on T4 — anti-OOM."""
        output_name = f"hunyuan-{uuid.uuid4().hex[:8]}"
        output_path = self.OUTPUT_DIR / f"{output_name}.mp4"

        gen_script = f'''
import torch
import gc
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

print(f"GPU: {{torch.cuda.get_device_name()}}")
print(f"VRAM: {{torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}}GB")

torch.cuda.empty_cache()
gc.collect()

from diffusers import HunyuanVideoPipeline

print("Loading Hunyuan (T4 optimized)...")
pipe = HunyuanVideoPipeline.from_pretrained(
    "hunyuanvideo/HunyuanVideo",
    torch_dtype=torch.bfloat16,
)

if "{offload_mode}" == "sequential":
    pipe.enable_sequential_cpu_offload()
else:
    pipe.enable_model_cpu_offload()

pipe.enable_attention_slicing(1)
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()

print(f"VRAM after load: {{torch.cuda.memory_allocated() / 1e9:.2f}}GB")

print(f"Generating {{'{num_frames}'}} frames...")
video = pipe(
    "{script}",
    num_frames={num_frames},
    guidance_scale=5.0,
    num_inference_steps=30,
    width={resolution[0]},
    height={resolution[1]},
).frames[0]

import cv2
import numpy as np
out_path = "{output_path}"
h, w = video[0].shape[:2]
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(out_path, fourcc, 8.0, (w, h))
for f in video:
    out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))
out.release()

del video
del pipe
gc.collect()
torch.cuda.empty_cache()

print(f"DONE: {{out_path}}")
'''
        return await self._run_gen_script(gen_script, "hunyuan", output_path, resolution)

    async def _generate_wan_lip(
        self, script: str, face_image: Optional[str], audio_path: Optional[str],
        resolution: tuple[int, int], use_sequential: bool = True,
    ) -> VideoResult:
        """Generate video with lip sync — sequential (not parallel) to avoid OOM.

        Step 1: Generate base video with Wan 2.2 (VRAM freed after)
        Step 2: Load Wav2Lip separately (only ~2GB VRAM)
        """
        output_name = f"wanlip-{uuid.uuid4().hex[:8]}"
        output_path = self.OUTPUT_DIR / f"{output_name}.mp4"

        # Step 1: Generate base video
        base_result = await self._generate_wan(script, resolution, num_frames=81, use_sequential=use_sequential)
        if not base_result.success:
            return base_result

        # Step 2: Apply Wav2Lip (separate process, Wan already freed)
        if face_image and audio_path:
            lip_result = await self._apply_wav2lip(
                base_result.video_path, face_image, audio_path, output_path
            )
            if lip_result.success:
                return lip_result
            print(f"Wav2Lip failed, returning base video: {lip_result.error}")

        return base_result

    async def _apply_wav2lip(
        self, video_path: str, face_image: str, audio_path: str, output_path: str
    ) -> VideoResult:
        """Apply Wav2Lip — only ~2GB VRAM, safe for T4."""
        wav2lip_dir = self.MODEL_DIR / "Wav2Lip"
        checkpoint = wav2lip_dir / "wav2lip_gan.pth"

        if not wav2lip_dir.exists() or not checkpoint.exists():
            await self._install_wav2lip(wav2lip_dir)

        if not checkpoint.exists():
            return VideoResult(
                video_path="", model="wav2lip", duration_sec=0,
                resolution=(512, 512), success=False,
                error="Wav2Lip checkpoint not found",
            )

        gen_script = f'''
import torch
import gc
torch.cuda.empty_cache()
gc.collect()

import subprocess
result = subprocess.run([
    "python", "{wav2lip_dir}/inference.py",
    "--checkpoint_path", "{checkpoint}",
    "--face", "{face_image}",
    "--audio", "{audio_path}",
    "--outfile", "{output_path}",
    "--nosmooth",
], capture_output=True, text=True, timeout=120)

torch.cuda.empty_cache()
gc.collect()

if result.returncode != 0:
    print(f"Wav2Lip error: {{result.stderr[:500]}}")
else:
    print(f"DONE: {{output_path}}")
'''
        return await self._run_gen_script(gen_script, "wav2lip", Path(output_path), (512, 512))

    async def _install_wav2lip(self, target_dir: Path):
        """Install Wav2Lip on Kaggle."""
        import subprocess
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/Rudrabha/Wav2Lip", str(target_dir)],
                capture_output=True, timeout=120,
            )
            subprocess.run(
                ["pip", "install", "-r", str(target_dir / "requirements.txt")],
                capture_output=True, timeout=300,
            )
            checkpoint_url = "https://huggingface.co/schirrmacher/wav2lip/resolve/main/wav2lip_gan.pth"
            subprocess.run(
                ["wget", "-q", checkpoint_url, "-O", str(target_dir / "wav2lip_gan.pth")],
                capture_output=True, timeout=120,
            )
            print(f"Wav2Lip installed at {target_dir}")
        except Exception as e:
            print(f"Wav2Lip install failed: {e}")

    async def _run_gen_script(
        self, gen_script: str, model: str, output_path: Path, resolution: tuple[int, int]
    ) -> VideoResult:
        """Run generation script and return result."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", "-c", gen_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)

            if stdout:
                print(stdout.decode())

            if proc.returncode == 0 and output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                return VideoResult(
                    video_path=str(output_path),
                    model=model,
                    duration_sec=size_mb * 0.8,
                    resolution=resolution,
                    success=True,
                    frames_generated=81,
                )
            else:
                error_msg = stderr.decode()[:500] if stderr else "Generation failed"
                if "out of memory" in error_msg.lower() or "oom" in error_msg.lower():
                    error_msg = f"OOM on T4! Try: use_sequential_offload=True, lower resolution, or fewer frames. Original: {error_msg}"
                return VideoResult(
                    video_path="", model=model, duration_sec=0,
                    resolution=resolution, success=False,
                    error=error_msg,
                )
        except asyncio.TimeoutError:
            return VideoResult(
                video_path="", model=model, duration_sec=0,
                resolution=resolution, success=False,
                error=f"{model} timed out (600s limit)",
            )
        except Exception as e:
            return VideoResult(
                video_path="", model=model, duration_sec=0,
                resolution=resolution, success=False,
                error=str(e),
            )


# ── Kaggle Notebook Generator ────────────────────────────────────

def create_kaggle_notebook(
    script: str = "Product review, person holding power bank, close-up shot",
    model: str = "wan-2-2",
    resolution: tuple[int, int] = (512, 512),
    num_frames: int = 81,
) -> dict:
    """Generate Kaggle notebook with anti-OOM optimizations."""
    cells = [
        # Title
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# TITAN AIO — {model.upper()} Video Generator (Anti-OOM)\n",
                f"T4 Tesla 16GB VRAM — optimized for memory efficiency\n",
                f"Script: {script[:60]}..."
            ]
        },
        # Install deps
        {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU"},
            "source": [
                "!pip install -q diffusers transformers accelerate torch\n",
                "!pip install -q opencv-python sentencepiece protobuf\n",
            ],
            "execution_count": None,
            "outputs": []
        },
        # Check GPU + VRAM
        {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU"},
            "source": [
                "import torch, gc\n",
                "print(f'GPU: {torch.cuda.get_device_name()}')\n",
                "total = torch.cuda.get_device_properties(0).total_mem / 1e9\n",
                "free = torch.cuda.mem_get_info()[0] / 1e9\n",
                "print(f'Total VRAM: {total:.1f}GB')\n",
                "print(f'Free VRAM: {free:.1f}GB')\n",
                "print(f'\\n⚠️ T4 has {total:.0f}GB — Wan 2.2 needs ~14GB with offload')\n",
            ],
            "execution_count": None,
            "outputs": []
        },
        # Load model (anti-OOM)
        {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU"},
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
            ],
            "execution_count": None,
            "outputs": []
        },
        # Generate video
        {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU"},
            "source": [
                f"print('Generating {num_frames} frames...')\n",
                f"video = pipe(\n",
                f"    '{script}',\n",
                f"    num_frames={num_frames},\n",
                "    guidance_scale=5.0,\n",
                "    num_inference_steps=25,\n",
                f"    width={resolution[0]},\n",
                f"    height={resolution[1]},\n",
                ").frames[0]\n",
                "\n",
                "print(f'Generated {{len(video)}} frames')\n",
            ],
            "execution_count": None,
            "outputs": []
        },
        # Save video + cleanup
        {
            "cell_type": "code",
            "metadata": {"accelerator": "GPU"},
            "source": [
                "import cv2, numpy as np\n",
                "output_path = '/kaggle/working/titan_video.mp4'\n",
                "\n",
                "h, w = video[0].shape[:2]\n",
                "out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), 8.0, (w, h))\n",
                "for f in video:\n",
                "    out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))\n",
                "out.release()\n",
                "\n",
                "# Cleanup to free VRAM\n",
                "del video\n",
                "del pipe\n",
                "gc.collect()\n",
                "torch.cuda.empty_cache()\n",
                "\n",
                "size_mb = os.path.getsize(output_path) / (1024*1024)\n",
                "print(f'\\n✅ Video saved: {output_path} ({size_mb:.1f} MB)')\n",
                "print(f'VRAM freed: {torch.cuda.mem_get_info()[0] / 1e9:.1f}GB available')\n",
            ],
            "execution_count": None,
            "outputs": []
        },
    ]

    return {
        "cells": cells,
        "metadata": {
            "kaggle": {
                "accelerator": "GPU",
                "dataSources": [],
                "isGpuEnabled": True,
                "isInternetEnabled": True,
                "language": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }


if __name__ == "__main__":
    notebook = create_kaggle_notebook()
    output = Path("/tmp/titan_kaggle_video.ipynb")
    with open(output, "w") as f:
        json.dump(notebook, f, indent=2)
    print(f"Kaggle notebook saved: {output}")
    print("Upload to Kaggle → Enable GPU → Run all cells")
