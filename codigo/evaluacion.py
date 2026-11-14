"""Evaluación del agente: compara Q-Learning con el baseline ID3 y una política aleatoria.

Uso:
    python evaluacion.py    Escribe docs/resultados_hito2.json y las figuras en docs/figuras/
"""
import json
import random
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from entorno import MODELO, NIVELES_APOYO, PERFILES, medir, politica_aleatoria, politica_id3, sesion_simulada
from experimento_a_agente import FUERTES, OFICIOS
from q_learning import VARIEDAD, cargar, entrenar, politica_q

DOCS = Path(__file__).resolve().parent.parent / "docs"
FIGURAS = DOCS / "figuras"
SEMILLAS = range(5)
SESIONES = 5_000
COLOR = {"Q-Learning": "#2a78d6", "ID3 (baseline)": "#eb6834", "Aleatoria": "#1baf7a"}
TINTA, TENUE, REJILLA = "#0b0b0b", "#52514e", "#e6e5e0"
SENSIBILIDAD = {"α = 0,30 fija": {"alfa": 0.30}, "α = 0,10 fija": {"alfa": 0.10}, "α = 0,02 fija": {"alfa": 0.02},
                "α = N⁻⁰·⁶": {"omega": 0.6}, "α = N⁻⁰·⁸⁵ (elegida)": {"omega": 0.85}, "α = N⁻¹": {"omega": 1.0}}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": TENUE, "axes.labelcolor": TENUE,
                     "xtick.color": TENUE, "ytick.color": TENUE, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": REJILLA, "axes.axisbelow": True, "axes.titlecolor": TINTA,
                     "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left", "savefig.dpi": 200})


def politicas(Q):
    return {"Q-Learning": politica_q(Q, rng=random.Random(98)), "ID3 (baseline)": politica_id3,
            "Aleatoria": politica_aleatoria(random.Random(99))}


def comparar(Q):
    """Métricas por perfil de jugador para cada política, incluido un perfil no visto al entrenar."""
    grupos = {**{n: [p] for n, p in PERFILES.items()}, "no visto": [MODELO["perfil_no_visto"]],
              "mezcla": list(PERFILES.values())}
    return {g: {n: medir(p, perfiles, SESIONES, semilla=1) for n, p in politicas(Q).items()}
            for g, perfiles in grupos.items()}


def variedad(Q):
    """Pistas iniciales distintas por oficio y retorno, con y sin alternancia entre acciones casi iguales."""
    perfiles, salida = list(PERFILES.values()), {}
    for nombre, pol in {"ID3 (baseline)": politica_id3, "Q-Learning codiciosa": politica_q(Q, rng=random.Random(6)),
                        f"Q-Learning con variedad {VARIEDAD}": politica_q(Q, VARIEDAD, random.Random(7))}.items():
        rng, primeras, retornos = random.Random(3), {o: set() for o in OFICIOS}, []
        for i in range(SESIONES):
            for r in sesion_simulada(pol, perfiles[i % len(perfiles)], rng):
                primeras[r["objetivo"]].add(r["primera"])
                retornos.append(r["retorno"])
        salida[nombre] = {"primeras_distintas": statistics.mean(len(v) for v in primeras.values()),
                          "retorno": statistics.mean(retornos)}
    return salida


def politica_aprendida(Q):
    """Primera pista por oficio y nivel de apoyo, y cuánto cambia la política entre apoyo bajo y alto."""
    mejor = lambda s: max(Q[s], key=Q[s].get)
    primera = {o: [mejor((o, frozenset(), 0, ap)) for ap in range(len(NIVELES_APOYO))] for o in OFICIOS}
    comunes = [s for s in Q if s[3] == 0 and (*s[:3], 2) in Q]
    return {"primera_pista": primera,
            "primera_es_fuerte": [sum(p[ap] in FUERTES for p in primera.values()) for ap in range(len(NIVELES_APOYO))],
            "estados_comparables": len(comunes),
            "estados_distintos_bajo_alto": sum(mejor(s) != mejor((*s[:3], 2)) for s in comunes),
            "estados": len(Q)}


def sensibilidad():
    """Retorno final y estabilidad de la política según la tasa de aprendizaje (3 semillas)."""
    salida = {}
    for nombre, kw in SENSIBILIDAD.items():
        finales = [entrenar(semilla=s, cada=50_000, **kw)[1][-1] for s in range(3)]
        salida[nombre] = {"retorno": statistics.mean(f["retorno"] for f in finales),
                          "cambios": statistics.mean(f["cambios"] for f in finales)}
    return salida


