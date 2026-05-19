from pathlib import Path
import json

# =========================
# PRESETS
# =========================

PRESETS = {
    "1": {"nombre": "MrBeast", "palabras": 1,    "descripcion": "1 palabra por caption"},
    "2": {"nombre": "Hormozi", "palabras": 3,    "descripcion": "2-3 palabras por caption"},
    "3": {"nombre": "Podcast", "palabras": 5,    "descripcion": "4-5 palabras por caption"},
    "4": {"nombre": "Custom",  "palabras": None, "descripcion": "Elegís la cantidad"},
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
    print("\n  Presets:")
    for key, p in PRESETS.items():
        print(f"  [{key}] {p['nombre']} — {p['descripcion']}")


def cargar_palabras(json_path: Path) -> list:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def agrupar_palabras(words: list, n: int) -> list[dict]:
    grupos = []
    for i in range(0, len(words), n):
        bloque = words[i:i + n]
        grupos.append({
            "start": bloque[0]["start"],
            "end":   bloque[-1]["end"],
            "text":  " ".join(w["word"] for w in bloque).strip(),
        })
    return grupos


def formato_srt_time(seconds: float) -> str:
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def generar_srt(grupos: list) -> str:
    lineas = []
    for i, g in enumerate(grupos, start=1):
        lineas.append(str(i))
        lineas.append(f"{formato_srt_time(g['start'])} --> {formato_srt_time(g['end'])}")
        lineas.append(g["text"])
        lineas.append("")
    return "\n".join(lineas)


def generar_captions(json_path: Path, preset: dict, output_path: Path = None) -> Path:
    """
    Genera un .SRT desde json_path con el preset dado.
    Guarda en output_path si se provee, si no al lado del JSON.
    Retorna el path del .SRT generado.
    """
    words  = cargar_palabras(json_path)
    grupos = agrupar_palabras(words, preset["palabras"])
    srt    = generar_srt(grupos)

    dest = output_path if output_path else json_path.with_name(f"{json_path.stem}_{preset['nombre']}.srt")
    dest.write_text(srt, encoding="utf-8")

    print(f"   {len(words)} palabras → {len(grupos)} captions", flush=True)
    print(f"   ✅ {dest.name}", flush=True)
    return dest


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    while True:

        print("\n==============================")
        print(f" Captions Generator — SRT")
        print("==============================")
        mostrar_presets()

        opcion = input("\nElegí un preset (1/2/3/4) o escribí 'exit': ").strip()

        if opcion.lower() == "exit":
            print("\n👋 Cerrando programa...")
            break

        if opcion not in PRESETS:
            print("\n❌ Opción inválida.")
            continue

        preset = PRESETS[opcion]

        if preset["palabras"] is None:
            try:
                n = int(input("¿Cuántas palabras por caption? ").strip())
                if n < 1:
                    raise ValueError
            except ValueError:
                print("\n❌ Ingresá un número entero mayor a 0.")
                continue
            preset = {**preset, "palabras": n}

        json_input = input("\nArrastrá el JSON de transcripción acá: ").strip()
        json_path  = limpiar_path(json_input)

        if not json_path.exists():
            print(f"\n❌ Archivo no encontrado: {json_path}")
            continue

        if json_path.suffix.lower() != ".json":
            print("\n❌ El archivo debe ser un .json generado por transcribe.py.")
            continue

        print(f"\n📄 Cargando: {json_path.name}")
        output = generar_captions(json_path, preset)
        print(f"\n✅ Listo.")
        print(f"📁 {output}")
