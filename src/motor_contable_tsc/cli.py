from __future__ import annotations

import argparse
from pathlib import Path

from .cartola import leer_cartola
from .normalizador import normalizar_movimiento
from .reporte import exportar_normalizacion_excel


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="motor-contable-tsc",
        description="Normaliza una cartola bancaria y genera un Excel de validación.",
    )
    parser.add_argument("cartola", type=Path, help="Ruta del archivo Excel de cartola")
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("output/Cartola_Normalizada.xlsx"),
        help="Ruta del Excel de salida",
    )
    return parser


def main() -> int:
    argumentos = construir_parser().parse_args()
    movimientos = leer_cartola(argumentos.cartola)
    normalizados = [normalizar_movimiento(movimiento) for movimiento in movimientos]
    destino = exportar_normalizacion_excel(normalizados, argumentos.salida)
    print(f"Archivo generado: {destino}")
    print(f"Movimientos procesados: {len(normalizados)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
