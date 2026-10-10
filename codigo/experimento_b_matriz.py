"""Matriz digital de selección de pictogramas con síntesis de voz (Gradio + gTTS).

Uso:
    python experimento_b_matriz.py    Servidor en http://127.0.0.1:7860
"""
import base64
import hashlib
import random
import re
import threading
import time
from pathlib import Path
from urllib.parse import quote

import gradio as gr
from gtts import gTTS

from experimento_a_agente import ATRIBUTOS, OFICIOS, dar_pista, evaluar, nuevo_estado, tarjetas

DATOS = Path(__file__).resolve().parent.parent / "datos"
PICTOS = DATOS / "pictogramas"
AUDIO = DATOS / "audio"
LISTA = list(OFICIOS)

FUENTE = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&display=swap">'
CLARO = """() => {
  const f = () => document.body.classList.remove('dark');
  f();
  new MutationObserver(f).observe(document.body, {attributes: true, attributeFilter: ['class']});
}"""
CLIC = """element.addEventListener('click', e => {
  const b = e.target.closest('button[data-o]');
  if (b && !b.disabled) { b.classList.add('pulsada'); trigger('click', {oficio: b.dataset.o}); }
});"""
SONAR = """watch('value', () => {
  const a = element.querySelector('audio');
  if (a) { a.currentTime = 0; a.play().catch(() => {}); }
});"""
CSS = """
:root {
  color-scheme: light;
  --tinta: #1B2559; --mesa: #EAF2FB; --sol: #FFC93C; --azul: #2742A8;
  --cielo: #D3E9FF; --cielo-borde: #8DB8E8; --menta: #D4F1DC; --menta-borde: #86C99A;
  --rosa: #FFDDE8; --rosa-borde: #EDA0B8;
  --bien: #1E7B3A; --bien-fondo: #DDF4E3; --mal: #C0262D; --mal-fondo: #FDE6E7;
  --letra: "Fredoka", "Nunito", "Trebuchet MS", system-ui, sans-serif;
}
html, body { background: var(--mesa) radial-gradient(#CFDDEE 1.4px, transparent 1.6px) 0 0 / 24px 24px !important; }
gradio-app, .gradio-container { background: transparent !important; }
.gradio-container { width: 100% !important; max-width: 1340px !important; margin: 0 auto !important; padding: 0 !important; font-family: var(--letra) !important; color: var(--tinta); }
.gradio-container > .main { padding: 6px 16px 14px !important; }
footer { display: none !important; }

.cartel { text-align: center; padding: 4px 0 10px; }
.cartel h1 {
  display: inline-block; margin: 0; padding: 6px 30px 8px;
  background: var(--sol); color: var(--tinta); border: 4px solid var(--tinta); border-radius: 20px;
  box-shadow: 6px 6px 0 var(--tinta); transform: rotate(-1.5deg);
  font: 700 clamp(1.6rem, 3.4vw, 2.4rem)/1.1 var(--letra); letter-spacing: .02em; text-transform: uppercase;
}

#lado-pista {
  background: #fff; border: 4px solid var(--tinta); border-radius: 24px;
  padding: 14px; box-shadow: 0 8px 0 #C3D2E6; gap: 14px;
}
.panel { text-align: center; border-radius: 16px; padding: 10px 8px 8px; }
.panel h2 { margin: 0 0 6px; font: 600 clamp(1.35rem, 2.3vw, 1.9rem)/1.2 var(--letra); color: var(--tinta); }
.panel.error { background: var(--mal-fondo); }
.panel.error h2 { color: #8E1B21; }
.panel.bien { background: var(--bien-fondo); }
.panel.bien h2 { color: #14532D; }
.rotulo { margin: 0 0 8px; font: 600 1.2rem var(--letra); color: var(--azul); }
.rotulo:empty { display: none; }
.tira {
  container-type: inline-size; display: flex; justify-content: center; align-items: center; gap: 4px;
  padding: 14px 6px 18px; background: #FFF3D1; border: 3px dashed #D9A62E; border-radius: 18px;
}
.mas { flex: none; font: 700 clamp(1.3rem, 5cqi, 2.4rem)/1 var(--letra); color: var(--azul); }
.carta {
  container-type: inline-size; flex: 1 1 0; min-width: 0; max-width: 150px; margin: 0; padding: 6px 4px 4px;
  background: #fff; border: 3px solid var(--tinta); border-radius: 16px; box-shadow: 0 5px 0 var(--tinta);
}
.carta:nth-child(4n+1) { transform: rotate(-2deg); }
.carta:nth-child(4n+3) { transform: rotate(2deg); }
.carta img { display: block; width: 100%; aspect-ratio: 1; object-fit: contain; }
.carta figcaption { margin-top: 4px; font: 700 min(1.3rem, 13cqi)/1.1 var(--letra); color: var(--tinta); letter-spacing: .03em; white-space: nowrap; }
.tira:has(> .carta:nth-of-type(4)) figcaption { font-size: min(1.3rem, 15cqi); }
#lado-pista .html-container { padding: 0; }
.contador { display: flex; align-items: center; justify-content: center; gap: 4px; margin: 10px 0 0; font: 600 1.05rem var(--letra); color: var(--tinta); }
.contador i { font-style: normal; font-size: 1.6rem; line-height: 1; color: #6E7890; }
.contador i.on { color: #8F5C00; }

.panel.bien .tira { position: relative; overflow: hidden; background: #FFE9A8; border-style: solid; }
.panel.bien .tira::before {
  content: ""; position: absolute; inset: -60%;
  background: repeating-conic-gradient(#FFD45C 0 10deg, #FFF0C2 10deg 20deg); animation: giro 8s ease-out;
}
.panel.bien .carta { container-type: normal; position: relative; flex: none; max-width: none; transform: none; animation: pop .7s ease-out; }
.panel.bien .carta img { width: clamp(140px, 34cqi, 210px); }

#repetir, #nueva {
  min-height: 64px; font: 600 1.3rem var(--letra); border: 3px solid var(--tinta); border-radius: 16px;
  box-shadow: 0 5px 0 var(--tinta);
}
#repetir { background: var(--azul); color: #fff; }
#nueva { background: var(--sol); color: var(--tinta); }
#repetir:active, #nueva:active { transform: translateY(4px); box-shadow: 0 1px 0 var(--tinta); }

.tablero {
  container-type: inline-size; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; padding: 16px;
  background: #fff; border: 4px solid var(--tinta); border-radius: 24px; box-shadow: 0 8px 0 #C3D2E6;
}
.casilla {
  position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 0;
  padding: 8px 8px 10px; background: var(--fondo); border: 3px solid var(--borde); border-radius: 18px;
  box-shadow: 0 6px 0 var(--borde); color: var(--tinta); font: inherit; cursor: pointer;
  transition: transform .08s, box-shadow .08s;
}
.casilla:nth-child(-n+4) { --fondo: var(--cielo); --borde: var(--cielo-borde); }
.casilla:nth-child(n+5):nth-child(-n+8) { --fondo: var(--menta); --borde: var(--menta-borde); }
.casilla:nth-child(n+9) { --fondo: var(--rosa); --borde: var(--rosa-borde); }
.casilla img {
  width: 100%; height: clamp(72px, 14vh, 140px); padding: 4px; box-sizing: border-box;
  object-fit: contain; background: #fff; border-radius: 12px;
}
.casilla span { font: 700 clamp(.85rem, 2.6cqi, 1.3rem)/1.1 var(--letra); letter-spacing: .02em; }
.casilla:active, .casilla.pulsada { transform: translateY(4px); box-shadow: 0 2px 0 var(--borde); }
.casilla:disabled { cursor: default; }
.casilla:focus-visible, #repetir:focus-visible, #nueva:focus-visible { outline: 4px solid var(--azul); outline-offset: 3px; }
.casilla.mal { --fondo: var(--mal-fondo); --borde: var(--mal); }
.casilla.mal img { opacity: .35; }
.casilla.mal span { color: #8E1B21; text-decoration: line-through 3px; }
.casilla.gana { --fondo: var(--bien-fondo); --borde: var(--bien); animation: pop .6s ease-out; }
.casilla.ultimo { animation: sacudir .45s; }
.casilla.mal::after, .casilla.gana::after {
  position: absolute; top: -12px; right: -12px; width: 40px; height: 40px; display: grid; place-items: center;
  border: 3px solid #fff; border-radius: 50%; color: #fff; font: 700 1.4rem/1 var(--letra);
}
.casilla.mal::after { content: "✗"; background: var(--mal); }
.casilla.gana::after { content: "★"; background: var(--bien); }
.tablero.fin .casilla:not(.gana) { opacity: .4; }

@keyframes pop { 0% { transform: scale(.85); } 60% { transform: scale(1.08); } 100% { transform: scale(1); } }
@keyframes sacudir { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-8px); } 75% { transform: translateX(8px); } }
@keyframes giro { to { transform: rotate(1turn); } }
@media (orientation: portrait) { .casilla img { height: clamp(72px, 10vh, 120px); } }
@media (orientation: portrait) and (min-width: 600px) {
  .carta { max-width: 120px; }
  .casilla img { height: clamp(64px, 6.5vh, 100px); }
  .panel.bien .carta img { width: clamp(100px, 18cqi, 130px); }
}
@media (max-width: 480px) {
  #lado-pista { padding: 8px; }
  .panel { padding-inline: 0; }
  .tira { gap: 2px; padding-inline: 3px; }
  .carta { padding: 4px 2px 3px; border-width: 2px; }
  .tablero { grid-template-columns: repeat(2, 1fr); }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
"""


