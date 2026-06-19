"""TITAN AIO — Modal A100 FLUX Image Generator
Deploy: modal deploy Workers/modal_a100.py
Run:    modal run Workers/modal_a100.py
"""

import modal

app = modal.App("titan-aio-flux")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "accelerate",
    "sentencepiece",
    "huggingface-hub",
)


@app.function(
    gpu="A100",
    timeout=900,
    image=image,
    secrets=[modal.Secret.from_name("titan-hf-token")],
)
def generate(prompt: str) -> bytes:
    import os, torch, io
    from huggingface_hub import login
    from diffusers import FluxPipeline

    login(token=os.environ["HF_TOKEN"])
    print(f"GPU: {torch.cuda.get_device_name()}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")

    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-schnell",
        torch_dtype=torch.bfloat16,
    )
    pipe.to("cuda")
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()
    print("FLUX ready")

    img = pipe(
        prompt,
        guidance_scale=3.5,
        num_inference_steps=4,
        width=1024,
        height=1024,
    ).images[0]

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    print(f"DONE ({len(buf.getvalue()) // 1024} KB)")
    return buf.getvalue()


@app.function(
    gpu="A100",
    timeout=900,
    image=image,
    secrets=[modal.Secret.from_name("titan-hf-token")],
)
def generate_video(script: str) -> bytes:
    import torch, os, io, uuid, cv2, numpy as np
    from diffusers import WanPipeline

    print(f"GPU: {torch.cuda.get_device_name()}")
    from huggingface_hub import login
    login(token=os.environ["HF_TOKEN"])
    pipe = WanPipeline.from_pretrained(
        "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
        torch_dtype=torch.float16,
    )
    pipe.to("cuda")
    pipe.enable_model_cpu_offload()
    print("Wan ready")

    video = pipe(
        script,
        num_frames=41,
        guidance_scale=5.0,
        num_inference_steps=25,
        width=512,
        height=512,
    ).frames[0]

    out_path = f"/tmp/{uuid.uuid4().hex[:12]}.mp4"
    h, w = video[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, 8.0, (w, h))
    for f in video:
        out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))
    out.release()

    with open(out_path, "rb") as f:
        return f.read()


@app.function(
    gpu="A100",
    timeout=900,
    image=image,
    secrets=[modal.Secret.from_name("titan-hf-token")],
)
def batch_generate(prompts: list[str]) -> list[bytes]:
    """Generate multiple images in one session — lebih hemat."""
    import os, torch, io
    from huggingface_hub import login
    from diffusers import FluxPipeline

    login(token=os.environ["HF_TOKEN"])
    print(f"GPU: {torch.cuda.get_device_name()}")

    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-schnell",
        torch_dtype=torch.bfloat16,
    )
    pipe.to("cuda")
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()

    results = []
    for prompt in prompts:
        img = pipe(
            prompt,
            guidance_scale=3.5,
            num_inference_steps=4,
            width=1024,
            height=1024,
        ).images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        results.append(buf.getvalue())
        print(f"  ✅ {prompt[:50]}... ({len(buf.getvalue()) // 1024} KB)")

    return results


@app.local_entrypoint()
def main():
    prompt = "product photography of premium power bank, white background, studio lighting, 4k quality"
    print(f"Generating: {prompt}")
    img_bytes = generate.remote(prompt)
    with open("/tmp/titan_flux.png", "wb") as f:
        f.write(img_bytes)
    print(f"✅ Saved: /tmp/titan_flux.png ({len(img_bytes) // 1024} KB)")
