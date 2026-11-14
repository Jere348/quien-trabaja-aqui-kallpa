"""Modelo principal: Q-Learning tabular que aprende qué pista dar en cada estado del juego.

Uso:
    python q_learning.py            Entrena y guarda datos/q_tabla.json
    python q_learning.py --jugar    Sesión en consola guiada por la política aprendida
    python q_learning.py --demo     Partidas de un jugador simulado, paso a paso
"""
import json
import random
import sys
from pathlib import Path

from entorno import (MIRA_BIEN, NIVELES_APOYO, PARTIDAS_SESION, PERFILES, acciones, clave, medir, nivel_apoyo,
                     partida_simulada, politica_id3, sesion_simulada)
from experimento_a_agente import OFICIOS, frase, humano, nuevo_estado, partida

TABLA = Path(__file__).resolve().parent.parent / "datos" / "q_tabla.json"
EPISODIOS, ALFA, OMEGA, GAMMA, EPSILON = 300_000, None, 0.85, 0.95, (1.0, 0.05)
FRACCION_EXPLORACION = 0.7
VARIEDAD = 0.25


def politica_q(Q, variedad=0.0, rng=random):
    """Política codiciosa sobre Q. Con variedad > 0 alterna entre las acciones casi igual de buenas.

    En estados que no se visitaron durante el entrenamiento recurre al baseline ID3.
    """
    def politica(est, objetivo):
        q = Q.get(clave(est, objetivo), {})
        validas = [a for a in acciones(est) if a in q]
        if not validas:
            return politica_id3(est, objetivo)
        mejor = max(q[a] for a in validas)
        return rng.choice([a for a in validas if q[a] >= mejor - variedad])
    return politica


def entrenar(episodios=EPISODIOS, alfa=ALFA, omega=OMEGA, gamma=GAMMA, epsilon=EPSILON, semilla=0, cada=5_000, evaluar_con=1_000):
    """Entrena con sesiones simuladas y exploración ε-codiciosa decreciente.

    Con alfa=None la tasa de aprendizaje decae con las visitas: α = N(s,a)^-omega.

    Retorna (Q, historia); historia guarda un punto de control cada `cada` partidas con el retorno
    y el éxito de la política codiciosa, el cambio medio de Q por actualización (α·|δ|) y la fracción
    de estados cuya acción codiciosa cambió.
    """
    rng = random.Random(semilla)
    perfiles = list(PERFILES.values())
    Q, visitas, marcha = {}, {}, {"eps": epsilon[0], "delta": 0.0, "pasos": 0}

    def explorar(est, objetivo):
        validas = acciones(est)
        if rng.random() < marcha["eps"]:
            return rng.choice(validas)
        q = Q.get(clave(est, objetivo), {})
        return max(validas, key=lambda a: q.get(a, 0.0))

    def aprender(s, a, r, s2, acciones2):
        q = Q.setdefault(s, {})
        futuro = max(Q.get(s2, {}).get(b, 0.0) for b in acciones2) if s2 else 0.0
        td = r + gamma * futuro - q.get(a, 0.0)
        visitas[s, a] = visitas.get((s, a), 0) + 1
        paso = (alfa or visitas[s, a] ** -omega) * td
        q[a] = q.get(a, 0.0) + paso
        marcha["delta"] += abs(paso)
        marcha["pasos"] += 1

    historia, codiciosa = [], {}
    for partidas in range(PARTIDAS_SESION, episodios + 1, PARTIDAS_SESION):
        avance = partidas / (FRACCION_EXPLORACION * episodios)
        marcha["eps"] = max(epsilon[1], epsilon[0] - (epsilon[0] - epsilon[1]) * avance)
        sesion_simulada(explorar, rng.choice(perfiles), rng, al_paso=aprender)
        if partidas % cada < PARTIDAS_SESION:
            nueva = {s: max(q, key=q.get) for s, q in Q.items()}
            cambios = sum(nueva[s] != codiciosa.get(s) for s in nueva) / len(nueva)
            codiciosa = nueva
            m = medir(politica_q(Q, rng=random.Random(semilla)), perfiles, evaluar_con, semilla=10_000 + semilla)
            historia.append({"episodio": partidas, "epsilon": marcha["eps"], "delta_q": marcha["delta"] / marcha["pasos"],
                             "cambios": cambios, "retorno": m["retorno"], "exito_3": m["exito_3"]})
            marcha["delta"], marcha["pasos"] = 0.0, 0
    return Q, historia


