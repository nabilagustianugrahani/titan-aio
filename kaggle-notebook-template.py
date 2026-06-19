"""
Claude Code di Kaggle T4 + Tunnel
"""

import subprocess, os, time, re

os.makedirs("/kaggle/working/output", exist_ok=True)
LOG = "/kaggle/working/output/run.log"
def log(m):
    with open(LOG,"a") as f: f.write(f"{time.strftime('%H:%M:%S')} {m}\n")
    print(m)

log("Install Claude Code...")
subprocess.run("npm install -g @anthropic-ai/claude-code@latest", shell=True, timeout=120)
log("Claude Code installed!")

log("Install cloudflared...")
subprocess.run(["wget","-q",
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    "-O","/usr/local/bin/cf"])
os.chmod("/usr/local/bin/cf",0o755)

log("Start tunnel ke port 8080...")
subprocess.Popen(["/usr/local/bin/cf","tunnel","--url","http://127.0.0.1:8080"],
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)

# Bikin endpoint proxy sederhana
subprocess.Popen(["claude","serve","--port","8080"], shell=True)

time.sleep(5)
log("Claude Code serve running on :8080")
log("Cek log di /kaggle/working/output/ untuk URL tunnel")

while True: time.sleep(60)
