from pathlib import Path
import subprocess
import os

# =========================
# PRESETS
# =========================

PRESETS = {
    "1": {"nombre": "Podcast",      "descripcion": "Pausas naturales, ritmo conservado",    "margin": "0.4sec", "threshold": "0.06"},
    "2": {"nombre": "Talking-Head", "descripcion": "Corte estándar para cámara frontal",    "margin": "0.2sec", "threshold": "0.04"},
    "3": {"nombre": "Short-form",   "descripcion": "Corte agresivo para Reels / TikTok",    "margin": "0.1sec", "threshold": "0.03"},
}

# =========================
# FUNCIONES
# =========================

def limpiar_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def mostrar_presets():
    print("\n  Presets disponibles:")
    for key, p in PRESETS.items():
        print(f"  [{key}] {p['nombre']} — {p['descripcion']}")


def procesar(video_path: Path, preset: dict, clip_sequence: bool, output_folder: Path = None) -> Path:
    """
    Corre auto-editor sobre video_path con el preset dado.
    Si clip_sequence=True exporta clips separados en una subcarpeta.
    Si output_folder se provee, los archivos van ahí; si no, al lado del video.
    Retorna el path del output (carpeta o archivo).
    """
    destino = output_folder if output_folder else video_path.parent
    destino.mkdir(parents=True, exist_ok=True)
    os.chdir(video_path.parent)

    if clip_sequence:
        antes = set(video_path.parent.glob("*.mp4"))

        cmd = [
            "auto-editor", str(video_path),
            "--margin", preset["margin"],
            "--edit",   f"audio:threshold={preset['threshold']}",
            "--export", "clip-sequence",
        ]

        print(f"\n🎬 Procesando: {video_path.name}", flush=True)
        print(f"   Preset: {preset['nombre']} | margin: {preset['margin']} | threshold: {preset['threshold']}", flush=True)
        print(f"   Modo: clips separados\n", flush=True)

        subprocess.run(cmd, check=True)

        despues      = set(video_path.parent.glob("*.mp4"))
        nuevos       = despues - antes
        clips_folder = destino / f"{video_path.stem}_clips"
        clips_folder.mkdir(exist_ok=True)

        for clip in sorted(nuevos):
            clip.rename(clips_folder / clip.name)
            print(f"   → {clip.name}", flush=True)

        print(f"\n   {len(nuevos)} clips → {clips_folder.name}/", flush=True)
        return clips_folder

    else:
        output_path = destino / f"{video_path.stem}_{preset['nombre']}.mp4"

        cmd = [
            "auto-editor", str(video_path),
            "--margin", preset["margin"],
            "--edit",   f"audio:threshold={preset['threshold']}",
            "--output", str(output_path),
        ]

        print(f"\n🎬 Procesando: {video_path.name}", flush=True)
        print(f"   Preset: {preset['nombre']} | margin: {preset['margin']} | threshold: {preset['threshold']}", flush=True)
        print(f"   Modo: video completo → {output_path.name}\n", flush=True)

        subprocess.run(cmd, check=True)
        return output_path


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    while True:

        print("\n==============================")
        print(f" Silence Cutter")
        print("==============================")
        mostrar_presets()

        opcion = input("\nElegí un preset (1/2/3) o escribí 'exit': ").strip()

        if opcion.lower() == "exit":
            print("\n👋 Cerrando programa...")
            break

        if opcion not in PRESETS:
            print("\n❌ Opción inválida. Escribí 1, 2 o 3.")
            continue

        preset = PRESETS[opcion]

        modo = input("\n¿Output? [1] Video completo  [2] Clips separados: ").strip()
        if modo not in ["1", "2"]:
            print("\n❌ Opción inválida. Escribí 1 o 2.")
            continue

        clip_sequence = modo == "2"

        video_input = input("\nArrastrá el video acá: ").strip()
        video_path  = limpiar_path(video_input)

        if not video_path.exists():
            print(f"\n❌ Archivo no encontrado: {video_path}")
            continue

        if video_path.suffix.lower() not in [".mp4", ".mov", ".avi", ".mkv"]:
            print("\n❌ Formato no soportado.")
            continue

        try:
            output = procesar(video_path, preset, clip_sequence)
            print(f"\n✅ Listo.")
            print(f"📁 {output}")
        except subprocess.CalledProcessError:
            print("\n❌ Error ejecutando auto-editor.")
        except FileNotFoundError:
            print("\n❌ auto-editor no encontrado. Instalalo con: pip install auto-editor")
