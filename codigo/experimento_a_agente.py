"""Experimento A - Agente guía en consola para "¿Quién trabaja aquí?" (Kallpa-Play AI).

Baseline: en cada turno el agente da la pista con mayor Ganancia de Información (ID3)
sobre los oficios que todavía son posibles. Las pistas fuertes (herramienta y, al final,
lugar) se guardan para cuando el jugador falla varias veces, así nadie se queda atascado.

  python experimento_a_agente.py         -> jugar una partida
  python experimento_a_agente.py --sim   -> simular 1000 partidas y medir
"""
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

DATOS = json.loads((Path(__file__).resolve().parent.parent / "datos" / "escenarios.json").read_text(encoding="utf-8"))
OFICIOS = {o["oficio"]: o for o in DATOS["oficios"]}
ATRIBUTOS = DATOS["atributos"]
FRASES = DATOS["frases"]
FUERTES = DATOS["pistas_fuertes"]  # en orden: la última es la más fácil
FALLOS_FUERTE = DATOS["fallos_para_pista_fuerte"]

# Cada oficio debe poder distinguirse de los demás, si no el juego no tiene solución.
assert len({tuple(o[a] for a in ATRIBUTOS) for o in OFICIOS.values()}) == len(OFICIOS), "hay oficios con atributos idénticos"


def ganancia(cands, attr):
    """ID3: H(C) - H(C|A). Con oficios equiprobables H(C) = log2 n y H(C|A=v) = log2 n_v."""
    n = len(cands)
    conteo = Counter(OFICIOS[o][attr] for o in cands)
    return math.log2(n) - sum(nv / n * math.log2(nv) for nv in conteo.values())


def elegir_pista(est):
    """Estrategia de guía: mejor pista por entropía; las pistas fuertes se guardan como ayuda extra."""
    utiles = [a for a in ATRIBUTOS if a not in est["dadas"] and a not in FUERTES and ganancia(est["cands"], a) > 0]
    fuertes = [a for a in FUERTES if a not in est["dadas"]]
    if fuertes and (est["fallos"] >= FALLOS_FUERTE or not utiles):
        return fuertes[0]
    return max(utiles, key=lambda a: ganancia(est["cands"], a), default=None)


def tarjetas(attr, valor):
    """Palabras de la pista, una por tarjeta de pictograma: ["trabaja", "en", "hospital"]."""
    return FRASES.get(f"{attr}:{valor}", FRASES[attr]).format(valor).lower().split()


def frase(attr, valor):
    """Frase en pictogramas: cada palabra es una tarjeta, ej. [TRABAJA] + [EN] + [HOSPITAL]."""
    return " + ".join(f"[{p.upper()}]" for p in tarjetas(attr, valor))


def nuevo_estado():
    """Estado = (candidatos posibles, pistas dadas, fallos)."""
    return {"cands": set(OFICIOS), "dadas": set(), "fallos": 0}


def dar_pista(est, objetivo):
    """Elige la siguiente pista y actualiza el estado. Devuelve (atributo, valor) o None si no quedan."""
    attr = elegir_pista(est)
    if not attr:
        return None
    valor = OFICIOS[objetivo][attr]
    est["dadas"].add(attr)
    est["cands"] = {o for o in est["cands"] if OFICIOS[o][attr] == valor}
    return attr, valor


def evaluar(est, objetivo, respuesta):
    """Transición tras la respuesta del jugador. True = victoria."""
    if respuesta == objetivo:
        return True
    est["fallos"] += 1
    est["cands"].discard(respuesta)
    return False


def partida(objetivo, responder, decir=print):
    """Juega una partida en consola. Devuelve (pistas, intentos)."""
    est = nuevo_estado()
    while True:
        pista = dar_pista(est, objetivo)
        if pista:
            decir(f"\n🤖 Pista: {frase(*pista)}")
        else:
            decir(f"\n🤖 Mira bien: {' / '.join(f'[{c.upper()}]' for c in sorted(est['cands']))}")
        r = responder(est)
        if evaluar(est, objetivo, r):
            decir(f"🎉 ¡Muy bien! Es el [{objetivo.upper()}]")
            return len(est["dadas"]), est["fallos"] + 1
        decir(f"🤖 No es [{r.upper()}]. ¡Intenta otra vez!")


def humano(est):
    lista = list(OFICIOS)
    while True:
        r = input("👉 ¿Quién es? (número o nombre): ").strip().lower()
        if r.isdigit() and 1 <= int(r) <= len(lista):
            return lista[int(r) - 1]
        if r in OFICIOS:
            return r
        print("No entendí, escribe un número del tablero.")


def simular(n=1000):
    """Jugador simulado que elige al azar entre los oficios que siguen siendo posibles."""
    random.seed(0)
    res = [partida(random.choice(list(OFICIOS)), lambda est: random.choice(sorted(est["cands"])), decir=lambda *_: None)
           for _ in range(n)]
    pistas, intentos = zip(*res)
    assert max(intentos) <= len(OFICIOS), "una partida no terminó a tiempo"
    print(f"Partidas: {n} | éxito: 100%")
    print(f"Pistas promedio: {sum(pistas) / n:.2f} | intentos promedio: {sum(intentos) / n:.2f}")
    print(f"Acierta al primer intento: {intentos.count(1) / n:.0%} | máx. intentos: {max(intentos)}")


if __name__ == "__main__":
    if "--sim" in sys.argv:
        simular()
    else:
        print("=== ¿QUIÉN TRABAJA AQUÍ? ===")
        for i, o in enumerate(OFICIOS, 1):
            print(f"{i:>2}. [{o.upper()}]", end="\n" if i % 4 == 0 else "\t")
        partida(random.choice(list(OFICIOS)), humano)
