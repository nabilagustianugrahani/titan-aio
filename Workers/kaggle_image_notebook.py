# TITAN AIO — Image Worker Notebook

# ⚙️ Konfigurasi Worker
import os, sys, json, time, uuid, subprocess
from pathlib import Path

WORKER_ID = f"image-worker-{uuid.uuid4().hex[:8]}"
OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(m):
    with open(f"{OUTPUT_DIR}/worker.log","a") as f: f.write(f"{time.strftime('%H:%M:%S')} {m}\n")
    print(m)

log(f"=== TITAN AIO Image Worker: {WORKER_ID} ===")

# ── 1. Install Dependencies ────────────────────────────────
log("Installing torch + diffusers...")
subprocess.run("pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124", shell=True, timeout=300)
subprocess.run("pip install -q diffusers transformers accelerate sentencepiece redis boto3 pillow", shell=True, timeout=180)
log("Dependencies done")

# ── 2. Check GPU ────────────────────────────────────────────
gpu = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True)
log(f"GPU: {gpu.stdout.strip() if gpu.returncode==0 else 'NONE (CPU mode)'}")

# ── 3. Load Model ────────────────────────────────────────────
log("Loading FLUX.1-schnell...")
from diffusers import FluxPipeline
import torch
pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")
pipe.enable_model_cpu_offload()
log("FLUX model loaded!")

# ── 4. Connect Redis ───────────────────────────────────────
import redis

REDIS_URL = os.environ.get("TITAN_REDIS_URL", "redis://localhost:6379/0")
S3_BUCKET = os.environ.get("TITAN_S3_BUCKET", "titan-assets")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ── 5. Upload to S3 ─────────────────────────────────────────
def upload_to_s3(file_path: str, key: str) -> str:
    import boto3
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ.get("TITAN_S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("TITAN_S3_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("TITAN_S3_SECRET_KEY", "minioadmin"),
    )
    s3.upload_file(file_path, S3_BUCKET, key)
    return f"s3://{S3_BUCKET}/{key}"

# ── 6. Generate Function ────────────────────────────────────
def generate_image(prompt: str, model: str = "flux-schnell") -> dict:
    log(f"Generating: {prompt[:80]}...")
    t0 = time.time()

    image = pipe(
        prompt,
        guidance_scale=3.5,
        num_inference_steps=4 if "schnell" in model else 25,
        width=1024,
        height=1024,
        generator=torch.Generator("cpu").manual_seed(int(time.time()) % 2**31),
    ).images[0]

    file_id = uuid.uuid4().hex[:12]
    local_path = f"{OUTPUT_DIR}/{file_id}.png"
    image.save(local_path)

    s3_url = upload_to_s3(local_path, f"images/{file_id}.png")
    elapsed = int((time.time() - t0) * 1000)

    log(f"Done in {elapsed}ms: {s3_url}")
    return {"image_url": s3_url, "model_used": model, "generation_time_ms": elapsed}

# ── 7. Polling Loop ─────────────────────────────────────────
log(f"Worker {WORKER_ID} ready. Polling queue:image...")

while True:
    job_data = r.blpop("queue:image", timeout=30)
    if job_data is None:
        continue

    try:
        job = json.loads(job_data[1])
        log(f"Got job: {job['job_id']}")
        result = generate_image(job["payload"].get("prompt", ""), job["payload"].get("model", "flux-schnell"))
        result["job_id"] = job["job_id"]
        result["worker_id"] = WORKER_ID
        result["status"] = "completed"
        r.setex(f"result:{job['job_id']}", 3600, json.dumps(result))
        log(f"Job {job['job_id']} completed")
    except Exception as e:
        log(f"Job failed: {e}")
        r.setex(f"result:{job['job_id']}", 3600, json.dumps({"status": "failed", "error": str(e)}))
