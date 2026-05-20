from pathlib import Path
import json

# =========================
# CONFIG
# =========================

FORMATS = {".json"}

PRESETS = {
    "1": {"name": "MrBeast", "words": 1,    "description": "1 word per caption"},
    "2": {"name": "Hormozi", "words": 3,    "description": "2-3 words per caption"},
    "3": {"name": "Podcast", "words": 5,    "description": "4-5 words per caption"},
    "4": {"name": "Custom",  "words": None, "description": "You choose the amount"},
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
    """Returns all JSON files in a folder, or a single file."""
    if path.is_dir():
        return sorted([f for f in path.iterdir() if f.suffix.lower() in FORMATS])
    elif path.suffix.lower() in FORMATS:
        return [path]
    return []


def show_presets():
    print("\n  Available presets:")
    for key, p in PRESETS.items():
        print(f"  [{key}] {p['name']} — {p['description']}")


def load_words(json_path: Path) -> list:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def group_words(words: list, n: int) -> list[dict]:
    """Groups words into blocks of n — each block is one caption."""
    groups = []
    for i in range(0, len(words), n):
        block = words[i:i + n]
        groups.append({
            "start": block[0]["start"],
            "end":   block[-1]["end"],
            "text":  " ".join(w["word"] for w in block).strip(),
        })
    return groups


def format_srt_time(seconds: float) -> str:
    """Converts seconds to SRT format: HH:MM:SS,mmm"""
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def build_srt(groups: list) -> str:
    lines = []
    for i, g in enumerate(groups, start=1):
        lines.append(str(i))
        lines.append(f"{format_srt_time(g['start'])} --> {format_srt_time(g['end'])}")
        lines.append(g["text"])
        lines.append("")
    return "\n".join(lines)


def generar_captions(json_path: Path, preset: dict, output_path: Path = None) -> Path:
    """
    Generates a .SRT file from json_path using the given preset.
    Saves to output_path if provided, otherwise next to the JSON.
    Returns the path of the generated .SRT.
    """
    words  = load_words(json_path)
    groups = group_words(words, preset["words"])
    srt    = build_srt(groups)

    dest = output_path if output_path else json_path.with_name(f"{json_path.stem}_{preset['name']}.srt")
    dest.write_text(srt, encoding="utf-8")

    print(f"   {len(words)} words → {len(groups)} captions", flush=True)
    print(f"   ✅ {dest.name}", flush=True)
    return dest


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    while True:

        print("\n==============================")
        print(" Captions Generator — SRT")
        print("==============================")
        show_presets()

        option = input("\nChoose a preset (1/2/3/4) or type 'exit': ").strip()

        if option.lower() == "exit":
            print("\n👋 Closing...")
            break

        if option not in PRESETS:
            print("\n❌ Invalid option.")
            continue

        preset = PRESETS[option]

        # Custom: ask for word count
        if preset["words"] is None:
            try:
                n = int(input("How many words per caption? ").strip())
                if n < 1:
                    raise ValueError
            except ValueError:
                print("\n❌ Enter a positive integer.")
                continue
            preset = {**preset, "words": n}

        raw_input  = input("\nDrag a JSON file or folder here: ").strip()
        input_path = clean_path(raw_input)

        if not input_path.exists():
            print(f"\n❌ Not found: {input_path}")
            continue

        files = resolve_files(input_path)

        if not files:
            print("\n❌ No compatible JSON files found.")
            continue

        if input_path.is_dir():
            print(f"\n📁 Folder detected — {len(files)} file(s) to process.", flush=True)

        for i, json_path in enumerate(files, start=1):
            if len(files) > 1:
                print(f"\n[{i}/{len(files)}]", flush=True)
            print(f"\n📄 Loading: {json_path.name}", flush=True)
            output = generar_captions(json_path, preset)
            print(f"📁 {output}", flush=True)

        print(f"\n✅ Done. {len(files)} file(s) processed.", flush=True)
