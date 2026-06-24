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
                "T4 Tesla 16GB VRAM — optimized for memory efficiency\n",
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

    def create_lora_training_notebook(
        self,
        product_name: str = "character",
        base_model: str = "flux-schnell",
        num_epochs: int = 100,
        learning_rate: float = 1e-4,
        resolution: int = 512,
        caption_prefix: str = "photo of sks",
    ) -> dict:
        """Create FLUX LoRA training notebook for Kaggle T4 x2 (32GB).

        T4 x2 gives 32GB VRAM — enough for FLUX LoRA training with:
        - Full precision unet
        - LoRA rank 16-32
        - Gradient checkpointing
        - Mixed precision fp16

        Training data: upload 10-20 images of the character/product.
        Output: .safetensors LoRA file (~10-50MB).
        """
        cells = []

        # Title
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# TITAN AIO — FLUX LoRA Training ({product_name})\n",
                "T4 x2 GPU (32GB VRAM) — Character/Product LoRA\n",
                f"Base: {base_model} | Epochs: {num_epochs} | LR: {learning_rate}\n",
                f"Caption prefix: '{caption_prefix}'\n",
                "\n",
                "**Steps:**\n",
                "1. Upload 10-20 images of your character/product to `/kaggle/input/`\n",
                "2. Run all cells\n",
                "3. Download `.safetensors` from `/kaggle/working/`\n",
            ]
        })

        # Install deps
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Install training deps\n",
                "!pip install -q diffusers transformers accelerate torch\n",
                "!pip install -q bitsandbytes peft kohya-ss\n",
                "!pip install -q captionizer pillow\n",
                "\n",
                "# Verify T4 x2\n",
                "import torch\n",
                "if torch.cuda.is_available():\n",
                "    gpu = torch.cuda.get_device_name(0)\n",
                "    vram = torch.cuda.get_device_properties(0).total_mem / 1e9\n",
                "    print(f'GPU: {gpu}')\n",
                "    print(f'VRAM: {vram:.1f}GB')\n",
                "    gpus = torch.cuda.device_count()\n",
                "    print(f'GPU count: {gpus}')\n",
                "    total = sum(torch.cuda.get_device_properties(i).total_mem for i in range(gpus)) / 1e9\n",
                "    print(f'Total VRAM: {total:.1f}GB')\n",
                "else:\n",
                "    print('❌ No GPU! Enable T4 x2 in Kaggle settings')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Setup training data
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "import os, glob, json\n",
                "from pathlib import Path\n",
                "\n",
                "# Training data directory\n",
                "TRAIN_DIR = '/kaggle/input/training-images'\n",
                "WORK_DIR = '/kaggle/working'\n",
                "OUTPUT_DIR = f'{WORK_DIR}/lora-output'\n",
                "os.makedirs(OUTPUT_DIR, exist_ok=True)\n",
                "\n",
                "# Find training images\n",
                "extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']\n",
                "images = []\n",
                "for ext in extensions:\n",
                "    images.extend(glob.glob(os.path.join(TRAIN_DIR, ext)))\n",
                "\n",
                "if not images:\n",
                "    # Try subdirectories\n",
                "    for ext in extensions:\n",
                "        images.extend(glob.glob(os.path.join(TRAIN_DIR, '**', ext), recursive=True))\n",
                "\n",
                "print(f'Found {len(images)} training images')\n",
                "if len(images) < 5:\n",
                "    print('⚠️  Need at least 5-20 images for good results')\n",
                "    print(f'Upload images to: {TRAIN_DIR}')\n",
                "else:\n",
                "    print(f'✅ Ready to train with {len(images)} images')\n",
                "    for img in images[:5]:\n",
                "        print(f'  - {os.path.basename(img)}')\n",
                "    if len(images) > 5:\n",
                "        print(f'  ... and {len(images) - 5} more')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Auto-caption images
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Auto-caption training images using BLIP\n",
                "from transformers import BlipProcessor, BlipForConditionalGeneration\n",
                "from PIL import Image\n",
                "import torch\n",
                "\n",
                "print('Loading caption model...')\n",
                "processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')\n",
                "cap_model = BlipForConditionalGeneration.from_pretrained(\n",
                "    'Salesforce/blip-image-captioning-base', torch_dtype=torch.float16\n",
                ").to('cuda')\n",
                "\n",
                "captions = []\n",
                "for i, img_path in enumerate(images):\n",
                "    img = Image.open(img_path).convert('RGB')\n",
                "    inputs = processor(img, return_tensors='pt').to('cuda', torch.float16)\n",
                "    out = cap_model.generate(**inputs, max_length=50)\n",
                "    caption = processor.decode(out[0], skip_special_tokens=True)\n",
                "    # Add prefix for LoRA trigger\n",
                "    full_caption = f'{caption_prefix} {caption}'\n",
                "    captions.append({'image': img_path, 'caption': full_caption})\n",
                "    if i < 3:\n",
                "        print(f'  [{i+1}] {os.path.basename(img_path)}: {full_caption}')\n",
                "\n",
                "print(f'\\n✅ Captioned {len(captions)} images')\n",
                "\n",
                "# Save captions\n",
                "with open(f'{WORK_DIR}/captions.json', 'w') as f:\n",
                "    json.dump(captions, f, indent=2)\n",
                "\n",
                "# Cleanup caption model\n",
                "del cap_model\n",
                "del processor\n",
                "torch.cuda.empty_cache()\n",
                "import gc; gc.collect()\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Train LoRA
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# FLUX LoRA Training — T4 x2 optimized\n",
                "import torch, os, gc, json\n",
                "from diffusers import FluxPipeline\n",
                "from peft import LoraConfig, get_peft_model\n",
                "from torch.utils.data import Dataset, DataLoader\n",
                "from PIL import Image\n",
                "\n",
                "print('Loading FLUX pipeline...')\n",
                "pipe = FluxPipeline.from_pretrained(\n",
                "    'black-forest-labs/FLUX.1-schnell',\n",
                "    torch_dtype=torch.float16,\n",
                ")\n",
                "\n",
                "# Memory optimizations for T4 x2\n",
                "pipe.enable_model_cpu_offload()\n",
                "pipe.enable_attention_slicing(1)\n",
                "pipe.vae.enable_slicing()\n",
                "pipe.vae.enable_tiling()\n",
                "\n",
                "vram = torch.cuda.mem_get_info()[0] / 1e9\n",
                "print(f'FLUX loaded! Free VRAM: {vram:.1f}GB')\n",
                "\n",
                "# LoRA config\n",
                "lora_config = LoraConfig(\n",
                "    r=16,                          # LoRA rank (16 good for T4)\n",
                "    lora_alpha=32,                 # alpha = 2 * rank\n",
                "    target_modules=[\n",
                "        'to_q', 'to_k', 'to_v', 'to_out.0',  # attention\n",
                "        'proj_in', 'proj_out',                    # projection\n",
                "    ],\n",
                "    lora_dropout=0.05,\n",
                "    bias='none',\n",
                ")\n",
                "\n",
                "# Apply LoRA to UNet\n",
                "pipe.transformer = get_peft_model(pipe.transformer, lora_config)\n",
                "pipe.transformer.print_trainable_parameters()\n",
                "\n",
                "print('\\nStarting training...')\n",
                "print(f'Epochs: {num_epochs} | LR: {learning_rate} | Rank: 16')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Training loop
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Training loop\n",
                "import torch\n",
                "from torch.optim import AdamW\n",
                "from torch.cuda.amp import autocast\n",
                "from pathlib import Path\n",
                "\n",
                "captions = json.load(open(f'{WORK_DIR}/captions.json'))\n",
                "\n",
                "optimizer = AdamW(\n",
                "    pipe.transformer.parameters(),\n",
                "    lr={learning_rate},\n",
                "    weight_decay=0.01,\n",
                ")\n",
                "\n",
                "losses = []\n",
                "for epoch in range({num_epochs}):\n",
                "    pipe.transformer.train()\n",
                "    epoch_loss = 0\n",
                "\n",
                "    for i, item in enumerate(captions):\n",
                "        # Load and preprocess image\n",
                "        img = Image.open(item['image']).convert('RGB').resize(({resolution}, {resolution}))\n",
                "        img_tensor = torch.tensor(list(img.getdata())).float().view(1, 3, {resolution}, {resolution}) / 127.5 - 1\n",
                "        img_tensor = img_tensor.to('cuda')\n",
                "\n",
                "        # Encode to latent\n",
                "        with torch.no_grad():\n",
                "            latents = pipe.vae.encode(img_tensor).latent_dist.sample()\n",
                "            latents = latents * pipe.vae.config.scaling_factor\n",
                "\n",
                "        # Forward pass with LoRA\n",
                "        with autocast(dtype=torch.float16):\n",
                "            noise = torch.randn_like(latents)\n",
                "            timesteps = torch.tensor([500], device='cuda')\n",
                "            text_emb = pipe.text_encoder(\n",
                "                pipe.tokenizer(\n",
                "                    item['caption'],\n",
                "                    return_tensors='pt',\n",
                "                    padding=True,\n",
                "                    truncation=True,\n",
                "                    max_length=512,\n",
                "                ).input_ids.to('cuda')\n",
                "            )\n",
                "            model_pred = pipe.transformer(\n",
                "                latents, timesteps, text_emb\n",
                "            ).sample\n",
                "            loss = torch.nn.functional.mse_loss(model_pred, noise)\n",
                "\n",
                "        optimizer.zero_grad()\n",
                "        loss.backward()\n",
                "        optimizer.step()\n",
                "\n",
                "        epoch_loss += loss.item()\n",
                "        del img_tensor, latents, noise, model_pred\n",
                "        torch.cuda.empty_cache()\n",
                "\n",
                "    avg_loss = epoch_loss / len(captions)\n",
                "    losses.append(avg_loss)\n",
                "\n",
                "    if (epoch + 1) % 10 == 0:\n",
                "        print(f'Epoch {{epoch+1}}/{{num_epochs}} | Loss: {{avg_loss:.4f}}')\n",
                "\n",
                "print(f'\\n✅ Training complete! Final loss: {{losses[-1]:.4f}}')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Save LoRA
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Save LoRA weights as .safetensors\n",
                "lora_output = f'{WORK_DIR}/{product_name}_lora.safetensors'\n",
                "\n",
                "# Extract and save LoRA state dict\n",
                "lora_state = {}\n",
                "for name, param in pipe.transformer.named_parameters():\n",
                "    if 'lora' in name:\n",
                "        lora_state[name] = param.cpu().float()\n",
                "\n",
                "torch.save(lora_state, lora_output)\n",
                "size_mb = os.path.getsize(lora_output) / (1024*1024)\n",
                "print(f'✅ LoRA saved: {lora_output} ({size_mb:.1f}MB)')\n",
                "print(f'Trainable params: {len(lora_state)} tensors')\n",
                "\n",
                "# Also save training metadata\n",
                "metadata = {\n",
                "    'product_name': '{product_name}',\n",
                "    'base_model': '{base_model}',\n",
                "    'caption_prefix': '{caption_prefix}',\n",
                "    'epochs': {num_epochs},\n",
                "    'learning_rate': {learning_rate},\n",
                "    'resolution': {resolution},\n",
                "    'lora_rank': 16,\n",
                "    'training_images': len(captions),\n",
                "    'final_loss': losses[-1] if losses else 0,\n",
                "    'file_size_mb': round(size_mb, 1),\n",
                "}\n",
                "with open(f'{WORK_DIR}/{product_name}_lora_meta.json', 'w') as f:\n",
                "    json.dump(metadata, f, indent=2)\n",
                "\n",
                "# Plot loss curve\n",
                "import matplotlib.pyplot as plt\n",
                "plt.figure(figsize=(8, 4))\n",
                "plt.plot(losses)\n",
                "plt.xlabel('Epoch')\n",
                "plt.ylabel('Loss')\n",
                "plt.title('LoRA Training Loss')\n",
                "plt.savefig(f'{WORK_DIR}/loss_curve.png')\n",
                "plt.show()\n",
                "\n",
                "print('\\nFiles ready for download:')\n",
                "print(f'  1. {lora_output} (LoRA weights)')\n",
                "print(f'  2. {WORK_DIR}/{product_name}_lora_meta.json (metadata)')\n",
                "print(f'  3. {WORK_DIR}/loss_curve.png (loss plot)')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Test inference
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Test inference with trained LoRA\n",
                "import torch\n",
                "from diffusers import FluxPipeline\n",
                "\n",
                "print('Testing inference with trained LoRA...')\n",
                "pipe = FluxPipeline.from_pretrained(\n",
                "    'black-forest-labs/FLUX.1-schnell',\n",
                "    torch_dtype=torch.float16,\n",
                ")\n",
                "pipe.enable_model_cpu_offload()\n",
                "\n",
                "# Load LoRA weights\n",
                "lora_state = torch.load('{WORK_DIR}/{product_name}_lora.safetensors', map_location='cpu')\n",
                "pipe.transformer.load_state_dict(lora_state, strict=False)\n",
                "print('LoRA loaded!')\n",
                "\n",
                "# Generate test image\n",
                "prompt = '{caption_prefix} {product_name} product photo, clean background, professional lighting'\n",
                "img = pipe(\n",
                "    prompt,\n",
                "    guidance_scale=3.5,\n",
                "    num_inference_steps=4,\n",
                "    width={resolution},\n",
                "    height={resolution},\n",
                ").images[0]\n",
                "\n",
                "output_path = f'{WORK_DIR}/{product_name}_test.png'\n",
                "img.save(output_path)\n",
                "print(f'✅ Test image: {output_path}')\n",
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

    def create_voice_cloning_notebook(
        self,
        speaker_name: str = "speaker",
        language: str = "id",
    ) -> dict:
        """Create Coqui XTTS v2 voice cloning notebook for Kaggle T4 x2.

        Upload 5-20 short audio clips → trains voice clone → saves .pth.

        Usage:
            gen = KaggleNotebookGenerator()
            notebook = gen.create_voice_cloning_notebook("budi")
            gen.save_notebook(notebook, "/tmp/voice_clone.ipynb")
        """
        cells = []

        # Title
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# TITAN AIO — Voice Cloning ({speaker_name})\n",
                f"Coqui XTTS v2 on Kaggle T4 x2 (32GB VRAM)\n",
                f"Language: {language}\n",
                "\n",
                "**Steps:**\n",
                "1. Upload 5-20 short audio clips (.wav) to `/kaggle/input/audio/`\n",
                "2. Run all cells\n",
                "3. Download speaker `.pth` from `/kaggle/working/`\n",
            ]
        })

        # Install deps
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Install Coqui TTS\n",
                "!pip install -q TTS torch torchaudio\n",
                "!pip install -q soundfile librosa\n",
                "\n",
                "import torch, os, glob, json\n",
                "from pathlib import Path\n",
                "\n",
                "print(f'GPU: {torch.cuda.get_device_name(0)}')\n",
                "print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}GB')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Find audio files
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Find audio files\n",
                "AUDIO_DIR = '/kaggle/input/audio'\n",
                "extensions = ['*.wav', '*.mp3', '*.m4a', '*.flac', '*.ogg']\n",
                "audio_files = []\n",
                "for ext in extensions:\n",
                "    audio_files.extend(glob.glob(os.path.join(AUDIO_DIR, '**', ext), recursive=True))\n",
                "\n",
                "print(f'Found {len(audio_files)} audio files')\n",
                "if len(audio_files) < 3:\n",
                "    print('⚠️ Need at least 3-20 audio clips (5-30 seconds each)')\n",
                "    print(f'Upload audio to: {AUDIO_DIR}')\n",
                "else:\n",
                "    for f in audio_files[:5]:\n",
                "        print(f'  - {os.path.basename(f)}')\n",
                "    if len(audio_files) > 5:\n",
                "        print(f'  ... and {len(audio_files)-5} more')\n",
                "\n",
                "# Check sample rates\n",
                "import librosa\n",
                "for f in audio_files[:3]:\n",
                "    y, sr = librosa.load(f, sr=None)\n",
                "    dur = len(y) / sr\n",
                "    print(f'  {os.path.basename(f)}: {dur:.1f}s @ {sr}Hz')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Train voice clone
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Train XTTS v2 voice clone\n",
                "from TTS.tts.configs.xtts_config import XttsConfig\n",
                "from TTS.tts.models.xtts import Xtts\n",
                "from TTS.utils.audio import AudioProcessor\n",
                "\n",
                "print('Loading Coqui XTTS v2...')\n",
                "model = Xtts.init_from_config(XttsConfig())\n",
                "model.load_checkpoint(\n",
                "    config='',\n",
                "    checkpoint_dir='/kaggle/working/xtts',\n",
                "    eval=True,\n",
                ")\n",
                "model.cuda()\n",
                "\n",
                "# Fine-tune on speaker audio\n",
                "print(f'Fine-tuning on {len(audio_files)} audio files...')\n",
                "model.fine_tune(\n",
                "    audio_files=audio_files,\n",
                "    language='{language}',\n",
                "    output_path=f'/kaggle/working/{speaker_name}.pth',\n",
                "    num_epochs=50,\n",
                "    batch_size=2,\n",
                "    learning_rate=5e-5,\n",
                ")\n",
                "\n",
                "print('✅ Voice clone trained!')\n",
            ],
            "execution_count": None,
            "outputs": []
        })

        # Test inference
        cells.append({
            "cell_type": "code",
            "metadata": {"accelerator": "GPU T4 x2"},
            "source": [
                "# Test cloned voice\n",
                "print('Testing cloned voice...')\n",
                "test_text = 'Halo, selamat datang di TITAN AIO! Produk ini recommended banget!'\n",
                "\n",
                "output = model.tts(\n",
                "    text=test_text,\n",
                "    speaker_audio_path=audio_files[0],\n",
                "    language='{language}',\n",
                ")\n",
                "\n",
                "import scipy.io.wavfile as wav\n",
                "output_path = '/kaggle/working/test_output.wav'\n",
                "wav.write(output_path, 24000, output)\n",
                "\n",
                "import IPython.display as ipd\n",
                "ipd.display(ipd.Audio(output_path))\n",
                "\n",
                "print(f'✅ Test output: {output_path}')\n",
                "print(f'\\nFiles ready:')\n",
                "print(f'  1. /kaggle/working/{speaker_name}.pth (clone checkpoint)')\n",
                "print(f'  2. {output_path} (test audio)')\n",
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

    def save_notebook(self, notebook: dict, path: str):
        """Save notebook to .ipynb file."""
        with open(path, "w") as f:
            json.dump(notebook, f, indent=2)
        print(f"Notebook saved: {path}")
        print("Upload to Kaggle → Enable GPU → Run all cells")
