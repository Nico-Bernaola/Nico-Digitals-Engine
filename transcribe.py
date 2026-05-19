from pathlib import Path
from tqdm import tqdm
import json

# =========================
# CONFIG
# =========================

MODEL_SIZE = "small"
FORMATOS   = {".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav"}

# =========================
# FUNCIONES
# =========================

def limpiar_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def resolver_archivos(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted([f for f in path.iterdir() if f.suffix.lower() in FORMATOS])
    elif path.suffix.lower() in FORMATOS:
        return [path]
    return []


def transcribir(video_path: Path, model: "WhisperModel", output_path: Path = None) -> Path:
    """
    Transcribe video_path con el modelo dado.
    Guarda el JSON en output_path si se provee, si no al lado del video.
    Retorna el path del JSON generado.
    """
    print(f"\n📄 {video_path.name}", flush=True)

    segments, info = model.transcribe(str(video_path), beam_size=5, word_timestamps=True)
    print(f"   Idioma: {info.language} ({info.language_probability:.0%}) | Duración: {info.duration:.2f}s", flush=True)

    pbar = tqdm(
        total=info.duration, unit="s", desc="   Procesando",
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

    print(f"   ✅ {len(words)} palabras → {dest.name}", flush=True)
    return dest


def cargar_modelo() -> "WhisperModel":
    from faster_whisper import WhisperModel
    print(f"\n🔄 Cargando modelo Whisper {MODEL_SIZE}...", flush=True)
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("   Modelo listo.\n", flush=True)
    return model


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    model = None  # lazy loading

    while True:

        print("\n==============================", flush=True)
        print(f" Transcriber — Whisper {MODEL_SIZE}", flush=True)
        print("==============================", flush=True)

        raw_input = input("\nArrastrá un video o carpeta acá, o escribí 'exit': ").strip()

        if raw_input.lower() == "exit":
            print("\n👋 Cerrando programa...")
            break

        path = limpiar_path(raw_input)

        if not path.exists():
            print(f"\n❌ No encontrado: {path}", flush=True)
            continue

        archivos = resolver_archivos(path)

        if not archivos:
            print("\n❌ No se encontraron videos compatibles.", flush=True)
            continue

        if path.is_dir():
            print(f"\n📁 Carpeta detectada — {len(archivos)} archivo(s) para procesar.", flush=True)

        if model is None:
            model = cargar_modelo()

        for i, archivo in enumerate(archivos, start=1):
            if len(archivos) > 1:
                print(f"\n[{i}/{len(archivos)}]", flush=True)
            transcribir(archivo, model)

        print(f"\n✅ Sesión completa. {len(archivos)} archivo(s) procesado(s).", flush=True)
