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

PLATAFORMAS = {
    "instagram": {
        "nombre":   "Instagram",
        "tono":     "cercano, aspiracional, uso de emojis moderado",
        "caption":  "150-300 caracteres",
        "hashtags": "10-15 hashtags mixtos (nicho + masivos)",
        "cta":      "guardá este video, seguinos, comentá tu opinión",
    },
    "tiktok": {
        "nombre":   "TikTok",
        "tono":     "directo, energético, coloquial, gancho fuerte",
        "caption":  "100-150 caracteres",
        "hashtags": "5-8 hashtags trending y de nicho",
        "cta":      "seguime para más, comenta si te pasó, duet esto",
    },
    "youtube_shorts": {
        "nombre":   "YouTube Shorts",
        "tono":     "informativo pero dinámico, título clickbait honesto",
        "caption":  "100-200 caracteres",
        "hashtags": "3-5 hashtags relevantes",
        "cta":      "suscribite, mirá el video completo, dejá un like",
    },
    "linkedin": {
        "nombre":   "LinkedIn",
        "tono":     "profesional, reflexivo, agrega valor, sin emojis excesivos",
        "caption":  "200-400 caracteres con saltos de línea para legibilidad",
        "hashtags": "3-5 hashtags profesionales",
        "cta":      "¿qué pensás?, compartí si te aportó valor, seguime",
    },
}

# =========================
# FUNCIONES
# =========================

def limpiar_path(raw: str) -> Path:
    raw = raw.strip().replace('"', "").replace("'", "")
    if raw.startswith("/") and len(raw) > 2 and raw[2] == "/":
        raw = f"{raw[1].upper()}:{raw[2:]}"
    return Path(raw)


def cargar_transcripcion(json_path: Path) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        words = json.load(f)
    return " ".join(w["word"] for w in words).strip()


def generar_copy(transcripcion: str, plataforma: dict) -> str:
    prompt = f"""Sos un experto en marketing digital y copywriting para redes sociales.

Te doy la transcripción de un video y tu tarea es generar el copy completo para {plataforma['nombre']}.

TRANSCRIPCIÓN:
{transcripcion}

INSTRUCCIONES PARA {plataforma['nombre'].upper()}:
- Tono: {plataforma['tono']}
- Caption: {plataforma['caption']}
- Hashtags: {plataforma['hashtags']}
- CTA sugerido: {plataforma['cta']}

Respondé ÚNICAMENTE con el siguiente formato, sin explicaciones ni markdown:

TÍTULO:
[título optimizado para la plataforma]

HOOK:
[primera línea que para el scroll]

CAPTION:
[caption completa lista para copiar y pegar]

HASHTAGS:
[hashtags listos para copiar y pegar]

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


def generar_meta(json_path: Path, plataformas_keys: list, output_folder: Path) -> bool:
    """
    Genera copy para las plataformas indicadas desde json_path.
    Guarda los .txt en output_folder/meta/.
    Retorna True si no hubo errores.
    """
    transcripcion = cargar_transcripcion(json_path)
    meta_folder   = output_folder / "meta"
    meta_folder.mkdir(parents=True, exist_ok=True)
    errores = []

    for key in plataformas_keys:
        plataforma = PLATAFORMAS[key]
        print(f"\n🤖 Generando copy para {plataforma['nombre']}...", flush=True)
        try:
            copy = generar_copy(transcripcion, plataforma)
            out  = meta_folder / f"{key}.txt"
            out.write_text(copy, encoding="utf-8")
            print(f"   ✅ {out.name}", flush=True)
        except urllib.error.HTTPError as e:
            print(f"   ❌ Error API ({e.code}): {e.reason}", flush=True)
            errores.append(plataforma['nombre'])
        except Exception as e:
            print(f"   ❌ Error: {e}", flush=True)
            errores.append(plataforma['nombre'])

    generados = len(plataformas_keys) - len(errores)
    print(f"\n✅ {generados}/{len(plataformas_keys)} copies generados.", flush=True)
    if errores:
        print(f"⚠️  Fallaron: {', '.join(errores)}", flush=True)
    return len(errores) == 0


# =========================
# MAIN LOOP
# =========================

if __name__ == "__main__":

    while True:

        print("\n==============================", flush=True)
        print(f" Meta Generator",  flush=True)
        print("==============================", flush=True)

        json_input = input("\nArrastrá el JSON de transcripción acá o escribí 'exit': ").strip()

        if json_input.lower() == "exit":
            print("\n👋 Cerrando programa...")
            break

        json_path = limpiar_path(json_input)

        if not json_path.exists():
            print(f"\n❌ Archivo no encontrado: {json_path}", flush=True)
            continue

        if json_path.suffix.lower() != ".json":
            print("\n❌ El archivo debe ser un .json generado por transcribe.py.", flush=True)
            continue

        import questionary
        seleccion = questionary.checkbox(
            "¿Para qué plataformas generamos copy?",
            choices=[p["nombre"] for p in PLATAFORMAS.values()]
        ).ask()

        if not seleccion:
            print("\n⚠️  No seleccionaste ninguna plataforma.", flush=True)
            continue

        keys_elegidos = [k for k, v in PLATAFORMAS.items() if v["nombre"] in seleccion]

        print(f"\n📄 Cargando: {json_path.name}", flush=True)
        output_folder = json_path.parent / f"{json_path.stem}_meta"
        generar_meta(json_path, keys_elegidos, output_folder)
        print(f"📁 {output_folder / 'meta'}", flush=True)
