# MotorContableTSC

Motor para transformar una cartola bancaria en comprobantes contables importables a Nubox.

## Generar archivo Nubox

```bash
motor-contable-tsc "Cartola Santander.xlsx" \
  --plantilla "plantillaCargaComprobantes (1).xlsx" \
  --salida "output/Comprobantes_Nubox.xlsx"
```

## Generar solo archivo de validación

```bash
motor-contable-tsc "Cartola Santander.xlsx" \
  --solo-normalizar \
  --salida "output/Cartola_Normalizada.xlsx"
```

El flujo completo ejecuta:

1. Lectura de la cartola.
2. Normalización de movimientos y RUT.
3. Agrupación por Mes + Cuenta Contable + Cargo/Abono.
4. Construcción de comprobantes.
5. Exportación sobre la plantilla oficial Nubox.
