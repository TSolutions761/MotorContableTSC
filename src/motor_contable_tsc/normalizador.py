from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from .models import MovimientoBancario


_RUT_CON_PUNTOS = re.compile(r"(?<!\d)(\d{1,2}(?:\.\d{3}){2}-[0-9Kk])(?!\d)")
_RUT_SIN_PUNTOS = re.compile(r"(?<!\d)(\d{7,8}-[0-9Kk])(?!\d)")
_RUT_SOLO_DIGITOS = re.compile(r"(?<!\d)(\d{8,10})(?!\d)")


@dataclass(frozen=True, slots=True)
class MovimientoNormalizado:
    movimiento: MovimientoBancario
    rut: str
    razon_social: str
    glosa_contable: str
    estado: str

    @property
    def clave_grupo(self) -> tuple[str, str, str]:
        return self.movimiento.clave_grupo


def calcular_dv(cuerpo: str) -> str:
    """Calcula el dígito verificador de un RUT chileno sin puntos ni guion."""
    if not cuerpo.isdigit():
        raise ValueError("El cuerpo del RUT debe contener solo dígitos")

    suma = 0
    factor = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1

    resultado = 11 - (suma % 11)
    if resultado == 11:
        return "0"
    if resultado == 10:
        return "K"
    return str(resultado)


def normalizar_rut(valor: str) -> str:
    """Convierte distintas representaciones al formato XXXXXXXX-X."""
    limpio = re.sub(r"[^0-9Kk]", "", str(valor or "")).upper()
    if len(limpio) < 2:
        return "1-9"

    cuerpo, dv = limpio[:-1], limpio[-1]
    cuerpo = cuerpo.lstrip("0") or "0"
    if dv not in "0123456789K":
        return "1-9"
    if calcular_dv(cuerpo) != dv:
        return "1-9"
    return f"{cuerpo}-{dv}"


def extraer_rut(texto: str) -> str:
    """Extrae y valida el primer RUT reconocible desde una glosa bancaria."""
    origen = str(texto or "")

    for patron in (_RUT_CON_PUNTOS, _RUT_SIN_PUNTOS):
        for coincidencia in patron.findall(origen):
            rut = normalizar_rut(coincidencia)
            if rut != "1-9":
                return rut

    for coincidencia in _RUT_SOLO_DIGITOS.findall(origen):
        # En cartolas Santander suele aparecer RUT con cero inicial y DV al final.
        rut = normalizar_rut(coincidencia)
        if rut != "1-9":
            return rut

    return "1-9"


def construir_glosa_contable(movimiento: MovimientoBancario) -> str:
    """Prioriza la observación contable y usa la glosa bancaria como respaldo."""
    if movimiento.observacion.strip():
        return movimiento.observacion.strip()
    if movimiento.descripcion_bancaria.strip():
        return movimiento.descripcion_bancaria.strip()
    return "MOVIMIENTO BANCARIO"


def normalizar_movimiento(
    movimiento: MovimientoBancario,
    maestro_rut: Mapping[str, str] | None = None,
) -> MovimientoNormalizado:
    """Completa RUT, razón social, glosa y estado de un movimiento bancario."""
    maestro = maestro_rut or {}
    rut = extraer_rut(movimiento.descripcion_bancaria)
    razon_social = str(maestro.get(rut, "")).strip()

    pendientes: list[str] = []
    if rut == "1-9":
        pendientes.append("RUT_NO_IDENTIFICADO")
    elif not razon_social:
        pendientes.append("RAZON_SOCIAL_PENDIENTE")

    return MovimientoNormalizado(
        movimiento=movimiento,
        rut=rut,
        razon_social=razon_social,
        glosa_contable=construir_glosa_contable(movimiento),
        estado="OK" if not pendientes else "|".join(pendientes),
    )
