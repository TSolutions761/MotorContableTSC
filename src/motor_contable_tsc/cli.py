from __future__ import annotations

import argparse
from pathlib import Path

from .cartola import leer_cartola
from .normalizador import normalizar_movimiento
from .pipeline import generar_archivo_nubox
from .reporte import exportar_normalizacion_excel


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="motor-contable-tsc",
        description="Genera un archivo Nubox desde una cartola bancaria.",
    )
    parser.add_argument("cartola", type=Path, help="Ruta del archivo Excel de cartola")
    parser.add_argument(
        "--plantilla",
        type=Path,
        help="Ruta de la plantilla oficial de comprobantes Nubox",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("output/Comprobantes_Nubox.xlsx"),
        help="Ruta del Excel de salida",
    )
    parser.add_argument(
        "--solo-normalizar",
        action="store_true",
        help="Genera únicamente el Excel de validación de movimientos normalizados",
    )
    return parser


def main() -> int:
    argumentos = construir_parser().parse_args()

    if argumentos.solo_normalizar:
        movimientos = leer_cartola(argumentos.cartola)
        normalizados = [normalizar_movimiento(movimiento) for movimiento in movimientos]
        destino = exportar_normalizacion_excel(normalizados, argumentos.salida)
        print(f"Archivo de validación generado: {destino}")
        print(f"Movimientos procesados: {len(normalizados)}")
        return 0

    if argumentos.plantilla is None:
        raise SystemExit(
            "Debe indicar --plantilla para generar el archivo Nubox, "
            "o usar --solo-normalizar."
        )

    destino = generar_archivo_nubox(
        cartola=argumentos.cartola,
        plantilla=argumentos.plantilla,
        salida=argumentos.salida,
    )
    print(f"Archivo Nubox generado: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