def guardar(Q, ruta=TABLA, **meta):
    tabla = {"|".join([o, ",".join(sorted(dadas)), str(fallos), str(apoyo)]): {a: round(v, 3) for a, v in q.items()}
             for (o, dadas, fallos, apoyo), q in sorted(Q.items(), key=lambda kv: (kv[0][0], sorted(kv[0][1]), kv[0][2:]))}
    ruta.write_text(json.dumps({"meta": meta, "q": tabla}, ensure_ascii=False, indent=0), encoding="utf-8")


def cargar(ruta=TABLA):
    """Carga la tabla Q entrenada; retorna None si aún no se ha entrenado."""
    if not ruta.exists():
        return None
    Q = {}
    for llave, q in json.loads(ruta.read_text(encoding="utf-8"))["q"].items():
        o, dadas, fallos, apoyo = llave.split("|")
        Q[o, frozenset(filter(None, dadas.split(","))), int(fallos), int(apoyo)] = q
    return Q


def con_traza(Q, politica):
    """Envuelve la política para mostrar el estado observado y los valores Q de cada acción."""
    def trazada(est, objetivo):
        a = politica(est, objetivo)
        q = Q.get(clave(est, objetivo), {})
        valores = "  ".join(f"{b}={q[b]:+.2f}{'★' if b == a else ''}" for b in acciones(est) if b in q)
        print(f"   🧠 fallos={est['fallos']} apoyo={NIVELES_APOYO[est['apoyo']]} | Q: {valores}")
        return a
    return trazada


def jugar(Q):
    """Sesión humana en consola: el apoyo se ajusta según los fallos de las partidas anteriores."""
    politica, historial = con_traza(Q, politica_q(Q, VARIEDAD)), []
    while True:
        print("\n=== ¿QUIÉN TRABAJA AQUÍ? ===")
        for i, o in enumerate(OFICIOS, 1):
            print(f"{i:>2}. [{o.upper()}]", end="\n" if i % 4 == 0 else "\t")
        est = nuevo_estado() | {"apoyo": nivel_apoyo(historial)}
        _, intentos = partida(random.choice(list(OFICIOS)), humano, politica=politica, est=est)
        historial.append(intentos - 1)
        if input("\n¿Otra partida? (s/n): ").strip().lower() != "s":
            break


def demo(Q, perfil="apoyo alto", partidas=3, semilla=6):
    """Muestra paso a paso cómo el agente guía a un jugador simulado."""
    rng = random.Random(semilla)
    politica, historial = con_traza(Q, politica_q(Q, VARIEDAD, rng)), []

    def narrar(est, a, respuesta, acierto):
        pista = "MIRA BIEN" if a == MIRA_BIEN else frase(a, OFICIOS[objetivo][a])
        print(f"   🤖 {pista}\n   👉 responde [{respuesta.upper()}] {'🎉 ¡Muy bien!' if acierto else '❌ No es.'}")

    for n in range(1, partidas + 1):
        objetivo = rng.choice(list(OFICIOS))
        print(f"\nPartida {n} · jugador simulado «{perfil}» · objetivo oculto: {objetivo}")
        res = partida_simulada(politica, PERFILES[perfil], rng, nivel_apoyo(historial), objetivo, narrar=narrar)
        historial.append(res["fallos"])


if __name__ == "__main__":
    if "--jugar" in sys.argv or "--demo" in sys.argv:
        Q = cargar() or sys.exit("Primero entrena el agente: python q_learning.py")
        jugar(Q) if "--jugar" in sys.argv else demo(Q)
    else:
        Q, historia = entrenar()
        guardar(Q, episodios=EPISODIOS, omega=OMEGA, gamma=GAMMA, epsilon=EPSILON, semilla=0)
        fin = historia[-1]
        print(f"Estados aprendidos: {len(Q)} | retorno medio: {fin['retorno']:.2f} | éxito en ≤3 intentos: {fin['exito_3']:.0%}")
        print(f"Tabla guardada en {TABLA}")
