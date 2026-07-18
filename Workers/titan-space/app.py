"""TITAN AIO — Scene Builder + TTS + Music (cpu-basic, no GPU).

Single Gradio app combining:
1. Scene Builder — arrange clips + text + voiceover → export
2. Voice Cloner / TTS — text → speech (edge-tts)
3. Music Generator — prompt → background music (HF Inference API)
"""

import os
import subprocess
import uuid
from pathlib import Path

import gradio as gr

# ── Config ────────────────────────────────────────────────────────
HF_TOKEN = os.environ.get("HF_TOKEN", "")
WORK_DIR = Path("/tmp/titan-space")
WORK_DIR.mkdir(parents=True, exist_ok=True)

# ── TTS (edge-tts) ────────────────────────────────────────────────

VOICE_MAP = {
    "id": {"male": "id-ID-ArdiNeural", "female": "id-ID-GadisNeural"},
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"},
}

async def generate_tts(text: str, lang: str = "id", gender: str = "female", emotion: str = "enthusiastic") -> str:
    """Generate TTS audio. Returns path to .mp3 file."""
    try:
        import edge_tts
        rate = {"excited": "+20%", "enthusiastic": "+15%", "neutral": "+0%", "calm": "-10%"}.get(emotion, "+0%")
        voice = VOICE_MAP.get(lang, VOICE_MAP["id"]).get(gender, "id-ID-GadisNeural")
        out = str(WORK_DIR / f"tts-{uuid.uuid4().hex[:8]}.mp3")
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await communicate.save(out)
        return out
    except Exception as e:
        return f"Error: {e}"

# ── Music Generator (HF Inference API) ────────────────────────────

async def generate_music(prompt: str, duration: int = 15) -> str:
    """Generate music from prompt. Returns path to .wav file."""
    try:
        import httpx
        max_len = {5: 128, 10: 192, 15: 256, 20: 320, 30: 512}.get(duration, 256)
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api-inference.huggingface.co/models/facebook/musicgen-medium",
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": max_len, "temperature": 0.8}},
            )
            resp.raise_for_status()
            out = str(WORK_DIR / f"music-{uuid.uuid4().hex[:8]}.wav")
            with open(out, "wb") as f:
                f.write(resp.content)
            return out
    except Exception as e:
        return f"Error: {e}"

# ── Scene Builder ─────────────────────────────────────────────────

_ffmpeg = False
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    _ffmpeg = True
except Exception:
    pass

scenes: dict = {}

def add_scene(video, text: str, duration: int):
    sid = uuid.uuid4().hex[:8]
    scenes[sid] = {"id": sid, "video": video, "text": text, "duration": duration}
    return list(scenes.values())

def remove_scene(sid: str):
    scenes.pop(sid, None)
    return list(scenes.values())

def clear_scenes():
    scenes.clear()
    return []

async def export_scenes():
    if not scenes:
        return None, "No scenes"
    if not _ffmpeg:
        return None, "FFmpeg not available"

    concat = WORK_DIR / "concat.txt"
    with open(concat, "w") as f:
        s = sorted(scenes.values(), key=lambda x: list(scenes.keys()).index(x["id"]))
        for sc in s:
            if sc.get("video") and Path(sc["video"]).exists():
                f.write(f"file '{sc['video']}'\n")
                f.write(f"duration {sc['duration']}\n")

    out = str(WORK_DIR / f"scene-{uuid.uuid4().hex[:8]}.mp4")
    try:
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", out],
                       capture_output=True, timeout=300)
        return out, "Success"
    except Exception as e:
        return None, str(e)

# ── Gradio UI ─────────────────────────────────────────────────────

with gr.Blocks(title="TITAN AIO Creator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎬 TITAN AIO Creator")
    gr.Markdown("Scene Builder + AI Voice + AI Music — totally free")

    with gr.Tabs():
        # ── Tab 1: Scene Builder ──
        with gr.TabItem("🎥 Scene Builder"):
            with gr.Row():
                with gr.Column(scale=1):
                    sc_video = gr.Video(label="Video Clip")
                    sc_text = gr.Textbox(label="Text Overlay")
                    sc_dur = gr.Slider(2, 30, value=5, step=1, label="Duration")
                    add_btn = gr.Button("➕ Add Scene", variant="primary")
                with gr.Column(scale=2):
                    sc_list = gr.JSON(label="Scenes")
                    with gr.Row():
                        export_btn = gr.Button("🎬 Export Video", variant="primary")
                        clear_btn = gr.Button("Clear")
                    sc_out = gr.Video(label="Final Video")
                    sc_status = gr.Textbox(label="Status")

            add_btn.click(fn=add_scene, inputs=[sc_video, sc_text, sc_dur], outputs=sc_list)
            clear_btn.click(fn=clear_scenes, outputs=sc_list)
            export_btn.click(fn=export_scenes, outputs=[sc_out, sc_status])

        # ── Tab 2: Voice Cloner / TTS ──
        with gr.TabItem("🎤 Voice Generator"):
            tts_text = gr.Textbox(label="Text", placeholder="Halo guys, produk ini recommended!", lines=3)
            with gr.Row():
                tts_lang = gr.Dropdown(["id", "en"], value="id", label="Language")
                tts_gender = gr.Radio(["female", "male"], value="female", label="Voice Gender")
                tts_emotion = gr.Dropdown(["neutral", "enthusiastic", "excited", "calm"], value="enthusiastic", label="Emotion")
            tts_btn = gr.Button("🔊 Generate Voice", variant="primary")
            tts_audio = gr.Audio(label="Generated Voice", type="filepath")

            tts_btn.click(fn=generate_tts, inputs=[tts_text, tts_lang, tts_gender, tts_emotion], outputs=tts_audio)

        # ── Tab 3: Music Generator ──
        with gr.TabItem("🎵 Music Generator"):
            music_prompt = gr.Textbox(label="Music Description", placeholder="upbeat electronic background music for product review", lines=2)
            music_dur = gr.Slider(5, 30, value=15, step=5, label="Duration (sec)")
            music_btn = gr.Button("🎵 Generate Music", variant="primary")
            music_audio = gr.Audio(label="Generated Music", type="filepath")

            music_btn.click(fn=generate_music, inputs=[music_prompt, music_dur], outputs=music_audio)

if __name__ == "__main__":
    app.launch(server_port=7860)
