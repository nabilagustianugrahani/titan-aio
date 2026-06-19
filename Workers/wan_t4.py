import os, time, uuid, torch

print("GPU:", torch.cuda.get_device_name() if torch.cuda.is_available() else "CPU")

OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

from diffusers import WanPipeline

pipe = WanPipeline.from_pretrained(
    "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
    torch_dtype=torch.float16,
)
pipe.enable_model_cpu_offload()
print("Wan 2.2 ready")

video = pipe(
    "Product review of portable power bank, high quality, Indonesian language",
    num_frames=41,
    guidance_scale=5.0,
    num_inference_steps=25,
    width=512,
    height=512,
).frames[0]

fid = uuid.uuid4().hex[:12]
import cv2, numpy as np
p = f"{OUTPUT_DIR}/{fid}.mp4"
h, w = video[0].shape[:2]
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(p, fourcc, 8.0, (w, h))
for f in video:
    out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))
out.release()

print(f"DONE:{fid}.mp4")
print("ALL_DONE")
