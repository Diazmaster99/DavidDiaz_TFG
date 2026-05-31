# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
"""
Arranca un entrenamiento de SELF-PLAY a partir de un modelo YA ENTRENADO.

Copia el último checkpoint de un modelo de origen a un seed nuevo marcado con un
sufijo (por defecto 'selfplay'), de modo que:
  - el modelo de self-play no sobrescribe al de origen (vs random/heurístico),
  - la carpeta y el run de TensorBoard quedan claramente diferenciados
    (p.ej. models/doubles/<formato>/mlp/seed1_selfplay/ y el run
    'doubles_seed1_selfplay'),
  - el entrenamiento se reanuda desde ese checkpoint y continúa con --opponent self.

Uso típico (dobles, MLP, partiendo del modelo de seed1, formato VGC):
    python selfplay_from.py --mode doubles --format gen9vgc2026regi --policy mlp \\
        --src_seed 1 --team teams/vgc/reg_i --total_steps 1500000

Solo copiar y mostrar el comando (sin lanzar):
    python selfplay_from.py --mode doubles --src_seed 1 --no-launch

Requisitos para lanzar: servidor Showdown corriendo (lo comprueba train_*.py).
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def latest_numbered_checkpoint(folder: Path):
    """Devuelve (ruta, pasos) del checkpoint numerado más avanzado, o (None, -1)."""
    best, best_steps = None, -1
    for p in folder.glob("model_*_steps.zip"):
        m = re.search(r"model_(\d+)_steps", p.stem)
        if m and int(m.group(1)) > best_steps:
            best, best_steps = p, int(m.group(1))
    return best, best_steps


def main():
    ap = argparse.ArgumentParser(description="Copia un modelo entrenado a un seed "
                                             "nuevo y lanza self-play diferenciado.")
    ap.add_argument("--mode", choices=["doubles", "singles"], default="doubles",
                    help="Modo de combate (default: doubles)")
    ap.add_argument("--format", dest="battle_format", default="gen9vgc2026regi",
                    help="Formato de batalla (default: gen9vgc2026regi)")
    ap.add_argument("--policy", choices=["mlp", "transformer"], default="mlp",
                    help="Arquitectura (default: mlp)")
    ap.add_argument("--src_seed", type=int, required=True,
                    help="Seed del modelo ya entrenado de origen (por ejemplo el de vs heurístico)")
    ap.add_argument("--dst_seed", type=int, default=None,
                    help="Seed destino (default: el mismo que src_seed; la carpeta llevará el sufijo)")
    ap.add_argument("--tag", default="selfplay",
                    help="Sufijo que diferencia el modelo de self-play (default: selfplay)")
    ap.add_argument("--team", default=None,
                    help="Equipo VGC (fichero .txt o carpeta). Necesario para formatos no aleatorios.")
    ap.add_argument("--total_steps", type=int, default=1_500_000,
                    help="Pasos totales objetivo del run de self-play (incluye los ya entrenados). "
                         "Debe ser mayor que los pasos del checkpoint de origen.")
    ap.add_argument("--save_interval", type=int, default=20_000)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--no-launch", dest="no_launch", action="store_true",
                    help="Solo copia el checkpoint y muestra el comando, sin entrenar.")
    args = ap.parse_args()

    dst_seed = args.dst_seed if args.dst_seed is not None else args.src_seed
    base = Path("models") / args.mode / args.battle_format / args.policy
    src = base / f"seed{args.src_seed}"
    dst = base / f"seed{dst_seed}_{args.tag}"

    if not src.exists():
        sys.exit(f"ERROR: no existe la carpeta de origen: {src}")

    ckpt, steps = latest_numbered_checkpoint(src)
    if ckpt is None:
        final = src / "final.zip"
        msg = f"ERROR: no se encontraron checkpoints numerados (model_<N>_steps.zip) en {src}."
        if final.exists():
            msg += ("\n  Hay un 'final.zip' sin número de pasos: el reanudado no lo detecta. "
                    "Renómbralo a 'model_<N>_steps.zip' (con N = pasos entrenados) y reintenta.")
        sys.exit(msg)

    if args.total_steps <= steps:
        sys.exit(f"ERROR: --total_steps ({args.total_steps}) debe ser MAYOR que los pasos "
                 f"del checkpoint de origen ({steps}); si no, no se entrenaría nada.")

    dst.mkdir(parents=True, exist_ok=True)
    target = dst / ckpt.name
    shutil.copy2(ckpt, target)
    print(f"OK  Copiado checkpoint de origen:\n     {ckpt}  ({steps} pasos)\n  -> {target}")

    train_script = f"train_{args.mode}.py"
    cmd = [sys.executable, train_script,
           "--format", args.battle_format,
           "--policy", args.policy,
           "--opponent", "self",
           "--run_id", str(dst_seed),
           "--tag", args.tag,
           "--total_steps", str(args.total_steps),
           "--save_interval", str(args.save_interval),
           "--port", str(args.port),
           "--device", args.device]
    if args.team:
        cmd += ["--team", args.team]

    print("\nComando de self-play:\n  " + " ".join(cmd))
    if args.no_launch:
        print("\n(--no-launch) No se lanza el entrenamiento. Copia hecha y lista para reanudar.")
        return
    print("\nLanzando self-play (Ctrl+C para abortar)...\n")
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