def banda(ax, x, series, color):
    media = [statistics.mean(v) for v in zip(*series)]
    desv = [statistics.stdev(v) for v in zip(*series)]
    ax.fill_between(x, [m - d for m, d in zip(media, desv)], [m + d for m, d in zip(media, desv)], color=color, alpha=.18, lw=0)
    ax.plot(x, media, color=color, lw=2)
    return media


def figura_aprendizaje(historias, comparacion):
    x = [h["episodio"] / 1000 for h in historias[0]]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    media = banda(ax, x, [[h["retorno"] for h in hist] for hist in historias], COLOR["Q-Learning"])
    ax.annotate("Q-Learning (política codiciosa)", (x[-1], media[-1]), xytext=(-4, 9), textcoords="offset points",
                ha="right", color=TINTA)
    for nombre in ("ID3 (baseline)", "Aleatoria"):
        y = comparacion["mezcla"][nombre]["retorno"]
        ax.axhline(y, color=COLOR[nombre], lw=2, ls=(0, (5, 3)))
        ax.annotate(nombre, (x[-1], y), xytext=(-4, 5), textcoords="offset points", ha="right", color=TINTA)
    ax.set(title="Retorno medio por partida durante el entrenamiento", xlabel="Partidas de entrenamiento (miles)",
           ylabel="Retorno medio", xlim=(0, x[-1]))
    fig.text(.01, .01, "Media y desviación estándar de 5 semillas; evaluación sin exploración sobre 1 000 sesiones.",
             color=TENUE, fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(FIGURAS / "fig1_curva_aprendizaje.png")


def figura_convergencia(historias):
    x = [h["episodio"] / 1000 for h in historias[0]]
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.2))
    paneles = [("delta_q", "Cambio medio de Q (α·|δ|)", 1), ("cambios", "Estados que cambian de acción (%)", 100),
               ("epsilon", "Exploración ε", 1)]
    for ax, (campo, titulo, escala) in zip(ejes, paneles):
        banda(ax, x, [[h[campo] * escala for h in hist] for hist in historias], COLOR["Q-Learning"])
        ax.set(title=titulo, xlabel="Partidas (miles)", xlim=(0, x[-1]))
        if campo != "delta_q":
            ax.set_ylim(bottom=0)
    ejes[0].set_yscale("log")
    ejes[1].set_ylim(0, 40)
    fig.tight_layout(w_pad=3)
    fig.savefig(FIGURAS / "fig2_convergencia.png")


def figura_comparacion(comparacion):
    perfiles = [*PERFILES, "no visto"]
    paneles = [("primer_intento", "Acierto al primer intento (%)", 100, "{:.0f}"), ("intentos", "Intentos por partida", 1, "{:.2f}"),
               ("sin_fuerte", "Resueltas sin pista fuerte (%)", 100, "{:.0f}")]
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.5))
    ancho = .26
    for ax, (campo, titulo, escala, fmt) in zip(ejes, paneles):
        for i, nombre in enumerate(COLOR):
            valores = [comparacion[p][nombre][campo] * escala for p in perfiles]
            barras = ax.bar([j + (i - 1) * ancho for j in range(len(perfiles))], valores, ancho - .03, color=COLOR[nombre],
                            label=nombre)
            ax.bar_label(barras, [fmt.format(v) for v in valores], fontsize=7, color=TINTA, padding=2)
        ax.set(title=titulo, xticks=range(len(perfiles)), xticklabels=[p.replace(" ", "\n") for p in perfiles])
        ax.grid(axis="x", visible=False)
        ax.margins(y=.12)
    ejes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig3_comparacion.png")


if __name__ == "__main__":
    Q = cargar() or sys.exit("Primero entrena el agente: python q_learning.py")
    FIGURAS.mkdir(parents=True, exist_ok=True)
    historias = [entrenar(semilla=s)[1] for s in SEMILLAS]
    resultados = {"comparacion": comparar(Q), "variedad": variedad(Q), "politica": politica_aprendida(Q),
                  "sensibilidad": sensibilidad(), "historia_semilla_0": historias[0],
                  "retorno_final_semillas": [h[-1]["retorno"] for h in historias]}
    (DOCS / "resultados_hito2.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
    figura_aprendizaje(historias, resultados["comparacion"])
    figura_convergencia(historias)
    figura_comparacion(resultados["comparacion"])
    for perfil, fila in resultados["comparacion"].items():
        print(f"\n{perfil}")
        for nombre, m in fila.items():
            print(f"  {nombre:15} retorno {m['retorno']:5.2f} | éxito≤3 {m['exito_3']:.1%} | 1er intento {m['primer_intento']:.1%}"
                  f" | intentos {m['intentos']:.2f} | pistas {m['pistas']:.2f} | sin fuerte {m['sin_fuerte']:.1%}")