def img(palabra):
    return f'<img src="gradio_api/file={quote(str(PICTOS / f"{palabra}.png"))}" alt="">'


def carta(palabra):
    return f'<figure class="carta">{img(palabra)}<figcaption>{palabra.upper()}</figcaption></figure>'


def panel(mensaje, tono, rotulo, palabras, usadas, frase=False):
    """Mensaje del agente, tira de pictogramas y contador de pistas."""
    union = '<span class="mas">+</span>' if frase else ""
    estrellas = "".join('<i class="on">★</i>' if i < usadas else "<i>☆</i>" for i in range(len(ATRIBUTOS)))
    return (f'<section class="panel {tono}"><h2>{mensaje}</h2><p class="rotulo">{rotulo}</p>'
            f'<div class="tira">{union.join(map(carta, palabras))}</div>'
            f'<p class="contador" aria-label="Pistas usadas: {usadas} de {len(ATRIBUTOS)}">Pistas {estrellas}</p></section>')


def tablero(malos=(), gana=None):
    """Tablero de oficios; marca fallos, acierto y bloquea casillas ya jugadas."""
    ultimo = malos[-1] if malos and not gana else None
    casillas = "".join(
        f'<button class="casilla{" gana" if o == gana else " mal" if o in malos else ""}{" ultimo" if o == ultimo else ""}"'
        f' data-o="{o}"{" disabled" if gana or o in malos else ""}>{img(o)}<span>{o.upper()}</span></button>'
        for o in LISTA)
    return f'<div class="tablero{" fin" if gana else ""}">{casillas}</div>'


