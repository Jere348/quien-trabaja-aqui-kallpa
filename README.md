# ¿Quién trabaja aquí? — Kallpa-Play AI

Juego de mesa adaptado con pictogramas para la **Asociación Educativa Kallpa** (Inteligencia Artificial 1ASI0404, UPC 2026-20).
El agente da pistas en pictogramas (ID3 / ganancia de información) y guía al jugador hasta adivinar el oficio.

## Ejecutar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd codigo
python3 experimento_a_agente.py          # Experimento A: partida en consola
python3 experimento_a_agente.py --sim    # métricas sobre 1000 partidas simuladas
../.venv/bin/python experimento_b_matriz.py   # Experimento B: matriz de pictogramas (http://127.0.0.1:7860)
python3 descargar_pictogramas.py         # vuelve a bajar pictogramas faltantes de ARASAAC
```

## Estructura

- `codigo/` — agente, matriz de selección y descarga de pictogramas
- `datos/` — `escenarios.json` (12 oficios) y `pictogramas/`
- `docs/` — informes en PDF

## Ramas

- `main` — solo versiones entregadas (tags `hito-1`, `hito-2`, `hito-3`)
- `develop` — integración; aquí se juntan los avances
- `hito-1`, `hito-2`, ... — trabajo de cada hito; se une a `develop` con Pull Request

## Créditos

Pictogramas: Sergio Palao. Procedencia: [ARASAAC](https://arasaac.org). Licencia: CC BY-NC-SA. Propiedad: Gobierno de Aragón (España).
