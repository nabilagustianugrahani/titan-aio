# TITAN AIO — FLUX.1-schnell Image Generator

import torch, os, uuid, subprocess

print("GPU:", torch.cuda.get_device_name() if torch.cuda.is_available() else "CPU")

OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set HF token via huggingface_hub (not just env var)
HF_TOKEN = os.environ.get("HF_TOKEN", "YOUR_HF_TOKEN_HERE")

from huggingface_hub import login
login(token=HF_TOKEN)

print("HF auth done, loading FLUX...")
from diffusers import FluxPipeline

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.float16,
)
pipe.enable_model_cpu_offload()
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()
print("ready")

for prompt in [
    "product photography of premium power bank, white background, studio lighting, 4k",
    "lifestyle photo of person using portable charger outdoors",
]:
    img = pipe(prompt, guidance_scale=3.5, num_inference_steps=4, width=1024, height=1024).images[0]
    fid = uuid.uuid4().hex[:12]
    img.save(f"{OUTPUT_DIR}/{fid}.png")
    print(f"OK:{fid}")

print("ALL_DONE")
