# Licitación → Propuesta (NotebookLM)

App que automatiza NotebookLM (usando la librería **notebooklm-py** de Teng Lin)
para procesar los documentos de una licitación y generar una propuesta del
oferente en formato `.docx`, con un frontend web para manejarlo cómodamente.

## ¿Qué hace?

1. Subes los documentos de la licitación desde la web (o por CLI).
2. Crea un notebook en NotebookLM y sube los documentos.
3. Manda el primer mensaje pidiendo **la lista completa de ítems / requisitos**.
4. Manda el segundo mensaje pidiendo **redactar la propuesta del oferente**
   ("se oferta...", "se instalarán...", "se proveerá...").
5. Guarda los resultados como `.docx` con formato bonito en
   **`Output/<ID-de-la-licitación>/`**:
   - `Propuesta_Tecnica_<ID>.docx`
   - `Lista_Items_<ID>.docx`

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
# Backend
pip install -r requirements.txt
playwright install chromium
notebooklm login        # inicia sesión con Google

# Frontend
cd Frontend
pnpm install            # o npm install
```

## Uso con la web (frontend + backend)

En una terminal, levanta el backend:

```bash
uvicorn server:app --reload --port 8000
```

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
