from datetime import date
from decimal import Decimal

from motor_contable_tsc import MovimientoBancario, agrupar_movimientos


def test_agrupa_por_mes_cuenta_y_cargo_abono():
    movimientos = [
        MovimientoBancario(date(2026, 1, 3), "C", "2101-01", Decimal("100")),
        MovimientoBancario(date(2026, 1, 8), "C", "2101-01", Decimal("50")),
        MovimientoBancario(date(2026, 1, 9), "A", "2101-01", Decimal("25")),
        MovimientoBancario(date(2026, 2, 1), "C", "2101-01", Decimal("10")),
    ]

    grupos = agrupar_movimientos(movimientos)

    assert len(grupos) == 3
    assert grupos[0].clave == "202601-2101-01-A"
    assert grupos[0].total == Decimal("25")
    assert grupos[1].clave == "202601-2101-01-C"
    assert grupos[1].total == Decimal("150")
    assert grupos[2].clave == "202602-2101-01-C"
    assert grupos[2].total == Decimal("10")


def test_tipo_nubox_no_mezcla_ingresos_y_egresos():
    ingreso = MovimientoBancario(date(2026, 1, 3), "A", "1104-03", Decimal("100"))
    egreso = MovimientoBancario(date(2026, 1, 3), "C", "2101-01", Decimal("100"))

    assert ingreso.tipo_nubox == "I"
    assert egreso.tipo_nubox == "E"
