---
inclusion: fileMatch
fileMatchPattern: "datos.py"
---

# Excel «CITAS PANASONIC.xlsx»

- Pestaña **NO TOCAR** → Histórico (visitas realizadas y cerradas). Columnas B–K: orden, fecha límite, dirección,
  correo, cliente, móvil, servicio, descripción SAT, observaciones, cita. La columna A es una casilla sin uso.
- Pestaña **PANASONIC PENDIENTES** → Clientes actuales. Columnas: B cita, D estado, E orden, F fecha límite,
  G dirección, H correo, I cliente, J móvil, K tipo de servicio, L servicio, M descripción SAT. C está vacía.
- Cada visita ocupa **un bloque de 3 filas**: la dirección continúa en las filas 2 y 3 (ciudad, país) y algunas
  celdas están combinadas o desplazadas a la fila 2 (p. ej. el nº de orden tras un resto de cabecera «Columna1»).
  Lee por bloques y toma el primer valor no vacío de cada columna.
- **Colores**: son rellenos manuales, no formato condicional. Se importa el color exacto de la celda Estado
  (`color_estado`) y de la fila (`color_fila`). Al cambiar un estado desde la app, `datos.color_estado()`
  aplica el código del Excel (amarillo confirmado, rojo avería o cancelación, naranja/salmón problemas de correo).
- Los estados son texto libre con erratas («COMFIRMADO», «CORREO ERRORNEO»): consérvalos tal cual, no los normalices.
- Las citas mezclan formatos («21/10/2026 9,00», «04/11/2026 a las 11,30», fechas de Excel): usa `datos.parse_cita`.
