from pathlib import Path
from tqdm import tqdm
import json

# =========================
# CONFIG
# =========================

MODEL_SIZE = "small"
FORMATS    = {".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav"}

# =========================
# FUNCTIONS
# =========================

def clean_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def resolve_files(path: Path) -> list[Path]:
    """Returns all media files in a folder, or a single file."""
    if path.is_dir():
        return sorted([f for f in path.iterdir() if f.suffix.lower() in FORMATS])
    elif path.suffix.lower() in FORMATS:
        return [path]
    return []


def transcribir(video_path: Path, model: "WhisperModel", output_path: Path = None) -> Path:
    """
    Transcribes video_path using the given Whisper model.
    Saves the JSON to output_path if provided, otherwise next to the video.
    Returns the path of the generated JSON.
    """
    print(f"\n📄 {video_path.name}", flush=True)

    segments, info = model.transcribe(str(video_path), beam_size=5, word_timestamps=True)
    print(f"   Language: {info.language} ({info.language_probability:.0%}) | Duration: {info.duration:.2f}s", flush=True)

    pbar = tqdm(
        total=info.duration, unit="s", desc="   Processing",
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
    )

    words = []
    last_pos = 0
    for segment in segments:
        pbar.update(segment.end - last_pos)
        last_pos = segment.end
        if segment.words:
            for word in segment.words:
                words.append({
                    "word":  word.word.strip(),
                    "start": round(word.start, 3),
                    "end":   round(word.end, 3),
                })
    pbar.close()

    dest = output_path if output_path else video_path.with_suffix(".json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print(f"   ✅ {len(words)} words → {dest.name}", flush=True)
    return dest


def cargar_modelo() -> "WhisperModel":
    """Loads the Whisper model. Called once per session (lazy loading)."""
    from faster_whisper import WhisperModel
    print(f"\n🔄 Loading Whisper model ({MODEL_SIZE})...", flush=True)
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("   Model ready.\n", flush=True)
    return model


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    model = None  # lazy loading — model loads only when first file is dropped

    while True:

        print("\n==============================", flush=True)
        print(f" Transcriber — Whisper {MODEL_SIZE}", flush=True)
        print("==============================", flush=True)

        raw_input = input("\nDrag a video or folder here, or type 'exit': ").strip()

        if raw_input.lower() == "exit":
            print("\n👋 Closing...")
            break

        path = clean_path(raw_input)

        if not path.exists():
            print(f"\n❌ Not found: {path}", flush=True)
            continue

        files = resolve_files(path)

        if not files:
            print("\n❌ No compatible media files found.", flush=True)
            continue

        if path.is_dir():
            print(f"\n📁 Folder detected — {len(files)} file(s) to process.", flush=True)

        # Load model once per session
        if model is None:
            model = cargar_modelo()

        for i, file in enumerate(files, start=1):
            if len(files) > 1:
                print(f"\n[{i}/{len(files)}]", flush=True)
            transcribir(file, model)

        print(f"\n✅ Session complete. {len(files)} file(s) processed.", flush=True)
