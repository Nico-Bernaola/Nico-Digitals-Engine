from pathlib import Path
import subprocess

# =========================
# FUNCIONES
# =========================

def limpiar_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def split(video_path: Path, output_folder: Path) -> bool:
    """
    Separa audio y video en una subcarpeta split/ dentro de output_folder.
    Retorna True si tuvo éxito.
    """
    split_folder = output_folder / "split"
    split_folder.mkdir(parents=True, exist_ok=True)

    footage = split_folder / f"{video_path.stem}_footage.mp4"
    audio   = split_folder / f"{video_path.stem}_audio.mp3"

    ok_v = subprocess.run([
        "ffmpeg", "-i", str(video_path),
        "-an", "-c:v", "copy", "-y", str(footage)
    ], check=False).returncode == 0

    ok_a = subprocess.run([
        "ffmpeg", "-i", str(video_path),
        "-vn", "-q:a", "0", "-y", str(audio)
    ], check=False).returncode == 0

    if ok_v and ok_a:
        readme = split_folder / "README.txt"
        readme.write_text(
            f"Archivos generados por splitter — Nico Digitals Content Engine\n"
            f"Raw footage original: {video_path.name}\n\n"
            f"- {footage.name}: video sin audio (copia directa del raw, sin reencoding)\n"
            f"- {audio.name}: audio sin video (máxima calidad)\n",
            encoding="utf-8"
        )
        print(f"   ✅ {footage.name}", flush=True)
        print(f"   ✅ {audio.name}", flush=True)
        print(f"   ✅ README.txt", flush=True)
        return True
    else:
        print("   ❌ Error en split.", flush=True)
        return False


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    while True:

        print("\n==============================")
        print(f" FFmpeg Video Separator")
        print("==============================")

        video_input = input("\nArrastrá un video acá o escribí 'exit': ").strip()

        if video_input.lower() == "exit":
            print("\n👋 Cerrando programa...")
            break

        video_path = limpiar_path(video_input)

        if not video_path.exists():
            print("\n❌ Archivo no encontrado.")
            continue

        output_folder = video_path.parent / video_path.stem
        ok = split(video_path, output_folder)

        if ok:
            print(f"\n✅ Listo.")
            print(f"📁 {output_folder / 'split'}")
