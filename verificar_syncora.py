"""Verificación local de Syncora (El Poli) antes de una entrega.

Uso, desde la carpeta que contiene manage.py:
    python verificar_syncora.py

No modifica la base de datos real: Django crea una base temporal al ejecutar tests.
"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def ejecutar(titulo: str, *argumentos: str) -> bool:
    """Ejecuta una comprobación de Django y devuelve si tuvo éxito."""
    comando = [sys.executable, str(ROOT / "manage.py"), *argumentos]
    print("\n" + "=" * 64, flush=True)
    print(titulo, flush=True)
    print("Comando:", "python manage.py " + " ".join(argumentos), flush=True)
    print("=" * 64, flush=True)
    resultado = subprocess.run(comando, cwd=ROOT, check=False)
    if resultado.returncode == 0:
        print(f"\n[OK] {titulo}", flush=True)
        return True
    print(f"\n[ERROR] {titulo} (código {resultado.returncode})", flush=True)
    return False


def main() -> int:
    if not (ROOT / "manage.py").is_file():
        print("[ERROR] Ubicá este archivo junto a manage.py, en ElPoli_Django.")
        return 2

    print("VERIFICACIÓN GENERAL DE SYNCORA / EL POLI", flush=True)
    print("Python en uso:", sys.executable, flush=True)

    verificaciones = (
        ("Configuración de Django", ("check",)),
        ("Modelos y migraciones sincronizados", ("makemigrations", "--check", "--dry-run")),
        ("Todas las pruebas automáticas", ("test",)),
    )

    for titulo, argumentos in verificaciones:
        if not ejecutar(titulo, *argumentos):
            print("\nResultado general: NO APROBADO", flush=True)
            print("Revisá el error anterior antes de hacer el commit.", flush=True)
            return 1

    print("\n" + "=" * 64, flush=True)
    print("Resultado general: TODAS LAS COMPROBACIONES APROBADAS", flush=True)
    print("=" * 64, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
