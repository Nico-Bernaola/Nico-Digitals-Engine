from version import VERSION
from pathlib import Path
import questionary

# Imports de la suite — cada script expone sus funciones
from splitter       import split
from transcribe     import transcribir, cargar_modelo, FORMATOS
from silence_cutter import procesar as cut, PRESETS as PRESETS_SILENCE
from captions       import generar_captions, PRESETS as PRESETS_CAPTIONS
from meta           import generar_meta, PLATAFORMAS

# =========================
# CONFIG
# =========================

PASOS = [
    {"key": "split",      "label": "Split        — separar audio y video"},
    {"key": "transcribe", "label": "Transcribe   — generar JSON con Whisper"},
    {"key": "cut",        "label": "Silence Cut  — eliminar silencios"},
    {"key": "captions",   "label": "Captions     — generar .SRT"},
    {"key": "meta",       "label": "Meta         — generar copy por plataforma"},
]

# =========================
# HELPERS
# =========================

def limpiar_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def separador(titulo: str):
    print(f"\n{'─'*50}", flush=True)
    print(f"  {titulo}",  flush=True)
    print(f"{'─'*50}",    flush=True)


# =========================
# MAIN LOOP
# =========================

while True:

    print("\n══════════════════════════════════════", flush=True)
    print(f"  Nico Digitals Content Engine | v{VERSION}", flush=True)
    print(  "  Pipeline — Alpha",                         flush=True)
    print(  "══════════════════════════════════════", flush=True)
    print(  "  ℹ️  Para ayuda leé el README.md\n",        flush=True)

    # ── Selección de válvulas ──────────────────────────────────────────────
    valvulas = questionary.checkbox(
        "¿Qué módulos querés correr? ",
        choices=[p["label"] for p in PASOS]
    ).ask()

    if not valvulas:
        print("\n⚠️  No seleccionaste ningún módulo.", flush=True)
        continue

    keys_activos = [p["key"] for p in PASOS if p["label"] in valvulas]

    # ── Dependencias automáticas ──────────────────────────────────────────
    for dep in ["captions", "meta"]:
        if dep in keys_activos and "transcribe" not in keys_activos:
            print(f"\n⚠️  '{dep}' requiere Transcribe. Activándolo automáticamente.", flush=True)
            keys_activos.insert(keys_activos.index(dep), "transcribe")

    # ── Configurar módulos opcionales ────────────────────────────────────
    preset_silence  = None
    clip_sequence   = False
    preset_captions = None
    plataformas_meta = []

    if "cut" in keys_activos:
        print("\n  Presets de Silence Cut:")
        for k, v in PRESETS_SILENCE.items():
            print(f"  [{k}] {v['nombre']} — {v['descripcion']}")
        op = input("  Elegí preset (1/2/3): ").strip()
        preset_silence = PRESETS_SILENCE.get(op, PRESETS_SILENCE["2"])

        modo_cut = questionary.select(
            "¿Cómo querés el output del corte?",
            choices=["Video completo", "Clips separados en carpeta"]
        ).ask()
        clip_sequence = modo_cut == "Clips separados en carpeta"

    if "captions" in keys_activos:
        print("\n  Presets de Captions:")
        for k, v in PRESETS_CAPTIONS.items():
            print(f"  [{k}] {v['nombre']} — {v['descripcion']}")
        op = input("  Elegí preset (1/2/3/4): ").strip()
        preset_captions = PRESETS_CAPTIONS.get(op, PRESETS_CAPTIONS["2"])
        if preset_captions["palabras"] is None:
            try:
                n = int(input("  ¿Cuántas palabras por caption? ").strip())
                preset_captions = {**preset_captions, "palabras": max(1, n)}
            except ValueError:
                preset_captions = PRESETS_CAPTIONS["2"]

    if "meta" in keys_activos:
        seleccion = questionary.checkbox(
            "¿Para qué plataformas generamos copy?",
            choices=[p["nombre"] for p in PLATAFORMAS.values()]
        ).ask() or []
        plataformas_meta = [k for k, v in PLATAFORMAS.items() if v["nombre"] in seleccion]

    # ── Input de video ────────────────────────────────────────────────────
    video_input = input("\nArrastrá el video crudo acá: ").strip()

    if video_input.lower() == "exit":
        print("\n👋 Cerrando programa...")
        break

    video_path = limpiar_path(video_input)

    if not video_path.exists():
        print(f"\n❌ Archivo no encontrado: {video_path}", flush=True)
        continue

    if video_path.suffix.lower() not in FORMATOS:
        print("\n❌ Formato no soportado.", flush=True)
        continue

    # ── Crear carpeta output ──────────────────────────────────────────────
    output_folder = video_path.parent / f"{video_path.stem}_output"
    output_folder.mkdir(exist_ok=True)
    print(f"\n📁 Output: {output_folder}", flush=True)

    # ── Ejecutar módulos en orden ─────────────────────────────────────────
    json_path = None
    whisper_model = None

    for key in keys_activos:

        if key == "split":
            separador("SPLIT — Separando audio y video")
            split(video_path, output_folder)

        elif key == "transcribe":
            separador("TRANSCRIBE — Generando JSON con Whisper")
            if whisper_model is None:
                whisper_model = cargar_modelo()
            dest = output_folder / f"{video_path.stem}_transcript.json"
            json_path = transcribir(video_path, whisper_model, output_path=dest)
            if not json_path:
                print("\n❌ Transcripción fallida. Abortando pipeline.", flush=True)
                break

        elif key == "cut":
            separador(f"SILENCE CUT — Preset: {preset_silence['nombre']}")
            cut(video_path, preset_silence, clip_sequence, output_folder=output_folder)

        elif key == "captions":
            separador(f"CAPTIONS — Preset: {preset_captions['nombre']}")
            if json_path:
                dest = output_folder / f"{video_path.stem}_{preset_captions['nombre']}.srt"
                generar_captions(json_path, preset_captions, output_path=dest)
            else:
                print("\n⚠️  No hay JSON disponible para captions.", flush=True)

        elif key == "meta":
            separador("META — Generando copy de marketing")
            if json_path and plataformas_meta:
                generar_meta(json_path, plataformas_meta, output_folder)
            else:
                print("\n⚠️  No hay JSON o plataformas para meta.", flush=True)

    print(f"\n{'═'*38}", flush=True)
    print(f"  ✅ Pipeline completo.",    flush=True)
    print(f"  📁 {output_folder}",       flush=True)
    print(f"{'═'*38}",                   flush=True)

    continuar = input("\n¿Procesar otro video? (Enter para continuar / 'exit' para salir): ").strip().lower()
    if continuar == "exit":
        print("\n👋 Cerrando programa...")
        break
