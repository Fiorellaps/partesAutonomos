# Proyecto: app de gestión (partes, visitas y comunicaciones)

App de Streamlit para un servicio técnico de Panasonic. Repositorio: github.com/Fiorellaps/partesAutonomos
(la raíz del repo es esta carpeta, `gestion-app/`).

## Estructura
- `app.py`: login, navegación (`ui.MODULOS`) y diseño por página.
- `ui.py`: estilos y piezas visuales comunes (ver `ui.md`).
- `datos.py`: tablas `historico`, `pendientes` y `comunicaciones` en `data/gestion/<tabla>.json`, importación
  del Excel, colores por estado, fechas de cita y WhatsApp.
- `fichas.py`: piezas compartidas entre páginas (panel de WhatsApp, tabla coloreada, CSV).
- `storage.py` + `partes/`: partes de trabajo con versiones, fotos y PDF.
- `views/`: una página por módulo (inicio, generar = Partes, historico, citas, calendario, clientes, comunicaciones).

## Entorno y ejecución
- Entorno: `.venv` de esta carpeta. Instala con `.venv/bin/python -m pip install -r requirements.txt`.
  Si añades una librería, inclúyela en `requirements.txt` e instálala en `.venv`.
- Lanzar: `.venv/bin/streamlit run app.py --server.port 8503`. Los puertos 8501 y 8502 suelen estar ocupados
  por otras apps de la usuaria: no los cierres.
- Si cambias un módulo importado (`ui.py`, `datos.py`…), reinicia el servidor: Streamlit puede seguir usando la
  versión antigua del módulo.
- Credenciales en `.streamlit/secrets.toml` (fuera de git). Nunca las escribas en el código ni en los logs.

## Datos
- `data/` y los `*.xlsx` no se suben a git: contienen datos de clientes.
- Para probar cosas que escriben datos, usa una copia: `PARTES_DATA=/tmp/<carpeta>` apunta la app a otro directorio.
- La importación del Excel sustituye Histórico y Clientes actuales; no la lances sobre `data/` real sin pedirlo.

## Verificación
- Compila: `.venv/bin/python -m py_compile app.py ui.py datos.py fichas.py views/*.py`.
- Comprobación en navegador con Playwright (`../.venv/bin/python`, que lo tiene instalado, con
  `channel="chrome"`): iniciar sesión, recorrer las páginas del menú, contar `[data-testid="stException"]`
  (debe ser 0) y medir los recuadros a 1440 px y 390 px.
- Borra los scripts y capturas temporales al terminar.

## Git
- No hagas commit ni push sin que te lo pidan. Añade los archivos por nombre.
