from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .cartola import leer_cartola
from .comprobantes import construir_comprobantes
from .exportador_nubox import exportar_comprobantes_nubox
from .normalizador import normalizar_movimiento


def generar_archivo_nubox(
    cartola: str | Path,
    plantilla: str | Path,
    salida: str | Path,
    *,
    maestro_rut: Mapping[str, str] | None = None,
    cuentas_con_auxiliar: set[str] | None = None,
    catalogo_glosas: Mapping[str, str] | None = None,
) -> Path:
    """Ejecuta el flujo completo Cartola -> Comprobantes -> Excel Nubox."""
    movimientos = leer_cartola(cartola)
    normalizados = [
        normalizar_movimiento(movimiento, maestro_rut=maestro_rut)
        for movimiento in movimientos
    ]
    comprobantes = construir_comprobantes(
        normalizados,
        cuentas_con_auxiliar=cuentas_con_auxiliar,
        catalogo_glosas=catalogo_glosas,
    )
    return exportar_comprobantes_nubox(
        comprobantes,
        plantilla=plantilla,
        salida=salida,
    )
