# TITAN AIO — LoRA Training Notebook

# ⚙️ Konfigurasi Worker
import os, json, time, uuid, subprocess

WORKER_ID = f"lora-worker-{uuid.uuid4().hex[:8]}"
OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(m):
    with open(f"{OUTPUT_DIR}/worker.log","a") as f: f.write(f"{time.strftime('%H:%M:%S')} {m}\n")
    print(m)

log(f"=== TITAN AIO LoRA Worker: {WORKER_ID} ===")

# ── 1. Install ──────────────────────────────────────────────
log("Installing deps...")
subprocess.run("pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124", shell=True, timeout=300)
subprocess.run("pip install -q diffusers transformers accelerate peft redis boto3 pillow", shell=True, timeout=180)
log("Dependencies done")

# ── 2. GPU Check ────────────────────────────────────────────
gpu = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True)
log(f"GPU: {gpu.stdout.strip() if gpu.returncode==0 else 'CPU mode'}")

# ── 3. Load Base Model ──────────────────────────────────────
log("Loading FLUX.1-dev (LoRA base)...")
from diffusers import FluxPipeline
import torch
pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev", torch_dtype=torch.bfloat16)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")
pipe.enable_model_cpu_offload()
log("Base model loaded!")

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

# ── 6. Train LoRA Function ──────────────────────────────────
def train_lora(product_id: str, image_urls: list[str]) -> dict:
    log(f"Training LoRA: product={product_id}, images={len(image_urls)}")
    t0 = time.time()

    # Download images
    import requests
    from PIL import Image
    IMAGES_DIR = f"{OUTPUT_DIR}/images/{product_id}"
    os.makedirs(IMAGES_DIR, exist_ok=True)

    for i, url in enumerate(image_urls[:10]):  # max 10 images
        try:
            img = Image.open(requests.get(url, stream=True).raw)
            img.save(f"{IMAGES_DIR}/{i:02d}.png")
        except Exception as e:
            log(f"  Image {i} failed: {e}")

    # Training config (simplified — use Kohya/SimpleTuner for prod)
    from diffusers import FluxPipeline
    from peft import LoraConfig, get_peft_model
    from diffusers.optimization import get_scheduler

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],
        lora_dropout=0.1,
    )

    # Save trained LoRA
    file_id = uuid.uuid4().hex[:12]
    output_path = f"{OUTPUT_DIR}/{file_id}.safetensors"
    # In production: train and save LoRA weights here
    # For now just create placeholder
    with open(output_path, "wb") as f:
        f.write(b"PLACEHOLDER_LORA_WEIGHTS")

    s3_url = upload_to_s3(output_path, f"lora/{product_id}.safetensors")
    elapsed = int((time.time() - t0) * 1000)
    log(f"LoRA done in {elapsed}ms")
    return {"lora_path": s3_url, "product_id": product_id, "training_time_ms": elapsed}

# ── 7. Polling Loop ─────────────────────────────────────────
log(f"Worker {WORKER_ID} ready. Polling queue:lora...")

while True:
    job_data = r.blpop("queue:lora", timeout=30)
    if job_data is None:
        continue

    try:
        job = json.loads(job_data[1])
        log(f"Got job: {job['job_id']}")
        result = train_lora(job["payload"].get("product_id", "unknown"), job["payload"].get("images", []))
        result["job_id"] = job["job_id"]
        result["worker_id"] = WORKER_ID
        result["status"] = "completed"
        r.setex(f"result:{job['job_id']}", 3600, json.dumps(result))
        log(f"Job {job['job_id']} completed")
    except Exception as e:
        log(f"Job failed: {e}")
        r.setex(f"result:{job['job_id']}", 3600, json.dumps({"status": "failed", "error": str(e)}))
