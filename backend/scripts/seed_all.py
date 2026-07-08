"""
seed_all.py — Corre TODOS los seeds del proyecto, en el orden correcto.

Pensado para que un dev nuevo (o tú, tras recrear el volumen de Postgres) deje
la base de datos lista con un solo comando, en vez de correr cada script a mano.

Cada script individual sigue siendo idempotente por su cuenta — correr este
maestro varias veces no duplica nada.

Uso (desde grin_web/backend, con el venv activado y la BD migrada):
    python scripts/seed_all.py
o dentro del contenedor:
    docker compose exec api python scripts/seed_all.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Orden: primero catálogos/usuarios base, luego lo que depende de ellos.
SCRIPTS = [
    "seed_math.py",
    "seed_feriados_peru.py",
    "seed_personal_planner.py",
    "seed_usuarios.py",
    "seed_productos.py",
]


def main() -> None:
    for nombre in SCRIPTS:
        print(f"\n=== {nombre} ===")
        resultado = subprocess.run([sys.executable, str(SCRIPTS_DIR / nombre)])
        if resultado.returncode != 0:
            print(f"[ERROR] {nombre} falló (código {resultado.returncode}). Abortando.")
            sys.exit(resultado.returncode)
    print("\n[OK] Todos los seeds se ejecutaron correctamente.")


if __name__ == "__main__":
    main()
