# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Genera las figuras de métricas de entrenamiento a partir de los logs de
TensorBoard (event files) y las guarda como PNG en la carpeta 'metrics/'.

No hace falta exportar nada a mano desde la web de TensorBoard: este script
lee directamente los event files de 'logs/'.

Detecta automáticamente todos los runs (cada carpeta con event files: distintas
seeds, mlp/transformer, etc.) y superpone sus curvas en una misma figura, con
leyenda, para poder compararlos.

Uso básico:
    python plot_metrics.py

Acotar a un subconjunto de logs (recomendado para una figura limpia):
    python plot_metrics.py --logdir logs/doubles/gen9vgc2026regi/mlp
    python plot_metrics.py --logdir logs/doubles/gen9vgc2026regi --outdir metrics/doubles

Opciones:
    --logdir   Carpeta raíz de logs a explorar (default: logs)
    --outdir   Carpeta de salida de las imágenes (default: metrics)
    --smooth   Suavizado exponencial 0..1 estilo TensorBoard (default: 0.9; 0 = sin suavizar)
    --dpi      Resolución de las imágenes (default: 200)

Requiere: matplotlib y tensorboard
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventana, solo guarda fichero
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

# Métricas ordenadas
# tag de TensorBoard -> (título, etiqueta del eje Y, nombre de fichero)
METRICS = [
    ("eval/win_rate",
     ("Tasa de victorias (media móvil)", "Tasa de victorias", "01_tasa_victorias")),
    ("rollout/ep_rew_mean",
     ("Recompensa media por episodio", "Recompensa media", "02_recompensa_media")),
    ("rollout/ep_len_mean",
     ("Duración media del combate", "Turnos por combate", "03_duracion_combate")),
    ("train/explained_variance",
     ("Varianza explicada por el crítico", "Varianza explicada", "04_varianza_explicada")),
    ("train/entropy_loss",
     ("Entropía de la política", "Pérdida de entropía", "05_entropia")),
    ("train/value_loss",
     ("Pérdida de la función de valor", "Pérdida de valor", "06_perdida_valor")),
    ("train/approx_kl",
     ("Divergencia KL aproximada (estabilidad de PPO)", "KL aproximada", "07_kl")),
    ("train/learning_rate",
     ("Tasa de aprendizaje (decaimiento lineal)", "Tasa de aprendizaje", "08_learning_rate")),
]


def _fmt_steps(x, _pos):
    """Formatea el eje X de pasos: 0, 200k, 400k, ..., 1M, 1.5M (sin '1e6')."""
    if x >= 1_000_000:
        v = x / 1_000_000
        return f"{v:.0f}M" if abs(v - round(v)) < 1e-9 else f"{v:.1f}M"
    if x >= 1_000:
        v = x / 1_000
        return f"{v:.0f}k" if abs(v - round(v)) < 1e-9 else f"{v:.1f}k"
    return f"{int(round(x))}"


def find_runs(logdir: Path) -> dict:
    """Devuelve {etiqueta: carpeta} por cada directorio que contenga event files."""
    runs = {}
    for ev in logdir.rglob("events.out.tfevents.*"):
        d = ev.parent
        if d in runs.values():
            continue
        try:
            rel = d.relative_to(logdir)
        except ValueError:
            rel = Path(d.name)
        # ignora carpetas archivadas/ocultas (componentes que empiezan por _ o .)
        if any(part.startswith(("_", ".")) for part in rel.parts):
            continue
        label = str(rel).replace("\\", "/")
        if label in (".", ""):
            label = logdir.name
        runs[label] = d
    return runs


def load_scalar(run_dir: Path, tag: str):
    """Carga (steps, values) de un escalar, fusionando todos los event files
    de la carpeta, ordenando por step y quedándose con el último valor de cada
    step (las reanudaciones generan varios ficheros con steps solapados)."""
    acc = EventAccumulator(str(run_dir), size_guidance={"scalars": 0})
    acc.Reload()
    if tag not in acc.Tags().get("scalars", []):
        return None, None
    by_step = {}
    for e in acc.Scalars(tag):
        by_step[e.step] = e.value  # el último valor escrito para ese step gana
    steps = sorted(by_step)
    values = [by_step[s] for s in steps]
    return steps, values


