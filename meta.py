from pathlib import Path
from dotenv import load_dotenv
import json
import urllib.request
import urllib.error
import os

# =========================
# CONFIG
# =========================

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL     = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

FORMATS = {".json"}

PLATAFORMAS = {
    "instagram": {
        "name":     "Instagram",
        "tone":     "close, aspirational, moderate emoji use",
        "caption":  "150-300 characters",
        "hashtags": "10-15 mixed hashtags (niche + broad)",
        "cta":      "save this video, follow us, comment your opinion",
    },
    "tiktok": {
        "name":     "TikTok",
        "tone":     "direct, energetic, colloquial, strong hook",
        "caption":  "100-150 characters",
        "hashtags": "5-8 trending and niche hashtags",
        "cta":      "follow for more, comment if this happened to you, duet this",
    },
    "youtube_shorts": {
        "name":     "YouTube Shorts",
        "tone":     "informative but dynamic, honest clickbait title",
        "caption":  "100-200 characters",
        "hashtags": "3-5 relevant hashtags",
        "cta":      "subscribe, watch the full video, leave a like",
    },
    "linkedin": {
        "name":     "LinkedIn",
        "tone":     "professional, reflective, adds value, minimal emojis",
        "caption":  "200-400 characters with line breaks for readability",
        "hashtags": "3-5 professional hashtags",
        "cta":      "what do you think?, share if this added value, follow me",
    },
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


def load_transcript(json_path: Path) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        words = json.load(f)
    return " ".join(w["word"] for w in words).strip()


def generate_copy(transcript: str, platform: dict) -> str:
    prompt = f"""You are an expert in digital marketing and social media copywriting.

I'm giving you a video transcript and your task is to generate the full copy for {platform['name']}.

TRANSCRIPT:
{transcript}

INSTRUCTIONS FOR {platform['name'].upper()}:
- Tone: {platform['tone']}
- Caption length: {platform['caption']}
- Hashtags: {platform['hashtags']}
- Suggested CTA: {platform['cta']}

Reply ONLY with the following format, no explanations or markdown:

TITLE:
[platform-optimized title]

HOOK:
[first line that stops the scroll]

CAPTION:
[full caption ready to copy and paste]

HASHTAGS:
[hashtags ready to copy and paste]

CTA:
[call to action]
"""

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }).encode("utf-8")

    req = urllib.request.Request(
        GEMINI_URL, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def generar_meta(json_path: Path, platform_keys: list, output_folder: Path) -> bool:
    """
    Generates copy for the given platforms from json_path.
    Saves .txt files in output_folder/meta/.
    Returns True if no errors occurred.
    """
    transcript  = load_transcript(json_path)
    meta_folder = output_folder / "meta"
    meta_folder.mkdir(parents=True, exist_ok=True)
    errors = []

    for key in platform_keys:
        platform = PLATAFORMAS[key]
        print(f"\n🤖 Generating copy for {platform['name']}...", flush=True)
        try:
            copy = generate_copy(transcript, platform)
            out  = meta_folder / f"{key}.txt"
            out.write_text(copy, encoding="utf-8")
            print(f"   ✅ {out.name}", flush=True)
        except urllib.error.HTTPError as e:
            print(f"   ❌ API error ({e.code}): {e.reason}", flush=True)
            errors.append(platform["name"])
        except Exception as e:
            print(f"   ❌ Error: {e}", flush=True)
            errors.append(platform["name"])

    generated = len(platform_keys) - len(errors)
    print(f"\n✅ {generated}/{len(platform_keys)} copies generated.", flush=True)
    if errors:
        print(f"⚠️  Failed: {', '.join(errors)}", flush=True)
    return len(errors) == 0


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    import questionary

    while True:

        print("\n==============================", flush=True)
        print(" Meta Generator",               flush=True)
        print("==============================", flush=True)

        # Platform selection
        selection = questionary.checkbox(
            "Generate copy for which platforms?",
            choices=[p["name"] for p in PLATAFORMAS.values()]
        ).ask()

        if not selection:
            print("\n⚠️  No platforms selected.", flush=True)
            continue

        platform_keys = [k for k, v in PLATAFORMAS.items() if v["name"] in selection]

        # Input
        raw_input  = input("\nDrag a JSON file or folder here: ").strip()

        input_path = clean_path(raw_input)

        if not input_path.exists():
            print(f"\n❌ Not found: {input_path}", flush=True)
            continue

        files = resolve_files(input_path)

        if not files:
            print("\n❌ No compatible JSON files found.", flush=True)
            continue

        if input_path.is_dir():
            print(f"\n📁 Folder detected — {len(files)} file(s) to process.", flush=True)

        for i, json_path in enumerate(files, start=1):
            if len(files) > 1:
                print(f"\n[{i}/{len(files)}]", flush=True)
            print(f"\n📄 Loading: {json_path.name}", flush=True)
            output_folder = json_path.parent / f"{json_path.stem}_meta"
            generar_meta(json_path, platform_keys, output_folder)
            print(f"📁 {output_folder / 'meta'}", flush=True)

        print(f"\n✅ Done. {len(files)} file(s) processed.", flush=True)

        again = input("\nProcess another file? (Enter to continue / 'exit' to quit): ").strip().lower()
        if again == "exit":
            print("\n👋 Closing...")
            break
