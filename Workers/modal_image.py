"""TITAN AIO — Modal SD3.5 Medium Image Generator."""

import modal

app = modal.App("titan-aio-image")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch", "torchvision",
    index_url="https://download.pytorch.org/whl/cu124",
).pip_install(
    "diffusers",
    "transformers",
    "accelerate",
    "sentencepiece",
    "protobuf",
)


@app.function(gpu="T4", timeout=600, image=image, container_idle_timeout=300)
def generate(prompt: str) -> bytes:
    import torch
    from diffusers import StableDiffusion3Pipeline

    print(f"GPU: {torch.cuda.get_device_name()}")
    print("Loading SD3.5 Medium...")

    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-medium",
        torch_dtype=torch.float16,
    )
    pipe.to("cuda")

    print("Generating...")
    img = pipe(
        prompt,
        guidance_scale=4.5,
        num_inference_steps=25,
        width=1024,
        height=1024,
    ).images[0]

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@app.local_entrypoint()
def main():
    prompt = "product photography of premium power bank, white background, studio lighting, 4k quality"
    img_bytes = generate.remote(prompt)
    with open("/tmp/titan_output.png", "wb") as f:
        f.write(img_bytes)
    print(f"✅ Image saved: /tmp/titan_output.png ({len(img_bytes)} bytes)")
