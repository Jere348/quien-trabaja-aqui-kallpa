"""Entorno del juego como proceso de decisión de Markov (MDP) y jugador simulado.

Estado     s = (objetivo, pistas dadas, fallos de la partida, nivel de apoyo de la sesión)
Acciones   A(s) = pistas aún no dadas; "lugar" queda para el final y, agotadas todas, "mira_bien"
Transición el jugador simulado interpreta la pista y responde en el tablero
Recompensa premio por acierto, costo por pista (mayor si es fuerte) y frustración del jugador por fallo
"""
import json
import random
from pathlib import Path

from experimento_a_agente import ATRIBUTOS, FUERTES, OFICIOS, elegir_pista, evaluar, nuevo_estado

MODELO = json.loads((Path(__file__).resolve().parent.parent / "datos" / "modelo_jugador.json").read_text(encoding="utf-8"))
PERFILES = MODELO["perfiles"]
RECOMPENSA = MODELO["recompensa"]
ULTIMA = MODELO["ultima_pista"]
MAX_TURNOS = MODELO["max_turnos"]
PARTIDAS_SESION = MODELO["partidas_por_sesion"]
MIRA_BIEN = "mira_bien"
MAX_FALLOS_ESTADO = 3
NIVELES_APOYO = ("bajo", "medio", "alto")


def nivel_apoyo(historial):
    """Nivel de apoyo (0 bajo, 1 medio, 2 alto) según los fallos de las últimas 3 partidas."""
    if not historial:
        return 1
    recientes = historial[-3:]
    media = sum(recientes) / len(recientes)
    return sum(media >= u for u in MODELO["umbrales_apoyo"])


def clave(est, objetivo):
    """Estado observable por el agente, usado como llave de la tabla Q."""
    return objetivo, frozenset(est["dadas"]), min(est["fallos"], MAX_FALLOS_ESTADO), est["apoyo"]


def acciones(est):
    """Acciones válidas: nunca se repite una pista y la última pista se reserva para el final."""
    libres = [a for a in ATRIBUTOS if a not in est["dadas"]]
    return [a for a in libres if a != ULTIMA] or libres or [MIRA_BIEN]


def costo(accion):
    if accion == MIRA_BIEN:
        return RECOMPENSA["mira_bien"]
    return RECOMPENSA["pista_fuerte" if accion in FUERTES else "pista"]


def politica_id3(est, objetivo):
    """Baseline del Hito 1: ganancia de información con pistas fuertes tras dos fallos."""
    return elegir_pista(est) or MIRA_BIEN


def politica_aleatoria(rng):
    return lambda est, objetivo: rng.choice(acciones(est))


class Jugador:
    """Jugador simulado: entiende cada pista con cierta probabilidad y a veces responde por despiste.

    P(entender) = comprension ** dificultad: a mayor necesidad de apoyo, las pistas abstractas
    se pierden mucho más que las concretas.
    """

    def __init__(self, perfil, rng):
        self.dificultad, self.despiste, self.frustracion = perfil["dificultad"], perfil["despiste"], perfil["frustracion"]
        self.rng = rng
        self.creencia = set(OFICIOS)

    def recibir(self, accion, valor, compatibles):
        """Actualiza la creencia con los oficios compatibles si la pista fue comprendida."""
        base = MODELO["comprension"].get(f"{accion}:{valor}", MODELO["comprension"][accion])
        if self.rng.random() < base ** self.dificultad:
            self.creencia &= compatibles

    def responder(self, malos):
        opciones = set(OFICIOS) if self.rng.random() < self.despiste else self.creencia
        return self.rng.choice(sorted(opciones - malos))


def partida_simulada(politica, perfil, rng, apoyo=1, objetivo=None, al_paso=None, narrar=None):
    """Simula una partida completa y devuelve sus métricas.

    al_paso(s, a, r, s2, acciones2) se invoca en cada transición; s2 es None en estado terminal.
    narrar(est, accion, respuesta, acierto) permite mostrar la partida paso a paso.
    """
    objetivo = objetivo or rng.choice(list(OFICIOS))
    est = nuevo_estado() | {"apoyo": apoyo}
    jugador, malos = Jugador(perfil, rng), set()
    retorno, fuerte, acierto, primera = 0.0, False, False, None
    for turno in range(1, MAX_TURNOS + 1):
        s, a = clave(est, objetivo), politica(est, objetivo)
        primera = primera or a
        if a == MIRA_BIEN:
            jugador.recibir(a, None, est["cands"])
        else:
            valor = OFICIOS[objetivo][a]
            est["dadas"].add(a)
            est["cands"] = {o for o in est["cands"] if OFICIOS[o][a] == valor}
            jugador.recibir(a, valor, {o for o in OFICIOS if OFICIOS[o][a] == valor})
        fuerte = fuerte or a in FUERTES or a == MIRA_BIEN
        respuesta = jugador.responder(malos)
        acierto = evaluar(est, objetivo, respuesta)
        malos.add(respuesta)
        if narrar:
            narrar(est, a, respuesta, acierto)
        r = costo(a) + (RECOMPENSA["acierto"] if acierto else -jugador.frustracion)
        retorno += r
        fin = acierto or turno == MAX_TURNOS
        if al_paso:
            al_paso(s, a, r, None if fin else clave(est, objetivo), None if fin else acciones(est))
        if fin:
            break
    return {"objetivo": objetivo, "retorno": retorno, "intentos": turno, "fallos": est["fallos"],
            "pistas": len(est["dadas"]), "resuelta": acierto, "sin_fuerte": acierto and not fuerte,
            "primera": primera}


def sesion_simulada(politica, perfil, rng, al_paso=None, partidas=PARTIDAS_SESION):
    """Simula una sesión: el nivel de apoyo se actualiza con el desempeño de las partidas previas."""
    historial, resultados = [], []
    for _ in range(partidas):
        res = partida_simulada(politica, perfil, rng, nivel_apoyo(historial), al_paso=al_paso)
        historial.append(res["fallos"])
        resultados.append(res)
    return resultados


def medir(politica, perfiles, sesiones, semilla=0):
    """Métricas medias de una política sobre sesiones simuladas, repartidas entre los perfiles dados."""
    rng = random.Random(semilla)
    res = [r for i in range(sesiones) for r in sesion_simulada(politica, perfiles[i % len(perfiles)], rng)]
    n = len(res)
    return {
        "retorno": sum(r["retorno"] for r in res) / n,
        "resueltas": sum(r["resuelta"] for r in res) / n,
        "exito_3": sum(r["resuelta"] and r["intentos"] <= 3 for r in res) / n,
        "primer_intento": sum(r["resuelta"] and r["intentos"] == 1 for r in res) / n,
        "intentos": sum(r["intentos"] for r in res) / n,
        "pistas": sum(r["pistas"] for r in res) / n,
        "sin_fuerte": sum(r["sin_fuerte"] for r in res) / n,
    }
