from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Iterable, Mapping

from .models import (
    ComprobanteContable,
    DetalleAuxiliar,
    DetalleBancario,
    LineaContable,
)
from .normalizador import MovimientoNormalizado


CUENTA_BANCO_SANTANDER = "1101-10"


def _fin_de_mes(periodo: str) -> date:
    if len(periodo) != 6 or not periodo.isdigit():
        raise ValueError(f"Periodo inválido: {periodo!r}; se esperaba AAAAMM")
    anio = int(periodo[:4])
    mes = int(periodo[4:])
    return date(anio, mes, monthrange(anio, mes)[1])


def _glosa_comprobante(
    movimientos: list[MovimientoNormalizado],
    tipo: str,
    cuenta: str,
    catalogo_glosas: Mapping[str, str] | None = None,
) -> str:
    catalogo = catalogo_glosas or {}

    # Prioriza coincidencias parametrizadas contra observación y glosa bancaria.
    for movimiento in movimientos:
        texto = " ".join(
            [
                movimiento.movimiento.observacion,
                movimiento.movimiento.descripcion_bancaria,
            ]
        ).upper()
        for patron, glosa in catalogo.items():
            if str(patron).upper() in texto and str(glosa).strip():
                return str(glosa).strip()

    glosas = {
        movimiento.glosa_contable.strip()
        for movimiento in movimientos
        if movimiento.glosa_contable.strip()
    }
    if len(glosas) == 1:
        return glosas.pop()

    concepto = "INGRESOS" if tipo == "I" else "EGRESOS"
    return f"{concepto} CUENTA {cuenta}"


def _agrupar_auxiliares(
    movimientos: list[MovimientoNormalizado],
) -> list[DetalleAuxiliar]:
    acumulados: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    referencias: dict[tuple[str, str], str] = {}

    for normalizado in movimientos:
        clave = (normalizado.rut, normalizado.razon_social)
        acumulados[clave] += normalizado.movimiento.monto
        referencias.setdefault(
            clave,
            normalizado.movimiento.descripcion_bancaria,
        )

    return [
        DetalleAuxiliar(
            rut=rut,
            razon_social=razon_social,
            monto=monto,
            glosa_referencia=referencias[(rut, razon_social)],
        )
        for (rut, razon_social), monto in sorted(acumulados.items())
    ]


def construir_comprobante(
    movimientos: Iterable[MovimientoNormalizado],
    *,
    cuenta_banco: str = CUENTA_BANCO_SANTANDER,
    requiere_auxiliar: bool = False,
    catalogo_glosas: Mapping[str, str] | None = None,
) -> ComprobanteContable:
    """Construye un comprobante de dos líneas contables desde un único grupo.

    Reglas:
    - Un comprobante contiene movimientos de un solo periodo, cuenta y Cargo/Abono.
    - A (abono bancario) genera comprobante I: Banco al Debe, contrapartida al Haber.
    - C (cargo bancario) genera comprobante E: contrapartida al Debe, Banco al Haber.
    - La cuenta bancaria se informa una sola vez y conserva N detalles bancarios.
    - Si la contrapartida requiere auxiliar, los movimientos se agrupan por RUT.
    """
    items = list(movimientos)
    if not items:
        raise ValueError("No se puede construir un comprobante sin movimientos")

    claves = {item.clave_grupo for item in items}
    if len(claves) != 1:
        raise ValueError(
            "Los movimientos deben pertenecer al mismo Mes + Cuenta + Cargo/Abono"
        )

    periodo, cuenta, cargo_abono = next(iter(claves))
    if cargo_abono not in {"A", "C"}:
        raise ValueError(f"Cargo/Abono inválido: {cargo_abono!r}")

    tipo = "I" if cargo_abono == "A" else "E"
    total = sum(
        (item.movimiento.monto for item in items),
        Decimal("0"),
    )
    glosa = _glosa_comprobante(items, tipo, cuenta, catalogo_glosas)

    if cargo_abono == "A":
        # El abono en la cuenta corriente aumenta Banco: Banco al Debe.
        debe_contrapartida, haber_contrapartida = Decimal("0"), total
        debe_banco, haber_banco = total, Decimal("0")
    else:
        # El cargo en la cuenta corriente disminuye Banco: Banco al Haber.
        debe_contrapartida, haber_contrapartida = total, Decimal("0")
        debe_banco, haber_banco = Decimal("0"), total

    linea_contrapartida = LineaContable(
        cuenta=cuenta,
        glosa=glosa,
        debe=debe_contrapartida,
        haber=haber_contrapartida,
        auxiliares=_agrupar_auxiliares(items) if requiere_auxiliar else [],
    )

    linea_banco = LineaContable(
        cuenta=cuenta_banco,
        glosa=glosa,
        debe=debe_banco,
        haber=haber_banco,
        movimientos_bancarios=[
            DetalleBancario(
                descripcion=item.movimiento.descripcion_bancaria,
                numero_documento=item.movimiento.numero_documento or "0",
                monto=item.movimiento.monto,
                fecha=item.movimiento.fecha,
            )
            for item in items
        ],
    )

    comprobante = ComprobanteContable(
        numero=0,
        tipo=tipo,
        fecha=_fin_de_mes(periodo),
        glosa=glosa,
        clave_grupo=f"{periodo}-{cuenta}-{cargo_abono}",
        lineas=[linea_contrapartida, linea_banco],
    )

    validar_comprobante(comprobante, requiere_auxiliar=requiere_auxiliar)
    return comprobante


def construir_comprobantes(
    movimientos: Iterable[MovimientoNormalizado],
    *,
    cuentas_con_auxiliar: set[str] | None = None,
    cuenta_banco: str = CUENTA_BANCO_SANTANDER,
    catalogo_glosas: Mapping[str, str] | None = None,
) -> list[ComprobanteContable]:
    """Agrupa normalizados y construye un comprobante por clave contable."""
    grupos: dict[tuple[str, str, str], list[MovimientoNormalizado]] = defaultdict(list)
    for movimiento in movimientos:
        grupos[movimiento.clave_grupo].append(movimiento)

    auxiliares = cuentas_con_auxiliar or set()
    comprobantes = [
        construir_comprobante(
            items,
            cuenta_banco=cuenta_banco,
            requiere_auxiliar=cuenta in auxiliares,
            catalogo_glosas=catalogo_glosas,
        )
        for (_, cuenta, _), items in grupos.items()
    ]
    return sorted(comprobantes, key=lambda item: item.clave_grupo)


def validar_comprobante(
    comprobante: ComprobanteContable,
    *,
    requiere_auxiliar: bool = False,
) -> None:
    if len(comprobante.lineas) != 2:
        raise ValueError("El comprobante bancario debe tener exactamente dos líneas contables")
    if not comprobante.cuadrado:
        raise ValueError(
            f"Comprobante descuadrado: Debe={comprobante.total_debe} "
            f"Haber={comprobante.total_haber}"
        )

    linea_contrapartida, linea_banco = comprobante.lineas
    monto_contrapartida = linea_contrapartida.debe or linea_contrapartida.haber
    monto_banco = linea_banco.debe or linea_banco.haber

    if linea_banco.total_movimientos_bancarios != monto_banco:
        raise ValueError("El total de detalles bancarios no coincide con la línea Banco")

    if requiere_auxiliar and linea_contrapartida.total_auxiliares != monto_contrapartida:
        raise ValueError("El total de auxiliares no coincide con la línea contable")
