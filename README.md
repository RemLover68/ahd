# Licitación → Propuesta (NotebookLM)

App que automatiza NotebookLM (usando la librería **notebooklm-py** de Teng Lin)
para procesar los documentos de una licitación y generar una propuesta del
oferente en formato `.docx`, con un frontend web para manejarlo cómodamente.

## ¿Qué hace?

1. Subes los documentos de la licitación desde la web (o por CLI).
2. Crea un notebook en NotebookLM y sube los documentos.
3. Ejecuta un **pipeline por secciones con checkpoints** (en vez de pedir todo
   en un solo turno, que da respuestas poco profundas):
   - **Fase 1:** lista completa de ítems / requisitos.
   - **Fase 2:** índice de secciones (lo define NotebookLM).
   - **Fase 3–5:** por cada sección → requisitos exhaustivos, propuesta del
     oferente y matriz de cumplimiento (cada uno guardado como checkpoint).
   - **Fase 6:** resumen ejecutivo y ensamblado de los `.docx`.
4. Guarda los resultados en **`Output/<ID-de-la-licitación>/`**:
   - `Propuesta_Tecnica_<ID>.docx`
   - `Lista_Items_<ID>.docx`
   - `Matriz_Cumplimiento_<ID>.docx`
   - `checkpoints/` con todos los intermedios (auditables / regenerables).

El **nombre de la subcarpeta** es el ID de la licitación detectado en los PDFs
(formato Mercado Público, p. ej. `2378-57-L126`). Si no se encuentra ninguno,
usa el nombre del primer archivo subido.

## Estructura

```
.
├── server.py                  # Backend HTTP (FastAPI)
├── licitacion_a_propuesta.py  # Lógica central + CLI
├── requirements.txt           # Dependencias del backend
├── Output/                     # Resultados generados (ignorado por git)
└── Frontend/                   # Frontend web (React + Vite + shadcn)
```

## Requisitos previos (una sola vez)

```bash
# Backend (dentro de un entorno virtual .venv)
python -m venv .venv
# Windows:        .\.venv\Scripts\activate
# Linux/macOS:    source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
notebooklm login        # inicia sesión con Google

# Frontend
cd Frontend
pnpm install            # o npm install
```

## Uso con la web (frontend + backend)

En una terminal, **con el `.venv` activado** y desde la raíz del repo, levanta
el backend (no requiere Docker):

```bash
# Windows:        .\.venv\Scripts\activate
# Linux/macOS:    source .venv/bin/activate
uvicorn server:app --reload --port 8000
```

> Importante: activa el `.venv` antes de `uvicorn`, si no usará un Python sin
> las dependencias. El backend escribe sus logs en consola y en `backend.log`.

En otra, levanta el frontend:

```bash
cd Frontend
pnpm dev                # o npm run dev
```

Abre la URL que muestra Vite (normalmente http://localhost:5173). Vite reenvía
automáticamente las llamadas `/api` al backend (ver `Frontend/vite.config.ts`).

Flujo: subes los documentos → "Procesar documentos" → se muestra el progreso →
al terminar descargas la propuesta técnica y la lista de ítems.

## Uso solo por CLI (sin frontend)

```bash
python licitacion_a_propuesta.py bases.pdf anexo.pdf
```

Los resultados quedan en `Output/<ID-de-la-licitación>/`.

| Opción      | Descripción                          | Por defecto |
|-------------|--------------------------------------|-------------|
| `documentos`| Archivos a subir                     | Los PDFs del repo |
| `--output`  | Carpeta raíz de salida               | `Output`    |

## Nota

`notebooklm-py` es una librería **no oficial** que usa APIs internas de Google,
así que puede dejar de funcionar si Google cambia algo de su lado.
