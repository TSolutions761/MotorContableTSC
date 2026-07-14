from datetime import date
from decimal import Decimal

from motor_contable_tsc.models import MovimientoBancario
from motor_contable_tsc.normalizador import (
    calcular_dv,
    extraer_rut,
    normalizar_movimiento,
    normalizar_rut,
)


def test_calcular_dv_conocido():
    assert calcular_dv("78722090") == "8"


def test_normalizar_rut_con_puntos():
    assert normalizar_rut("78.722.090-8") == "78722090-8"


def test_extraer_rut_con_cero_inicial_en_glosa():
    assert extraer_rut("0183929747 Transf Proveedor") == "18392974-7"


def test_rut_invalido_devuelve_generico():
    assert normalizar_rut("11.111.111-2") == "1-9"


def test_normalizar_movimiento_completa_razon_social_y_glosa():
    movimiento = MovimientoBancario(
        fecha=date(2026, 6, 5),
        cargo_abono="C",
        cuenta_contable="2101-01",
        monto=Decimal("150000"),
        descripcion_bancaria="0183929747 Transferencia",
        observacion="Pago proveedor",
    )

    resultado = normalizar_movimiento(
        movimiento,
        maestro_rut={"18392974-7": "PROVEEDOR DEMO SPA"},
    )

    assert resultado.rut == "18392974-7"
    assert resultado.razon_social == "PROVEEDOR DEMO SPA"
    assert resultado.glosa_contable == "Pago proveedor"
    assert resultado.estado == "OK"
