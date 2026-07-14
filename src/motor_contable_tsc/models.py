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


@dataclass(frozen=True, slots=True)
class DetalleAuxiliar:
    rut: str
    razon_social: str
    monto: Decimal
    glosa_referencia: str = ""


@dataclass(frozen=True, slots=True)
class DetalleBancario:
    descripcion: str
    numero_documento: str
    monto: Decimal
    fecha: date


@dataclass(slots=True)
class LineaContable:
    cuenta: str
    glosa: str
    debe: Decimal = Decimal("0")
    haber: Decimal = Decimal("0")
    auxiliares: list[DetalleAuxiliar] = field(default_factory=list)
    movimientos_bancarios: list[DetalleBancario] = field(default_factory=list)

    @property
    def total_auxiliares(self) -> Decimal:
        return sum((item.monto for item in self.auxiliares), Decimal("0"))

    @property
    def total_movimientos_bancarios(self) -> Decimal:
        return sum((item.monto for item in self.movimientos_bancarios), Decimal("0"))


@dataclass(slots=True)
class ComprobanteContable:
    numero: int
    tipo: str
    fecha: date
    glosa: str
    clave_grupo: str
    lineas: list[LineaContable] = field(default_factory=list)

    @property
    def total_debe(self) -> Decimal:
        return sum((linea.debe for linea in self.lineas), Decimal("0"))

    @property
    def total_haber(self) -> Decimal:
        return sum((linea.haber for linea in self.lineas), Decimal("0"))

    @property
    def cuadrado(self) -> bool:
        return self.total_debe == self.total_haber
