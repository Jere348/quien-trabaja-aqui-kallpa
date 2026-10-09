"""Experimento B - Matriz digital de selección de pictogramas (sin visión computacional).

El agente muestra la pista como tarjetas de pictogramas y el jugador responde tocando
un oficio del tablero. Usa el mismo motor del Experimento A.

  python experimento_b_matriz.py   -> abre http://127.0.0.1:7860
"""
import random
from pathlib import Path

import gradio as gr

from experimento_a_agente import OFICIOS, dar_pista, evaluar, nuevo_estado, tarjetas

PICTOS = Path(__file__).resolve().parent.parent / "datos" / "pictogramas"
LISTA = list(OFICIOS)


def picto(palabra):
    return str(PICTOS / f"{palabra}.png"), palabra.upper()


def turno(est, objetivo, mensaje):
    pista = dar_pista(est, objetivo)
    imagenes = [picto(p) for p in tarjetas(*pista)] if pista else [picto(c) for c in sorted(est["cands"])]
    return est, objetivo, imagenes, f"## {mensaje}\n### 🤖 {'Pista:' if pista else 'Mira bien:'}"


def nueva_partida():
    return turno(nuevo_estado(), random.choice(LISTA), "¿Quién trabaja aquí? 🤔")


def elegir(est, objetivo, evt: gr.SelectData):
    if objetivo is None:  # partida terminada: esperar "Nueva partida"
        return est, objetivo, gr.skip(), gr.skip()
    r = LISTA[evt.index]
    if evaluar(est, objetivo, r):
        return est, None, [picto(objetivo)], f"## 🎉 ¡Muy bien! Es el {objetivo.upper()}"
    return turno(est, objetivo, f"❌ No es {r.upper()}. ¡Intenta otra vez!")


with gr.Blocks(title="¿Quién trabaja aquí?") as demo:
    est, objetivo = gr.State(), gr.State()
    mensaje = gr.Markdown()
    pista = gr.Gallery(show_label=False, columns=4, height="auto", allow_preview=False, object_fit="contain")
    gr.Markdown("### 👇 Toca el oficio")
    tablero = gr.Gallery([picto(o) for o in LISTA], show_label=False, columns=4, height="auto",
                         allow_preview=False, object_fit="contain")
    boton = gr.Button("🔄 Nueva partida", size="lg")

    salidas = [est, objetivo, pista, mensaje]
    demo.load(nueva_partida, outputs=salidas)
    boton.click(nueva_partida, outputs=salidas)
    tablero.select(elegir, inputs=[est, objetivo], outputs=salidas)

if __name__ == "__main__":
    demo.launch(allowed_paths=[str(PICTOS)])
