# TITAN AIO — Video Worker Notebook

# ⚙️ Konfigurasi Worker
import os, json, time, uuid, subprocess

WORKER_ID = f"video-worker-{uuid.uuid4().hex[:8]}"
OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(m):
    with open(f"{OUTPUT_DIR}/worker.log","a") as f: f.write(f"{time.strftime('%H:%M:%S')} {m}\n")
    print(m)

log(f"=== TITAN AIO Video Worker: {WORKER_ID} ===")

# ── 1. Install ──────────────────────────────────────────────
log("Installing deps...")
subprocess.run("pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124", shell=True, timeout=300)
subprocess.run("pip install -q diffusers transformers accelerate sentencepiece redis boto3 pillow opencv-python", shell=True, timeout=180)
log("Dependencies done")

# ── 2. GPU Check ────────────────────────────────────────────
gpu = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True)
log(f"GPU: {gpu.stdout.strip() if gpu.returncode==0 else 'CPU mode'}")

# ── 3. Load Model (default: Wan 2.2) ───────────────────────
log("Loading Wan 2.2...")
from diffusers import WanPipeline
import torch
pipe = WanPipeline.from_pretrained("Wan-AI/Wan2.2-T2V-14B", torch_dtype=torch.bfloat16)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")
pipe.enable_model_cpu_offload()
log("Wan 2.2 loaded!")

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
def generate_video(script: str, model: str = "wan-2-2", duration: int = 30) -> dict:
    log(f"Generating video: {script[:60]}...")
    t0 = time.time()

    frames = pipe(
        script,
        num_frames=min(duration * 8, 81),  # ~8fps, max 81 frames
        guidance_scale=5.0,
        num_inference_steps=25,
        generator=torch.Generator("cpu").manual_seed(int(time.time()) % 2**31),
    ).frames[0]

    # Save as MP4
    import cv2, numpy as np
    file_id = uuid.uuid4().hex[:12]
    local_path = f"{OUTPUT_DIR}/{file_id}.mp4"
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(local_path, fourcc, 8.0, (w, h))
    for f in frames:
        out.write(cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR))
    out.release()

    s3_url = upload_to_s3(local_path, f"videos/{file_id}.mp4")
    elapsed = int((time.time() - t0) * 1000)
    log(f"Done in {elapsed}ms")
    return {"video_url": s3_url, "model_used": model, "duration_seconds": duration, "generation_time_ms": elapsed}

# ── 7. Polling Loop ─────────────────────────────────────────
log(f"Worker {WORKER_ID} ready. Polling queue:video...")

while True:
    job_data = r.blpop("queue:video", timeout=30)
    if job_data is None:
        continue

    try:
        job = json.loads(job_data[1])
        log(f"Got job: {job['job_id']}")
        result = generate_video(job["payload"].get("script", ""), job["payload"].get("model", "wan-2-2"))
        result["job_id"] = job["job_id"]
        result["worker_id"] = WORKER_ID
        result["status"] = "completed"
        r.setex(f"result:{job['job_id']}", 3600, json.dumps(result))
        log(f"Job {job['job_id']} completed")
    except Exception as e:
        log(f"Job failed: {e}")
        r.setex(f"result:{job['job_id']}", 3600, json.dumps({"status": "failed", "error": str(e)}))
