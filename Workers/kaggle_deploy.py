"""TITAN AIO — Kaggle Deployment Helper.

Generates and uploads Kaggle notebooks for GPU tasks.

Usage:
    python Workers/kaggle_deploy.py --task video --script "Product review"
    python Workers/kaggle_deploy.py --task lip-sync --face face.jpg --audio voice.wav
    python Workers/kaggle_deploy.py --task image --prompt "Product photo"
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Workers.kaggle_setup import KaggleNotebookGenerator


def deploy_to_kaggle(notebook_path: str, dataset_name: str = ""):
    """Upload notebook to Kaggle using kaggle CLI."""
    try:
        # Check if kaggle CLI is installed
        result = subprocess.run(
            ["kaggle", "--version"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("Kaggle CLI not found. Install with: pip install kaggle")
            print(f"Notebook saved at: {notebook_path}")
            print("Upload manually: https://www.kaggle.com/code/new")
            return

        # Push notebook
        cmd = ["kaggle", "kernels", "push", "-p", str(Path(notebook_path).parent)]
        if dataset_name:
            cmd.extend(["-d", dataset_name])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Notebook uploaded to Kaggle!")
            print(result.stdout)
        else:
            print(f"Upload failed: {result.stderr}")
    except FileNotFoundError:
        print("Kaggle CLI not found. Install with: pip install kaggle")
        print(f"Notebook saved at: {notebook_path}")


def main():
    parser = argparse.ArgumentParser(description="TITAN AIO Kaggle Deployment")
    parser.add_argument("--task", choices=["video", "lip-sync", "image", "lora"], required=True)
    parser.add_argument("--script", default="Product review, person holding power bank")
    parser.add_argument("--model", default="wan-2-2", choices=["wan-2-2", "hunyuan"])
    parser.add_argument("--face", help="Face image for lip sync")
    parser.add_argument("--audio", help="Audio file for lip sync")
    parser.add_argument("--prompt", default="Product photography, white background")
    parser.add_argument("--product-name", default="character", help="Product/character name for LoRA")
    parser.add_argument("--output", default="/tmp/titan_kaggle_notebook.ipynb")
    parser.add_argument("--deploy", action="store_true", help="Upload to Kaggle")
    args = parser.parse_args()

    gen = KaggleNotebookGenerator()

    if args.task == "video":
        notebook = gen.create_video_notebook(
            script=args.script,
            model=args.model,
        )
    elif args.task == "lip-sync":
        notebook = gen.create_lip_sync_notebook(
            face_image=args.face or "",
            audio_path=args.audio or "",
        )
    elif args.task == "image":
        notebook = gen.create_image_notebook(
            prompt=args.prompt,
            model="flux-schnell",
        )
    elif args.task == "lora":
        notebook = gen.create_lora_training_notebook(
            product_name=args.product_name,
            base_model="flux-schnell",
            num_epochs=100,
            learning_rate=1e-4,
            resolution=512,
        )

    gen.save_notebook(notebook, args.output)

    if args.deploy:
        deploy_to_kaggle(args.output)


if __name__ == "__main__":
    main()
