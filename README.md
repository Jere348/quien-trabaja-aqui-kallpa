# ¿Quién trabaja aquí? — Kallpa-Play AI

Juego de mesa adaptado con pictogramas para la **Asociación Educativa Kallpa** (Inteligencia Artificial 1ASI0404, UPC 2026-20).
El agente da pistas en pictogramas y voz, y guía al jugador hasta adivinar el oficio.

- **Baseline (Hito 1):** elige la pista por ganancia de información (ID3).
- **Modelo principal (Hito 2):** Q-Learning que aprende qué pista dar según el oficio, los fallos de la partida y el nivel de apoyo que necesita el jugador.

## Cómo probarlo

Se necesita Python 3.9 o superior. Los comandos se ejecutan desde la carpeta del proyecto.

### Linux / macOS

```bash
git clone https://github.com/Jere348/quien-trabaja-aqui-kallpa.git
cd quien-trabaja-aqui-kallpa
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd codigo
python juego.py
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Jere348/quien-trabaja-aqui-kallpa.git
cd quien-trabaja-aqui-kallpa
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd codigo
python juego.py
```

Si PowerShell no deja activar el entorno, ejecuta antes `Set-ExecutionPolicy -Scope Process RemoteSigned`.
En el símbolo del sistema (cmd) el entorno se activa con `.venv\Scripts\activate.bat`.

Luego abre http://127.0.0.1:7860 en el navegador y toca la pantalla una vez para que suene la voz.
El juego ya trae la tabla Q entrenada (`datos/q_tabla.json`) y las voces (`datos/audio/`), así que funciona sin internet.

## Entrenar y evaluar el agente

Con el entorno activado y dentro de `codigo/` (los comandos son iguales en Linux y Windows):

```bash
python experimento_a_agente.py          # Hito 1: partida en consola con el baseline ID3
python experimento_a_agente.py --sim    # Hito 1: métricas del baseline con jugador ideal
python q_learning.py                    # entrena Q-Learning y guarda datos/q_tabla.json (~5 s)
python q_learning.py --demo             # partidas guiadas paso a paso con jugador simulado
python q_learning.py --jugar            # sesión en consola con la política aprendida
python evaluacion.py                    # métricas y figuras en docs/ (~2 min)
python descargar_pictogramas.py         # vuelve a bajar pictogramas faltantes de ARASAAC
```

En Windows, si la consola no muestra bien los emojis o las tildes, ejecuta antes `chcp 65001`.

## Estructura

- `codigo/`
  - `experimento_a_agente.py` — reglas del juego y baseline ID3
  - `entorno.py` — el juego como MDP y jugador simulado
  - `q_learning.py` — entrenamiento y política del agente
  - `evaluacion.py` — comparación con el baseline, convergencia y figuras
  - `juego.py` — interfaz de pictogramas con voz, conectada al agente
  - `descargar_pictogramas.py` — descarga del catálogo ARASAAC
- `datos/`
  - `escenarios.json` — 12 oficios y sus atributos
  - `modelo_jugador.json` — supuestos del jugador simulado y de la recompensa
  - `q_tabla.json` — tabla Q entrenada
  - `pictogramas/`, `audio/` — catálogo ARASAAC y voces
  - `registro/partidas.csv` — se crea al jugar; registro anónimo de cada turno (no se sube al repositorio)
- `docs/` — informe técnico del Hito 2, resultados y figuras

## Ramas

- `main` — solo versiones entregadas
- `develop` — integración; aquí se juntan los avances
- `hito-1`, `hito-2`, ... — trabajo de cada hito; se une a `develop` con Pull Request

## Créditos

Pictogramas: Sergio Palao. Procedencia: [ARASAAC](https://arasaac.org). Licencia: CC BY-NC-SA. Propiedad: Gobierno de Aragón (España).
