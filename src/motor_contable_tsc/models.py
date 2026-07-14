from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MovimientoBancario:
    fecha: date
    cargo_abono: str
    cuenta_contable: str
    monto: Decimal
    descripcion_bancaria: str = ""
    observacion: str = ""
    numero_documento: str = "0"

    @property
    def tipo_nubox(self) -> str:
        return "I" if self.cargo_abono == "A" else "E"

    @property
    def periodo(self) -> str:
        return self.fecha.strftime("%Y%m")

    @property
    def clave_grupo(self) -> tuple[str, str, str]:
        return (self.periodo, self.cuenta_contable, self.cargo_abono)


@dataclass(slots=True)
class GrupoContable:
    periodo: str
    cuenta_contable: str
    cargo_abono: str
    movimientos: list[MovimientoBancario] = field(default_factory=list)

    @property
    def tipo_nubox(self) -> str:
        return "I" if self.cargo_abono == "A" else "E"

    @property
    def total(self) -> Decimal:
        return sum((m.monto for m in self.movimientos), Decimal("0"))

    @property
    def clave(self) -> str:
        return f"{self.periodo}-{self.cuenta_contable}-{self.cargo_abono}"