def ema(values, alpha):
    """Suavizado exponencial estilo TensorBoard. alpha en [0, 1)."""
    if not values or alpha <= 0:
        return list(values)
    out = []
    acc = values[0]
    for v in values:
        acc = alpha * acc + (1 - alpha) * v
        out.append(acc)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Genera PNGs de las métricas desde los logs de TensorBoard."
    )
    ap.add_argument("--logdir", default="logs", help="Carpeta raíz de logs (default: logs)")
    ap.add_argument("--outdir", default="metrics", help="Carpeta de salida (default: metrics)")
    ap.add_argument("--smooth", type=float, default=0.9,
                    help="Suavizado EMA 0..1 (default: 0.9; 0 = sin suavizado)")
    ap.add_argument("--dpi", type=int, default=200, help="Resolución de las imágenes (default: 200)")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="Excluye los runs cuyo nombre contenga alguna de estas subcadenas "
                         "(p.ej. --exclude transformer  o  --exclude seed2 selfplay).")
    ap.add_argument("--include", nargs="*", default=[],
                    help="Si se indica, SOLO se grafican los runs cuyo nombre contenga alguna "
                         "de estas subcadenas.")
    args = ap.parse_args()

    logdir = Path(args.logdir)
    outdir = Path(args.outdir)
    if not logdir.exists():
        print(f"ERROR: no existe la carpeta de logs '{logdir}'.")
        return
    outdir.mkdir(parents=True, exist_ok=True)

    runs = find_runs(logdir)
    if not runs:
        print(f"No se encontraron event files de TensorBoard en '{logdir}'.")
        return

    # Filtrado por nombre: --include (lista blanca) y --exclude (lista negra).
    if args.include:
        runs = {lab: d for lab, d in runs.items()
                if any(s.lower() in lab.lower() for s in args.include)}
    if args.exclude:
        runs = {lab: d for lab, d in runs.items()
                if not any(s.lower() in lab.lower() for s in args.exclude)}
    if not runs:
        print("Tras aplicar --include/--exclude no queda ningún run que graficar.")
        return

    print(f"Runs a graficar ({len(runs)}) en '{logdir}':")
    for label in sorted(runs):
        print(f"  - {label}")
    print()

    generated = 0
    for tag, (title, ylabel, fname) in METRICS:
        series = []
        for label, d in sorted(runs.items()):
            steps, values = load_scalar(d, tag)
            if steps:
                series.append((label, steps, values))
        if not series:
            print(f"(omitida) ningún run tiene la métrica '{tag}'")
            continue

        plt.figure(figsize=(7, 4))
        for label, steps, values in series:
            sm = ema(values, args.smooth)
            line, = plt.plot(steps, sm, linewidth=1.8, label=label)
            if args.smooth > 0:  # rastro tenue con los datos sin suavizar
                plt.plot(steps, values, linewidth=0.8, alpha=0.20, color=line.get_color())

        plt.xlabel("Pasos de entrenamiento")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(True, alpha=0.3)
        # Eje X en 0 / 200k / ... / 1M en vez de 0.2 ... y sin el offset '1e6'.
        plt.gca().xaxis.set_major_formatter(FuncFormatter(_fmt_steps))
        if len(series) > 1:
            plt.legend(fontsize=7)
        plt.tight_layout()
        out = outdir / f"{fname}.png"
        plt.savefig(out, dpi=args.dpi)
        plt.close()
        generated += 1
        print(f"OK  {out}  ({len(series)} curva/s)")

    print(f"\nListo: {generated} figura(s) guardada(s) en '{outdir}'.")


if __name__ == "__main__":
    main()
