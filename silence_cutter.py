from pathlib import Path
import subprocess
import os

# =========================
# CONFIG
# =========================

FORMATS = {".mp4", ".mov", ".avi", ".mkv"}

PRESETS = {
    "1": {"name": "Podcast",      "description": "Natural pauses, preserved rhythm",      "margin": "0.4sec", "threshold": "0.06"},
    "2": {"name": "Talking-Head", "description": "Standard cut for front-facing camera",  "margin": "0.2sec", "threshold": "0.04"},
    "3": {"name": "Short-form",   "description": "Aggressive cut for Reels / TikTok",     "margin": "0.1sec", "threshold": "0.03"},
}

# =========================
# FUNCTIONS
# =========================

def clean_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def resolve_files(path: Path) -> list[Path]:
    """Returns all video files in a folder, or a single file."""
    if path.is_dir():
        return sorted([f for f in path.iterdir() if f.suffix.lower() in FORMATS])
    elif path.suffix.lower() in FORMATS:
        return [path]
    return []


def show_presets():
    print("\n  Available presets:")
    for key, p in PRESETS.items():
        print(f"  [{key}] {p['name']} — {p['description']}")


def procesar(video_path: Path, preset: dict, clip_sequence: bool, output_folder: Path = None) -> Path:
    """
    Runs auto-editor on video_path with the given preset.
    If clip_sequence=True, exports each segment as a separate clip in a subfolder.
    If output_folder is provided, files go there; otherwise next to the video.
    Returns the output path (folder or file).
    """
    dest = output_folder if output_folder else video_path.parent
    dest.mkdir(parents=True, exist_ok=True)
    os.chdir(video_path.parent)

    if clip_sequence:
        # Snapshot of existing MP4s before running auto-editor
        before = set(video_path.parent.glob("*.mp4"))

        cmd = [
            "auto-editor", str(video_path),
            "--margin", preset["margin"],
            "--edit",   f"audio:threshold={preset['threshold']}",
            "--export", "clip-sequence",
        ]

        print(f"\n🎬 Processing: {video_path.name}", flush=True)
        print(f"   Preset: {preset['name']} | margin: {preset['margin']} | threshold: {preset['threshold']}", flush=True)
        print(f"   Mode: clip sequence\n", flush=True)

        subprocess.run(cmd, check=True)

        # Detect new files created by auto-editor and move them to dest
        after        = set(video_path.parent.glob("*.mp4"))
        new_clips    = after - before
        clips_folder = dest / f"{video_path.stem}_clips"
        clips_folder.mkdir(exist_ok=True)

        for clip in sorted(new_clips):
            clip.rename(clips_folder / clip.name)
            print(f"   → {clip.name}", flush=True)

        print(f"\n   {len(new_clips)} clips → {clips_folder.name}/", flush=True)
        return clips_folder

    else:
        output_path = dest / f"{video_path.stem}_{preset['name']}.mp4"

        cmd = [
            "auto-editor", str(video_path),
            "--margin", preset["margin"],
            "--edit",   f"audio:threshold={preset['threshold']}",
            "--output", str(output_path),
        ]

        print(f"\n🎬 Processing: {video_path.name}", flush=True)
        print(f"   Preset: {preset['name']} | margin: {preset['margin']} | threshold: {preset['threshold']}", flush=True)
        print(f"   Mode: single file → {output_path.name}\n", flush=True)

        subprocess.run(cmd, check=True)
        return output_path


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    while True:

        print("\n==============================")
        print(" Silence Cutter")
        print("==============================")
        show_presets()

        option = input("\nChoose a preset (1/2/3) or type 'exit': ").strip()

        if option.lower() == "exit":
            print("\n👋 Closing...")
            break

        if option not in PRESETS:
            print("\n❌ Invalid option. Type 1, 2 or 3.")
            continue

        preset = PRESETS[option]

        mode = input("\nOutput? [1] Single file  [2] Clip sequence: ").strip()
        if mode not in ["1", "2"]:
            print("\n❌ Invalid option. Type 1 or 2.")
            continue

        clip_sequence = mode == "2"

        raw_input  = input("\nDrag a video or folder here: ").strip()
        input_path = clean_path(raw_input)

        if not input_path.exists():
            print(f"\n❌ Not found: {input_path}")
            continue

        files = resolve_files(input_path)

        if not files:
            print("\n❌ No compatible video files found.")
            continue

        if input_path.is_dir():
            print(f"\n📁 Folder detected — {len(files)} file(s) to process.", flush=True)

        for i, video_path in enumerate(files, start=1):
            if len(files) > 1:
                print(f"\n[{i}/{len(files)}]", flush=True)
            try:
                output = procesar(video_path, preset, clip_sequence)
                print(f"\n✅ Done.")
                print(f"📁 {output}")
            except subprocess.CalledProcessError:
                print("\n❌ auto-editor failed.")
            except FileNotFoundError:
                print("\n❌ auto-editor not found. Install it with: pip install auto-editor")
