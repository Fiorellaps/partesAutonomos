# Normas de interfaz (Streamlit)

Toda la interfaz está en español y usa las piezas de `ui.py`. No dupliques estilos en las páginas.

## Recuadros del mismo tamaño (obligatorio)
Todo grupo de recuadros que se muestre junto (tarjetas, indicadores, gráficos de una misma fila) debe tener
el mismo ancho y alto, en ordenador y en móvil.

- **Tarjetas** (módulos, modelos, accesos…): dentro de `with ui.card_grid("nombre"):`, cada una como
  `st.container(border=True, key="card_…")` o `key="cardlink_…"` si es clicable. La rejilla iguala el alto
  de todas las filas al de la tarjeta más alta y deja el botón o enlace abajo.
  No uses `st.columns` para repartir tarjetas: cada columna crece por su cuenta y quedan de distinto alto.
- **Indicadores**: `ui.kpis([ui.kpi(...), ...])`. Ya reserva dos líneas para la etiqueta y la línea del
  subtítulo aunque esté vacía, para que las cifras queden alineadas.
- **Gráficos en la misma fila**: mismo `alto` en `ui.plotly_style(fig, alto)` y el mismo contenido en las
  tarjetas que los envuelven (título y, si una lleva `st.caption`, todas).

Tras cualquier cambio de interfaz, compruébalo midiendo los recuadros con Playwright (ver `proyecto.md`)
a 1440 px y 390 px de ancho: todos los del grupo deben dar el mismo ancho × alto.

## Gráficos
- Usa **Plotly** (`plotly.graph_objects`), no Altair ni `st.bar_chart`.
- Siempre `ui.plotly_style(fig, alto)` y se muestran con `ui.plotly_chart(fig)` (sin barra de herramientas ni zoom).
- Número encima de cada barra (`text=…, textposition="outside", cliponaxis=False`) y `hovertemplate` en español.
- Si hay muchas categorías con nombres largos, el gráfico ocupa todo el ancho; recorta las etiquetas del eje y
  muestra el nombre completo en el tooltip.
- Colores: azul de la app (`ui.AZUL`, `ui.AZUL_CLARO`). Los estados de clientes usan su color del Excel
  (`color_estado`), nunca una paleta inventada.

## Otras piezas
- Cabecera de página: `ui.hero(título, subtítulo, crumb=…)`. Títulos de bloque: `ui.section_label(...)`.
- Tarjetas de cita: `ui.cita_head(hora, día, nombre, dirección, etiquetas)` dentro de
  `st.container(border=True, key="card_cita_…")`; la dirección y las etiquetas reservan un alto fijo.
- Estados de clientes: `ui.chip(estado, color)`; tablas con colores de fila: `fichas.tabla_coloreada`.
- Avisos tras guardar: `ui.flash("…")` y después `st.rerun()` (un `st.toast` justo antes de `st.rerun()` se pierde).
- La página **Partes** usa diseño estrecho (pensada para el móvil); el resto, ancho completo. Lo decide `app.py`.
- El menú lateral es el nativo de Streamlit, a la izquierda.
