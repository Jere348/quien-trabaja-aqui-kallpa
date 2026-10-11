"""Descarga los pictogramas del juego desde la API de ARASAAC.

Genera datos/pictogramas/<palabra>.png y catalogo.json (palabra -> id ARASAAC).
Los ids registrados en catalogo.json tienen prioridad sobre la búsqueda automática.

Pictogramas: ARASAAC (https://arasaac.org), Gobierno de Aragón, licencia CC BY-NC-SA.
"""
import json
import urllib.parse
import urllib.request
from pathlib import Path

from experimento_a_agente import ATRIBUTOS, OFICIOS, tarjetas

CARPETA = Path(__file__).resolve().parent.parent / "datos" / "pictogramas"
CATALOGO = CARPETA / "catalogo.json"
API = "https://api.arasaac.org/v1/pictograms/es/search/"
IMG = "https://static.arasaac.org/pictograms/{0}/{0}_500.png"


def palabras():
    """Vocabulario completo: oficios y tokens de todas las pistas."""
    return sorted(set(OFICIOS) | {p for o in OFICIOS.values() for a in ATRIBUTOS for p in tarjetas(a, o[a])})


def main():
    CARPETA.mkdir(parents=True, exist_ok=True)
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8")) if CATALOGO.exists() else {}
    for p in palabras():
        if p not in catalogo:
            try:
                with urllib.request.urlopen(API + urllib.parse.quote(p), timeout=15) as r:
                    catalogo[p] = json.load(r)[0]["_id"]
            except Exception as e:
                print(f"  ✗ {p}: sin resultado ({e}) — búscalo a mano en arasaac.org")
                continue
        png = CARPETA / f"{p}.png"
        if not png.exists():
            urllib.request.urlretrieve(IMG.format(catalogo[p]), png)
            print(f"  ✓ {p} -> {catalogo[p]}")
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(catalogo)} pictogramas en {CARPETA}")


if __name__ == "__main__":
    main()