def pregunta(palabras):
    return f"¿{' '.join(palabras)}?"


def voz(texto, sintetizar=True):
    """Fragmento MP3 cacheado en disco; lo sintetiza si falta. Retorna None si no está disponible."""
    texto = re.sub(r"[^\w\s¡!¿?.,:]", "", texto).strip().lower()
    archivo = AUDIO / f"{hashlib.md5(texto.encode()).hexdigest()}.mp3"
    if not archivo.exists() and sintetizar:
        tmp = archivo.with_suffix(f".{threading.get_ident()}.tmp")
        try:
            AUDIO.mkdir(exist_ok=True)
            gTTS(texto, lang="es", tld="com.mx", timeout=5).save(tmp)
            tmp.replace(archivo)
        except Exception:
            tmp.unlink(missing_ok=True)
    return archivo if archivo.exists() else None


def precargar():
    """Genera en segundo plano todos los fragmentos de voz del juego."""
    fijos = ["¿Quién trabaja aquí?", "¡Intenta otra vez!", "Mira bien.", "¡Muy bien!"]
    por_oficio = [f for o in LISTA for f in (o, f"No es {o}.", f"Es el {o}.")]
    pistas = {pregunta(tarjetas(a, OFICIOS[o][a])) for o in LISTA for a in ATRIBUTOS}
    for frase in [*fijos, *por_oficio, *sorted(pistas)]:
        voz(frase)


