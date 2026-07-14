from datetime import date
from decimal import Decimal

from motor_contable_tsc.comprobantes import construir_comprobante
from motor_contable_tsc.models import MovimientoBancario
from motor_contable_tsc.normalizador import MovimientoNormalizado


def _normalizado(
    *,
    fecha: date,
    cargo_abono: str,
    cuenta: str,
    monto: str,
    rut: str,
    razon_social: str,
    descripcion: str,
) -> MovimientoNormalizado:
    movimiento = MovimientoBancario(
        fecha=fecha,
        cargo_abono=cargo_abono,
        cuenta_contable=cuenta,
        monto=Decimal(monto),
        descripcion_bancaria=descripcion,
        observacion="PAGO PROVEEDORES" if cargo_abono == "C" else "INGRESO CLIENTES",
        numero_documento="0",
    )
    return MovimientoNormalizado(
        movimiento=movimiento,
        rut=rut,
        razon_social=razon_social,
        glosa_contable=movimiento.observacion,
        estado="OK",
    )


def test_egreso_banco_al_haber_y_contrapartida_al_debe():
    items = [
        _normalizado(
            fecha=date(2026, 6, 5),
            cargo_abono="C",
            cuenta="2101-01",
            monto="100000",
            rut="76123456-7",
            razon_social="PROVEEDOR UNO SPA",
            descripcion="TRANSFERENCIA PROVEEDOR UNO",
        ),
        _normalizado(
            fecha=date(2026, 6, 10),
            cargo_abono="C",
            cuenta="2101-01",
            monto="50000",
            rut="76123456-7",
            razon_social="PROVEEDOR UNO SPA",
            descripcion="TRANSFERENCIA PROVEEDOR UNO",
        ),
    ]

    comprobante = construir_comprobante(items, requiere_auxiliar=True)

    assert comprobante.numero == 0
    assert comprobante.tipo == "E"
    assert comprobante.fecha == date(2026, 6, 30)
    assert comprobante.total_debe == Decimal("150000")
    assert comprobante.total_haber == Decimal("150000")
    assert comprobante.cuadrado

    contraparte, banco = comprobante.lineas
    assert contraparte.cuenta == "2101-01"
    assert contraparte.debe == Decimal("150000")
    assert contraparte.haber == Decimal("0")
    assert len(contraparte.auxiliares) == 1
    assert contraparte.auxiliares[0].monto == Decimal("150000")

    assert banco.cuenta == "1101-10"
    assert banco.debe == Decimal("0")
    assert banco.haber == Decimal("150000")
    assert len(banco.movimientos_bancarios) == 2
    assert banco.total_movimientos_bancarios == Decimal("150000")


def test_ingreso_banco_al_debe_y_contrapartida_al_haber():
    items = [
        _normalizado(
            fecha=date(2026, 7, 3),
            cargo_abono="A",
            cuenta="1104-03",
            monto="250000",
            rut="78722090-8",
            razon_social="CLIENTE DEMO SPA",
            descripcion="ABONO CLIENTE DEMO",
        )
    ]

    comprobante = construir_comprobante(items, requiere_auxiliar=True)

    assert comprobante.tipo == "I"
    assert comprobante.fecha == date(2026, 7, 31)

    contraparte, banco = comprobante.lineas
    assert contraparte.debe == Decimal("0")
    assert contraparte.haber == Decimal("250000")
    assert banco.debe == Decimal("250000")
    assert banco.haber == Decimal("0")
    assert comprobante.cuadrado


def test_rechaza_movimientos_de_cargos_y_abonos_mezclados():
    items = [
        _normalizado(
            fecha=date(2026, 6, 1),
            cargo_abono="C",
            cuenta="2101-01",
            monto="1000",
            rut="1-9",
            razon_social="",
            descripcion="CARGO",
        ),
        _normalizado(
            fecha=date(2026, 6, 2),
            cargo_abono="A",
            cuenta="2101-01",
            monto="1000",
            rut="1-9",
            razon_social="",
            descripcion="ABONO",
        ),
    ]

    try:
        construir_comprobante(items)
    except ValueError as exc:
        assert "mismo Mes + Cuenta + Cargo/Abono" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError por mezclar cargos y abonos")