def sonido(dicho):
    """Concatena los fragmentos cacheados en un <audio> oculto; el nonce fuerza repetir frases iguales."""
    partes = [voz(f, sintetizar=False) for f in dicho or []]
    mp3 = b"".join(p.read_bytes() for p in partes if p)
    if not mp3:
        return ""
    return f'<audio src="data:audio/mpeg;base64,{base64.b64encode(mp3).decode()}" data-n="{time.time_ns()}"></audio>'


def turno(est, objetivo, mensaje, tono, dicho):
    pista = dar_pista(est, objetivo)
    if pista:
        palabras = tarjetas(*pista)
        dicho = [*dicho, pregunta(palabras)]
    else:
        palabras = sorted(est["cands"])
        dicho = [*dicho, "Mira bien.", *palabras]
    rotulo = "🤖 Pista" if pista else "🤖 Mira bien"
    return (est, objetivo, panel(mensaje, tono, rotulo, palabras, len(est["dadas"]), frase=bool(pista)),
            tablero(est["malos"]), sonido(dicho), dicho)


def nueva_partida():
    return turno(nuevo_estado() | {"malos": []}, random.choice(LISTA), "¿Quién trabaja aquí? 🤔", "", ["¿Quién trabaja aquí?"])


def elegir(est, objetivo, evt: gr.EventData):
    try:
        r = evt.oficio
    except Exception:
        r = None
    if objetivo is None or r not in LISTA or r in est["malos"]:
        return (gr.skip(),) * 6
    if evaluar(est, objetivo, r):
        dicho = ["¡Muy bien!", f"Es el {objetivo}."]
        return (est, None, panel(f"🎉 ¡Muy bien! Es el {objetivo.upper()}", "bien", "", [objetivo], len(est["dadas"])),
                tablero(est["malos"], objetivo), sonido(dicho), dicho)
    est["malos"].append(r)
    return turno(est, objetivo, f"❌ No es {r.upper()}. ¡Intenta otra vez!", "error", [f"No es {r}.", "¡Intenta otra vez!"])


with gr.Blocks(title="¿Quién trabaja aquí?") as demo:
    est, objetivo, dicho = gr.State(), gr.State(), gr.State()
    gr.HTML('<header class="cartel"><h1>¿Quién trabaja aquí?</h1></header>', apply_default_css=False)
    with gr.Row(equal_height=False):
        with gr.Column(scale=4, min_width=320, elem_id="lado-pista"):
            cartas = gr.HTML(apply_default_css=False)
            with gr.Row():
                repetir = gr.Button("🔊 Repetir", elem_id="repetir")
                nueva = gr.Button("🔄 Nueva partida", elem_id="nueva")
        with gr.Column(scale=5, min_width=480):
            casillas = gr.HTML(tablero(), js_on_load=CLIC, apply_default_css=False)
    audio = gr.HTML(js_on_load=SONAR, apply_default_css=False, visible="hidden")

    salidas = [est, objetivo, cartas, casillas, audio, dicho]
    demo.load(nueva_partida, outputs=salidas, show_progress="hidden")
    nueva.click(nueva_partida, outputs=salidas, show_progress="hidden")
    casillas.click(elegir, inputs=[est, objetivo], outputs=salidas, show_progress="hidden")
    repetir.click(sonido, inputs=dicho, outputs=audio, show_progress="hidden")

if __name__ == "__main__":
    threading.Thread(target=precargar, daemon=True).start()
    demo.launch(allowed_paths=[str(DATOS)], css=CSS, js=CLARO, head=FUENTE)
