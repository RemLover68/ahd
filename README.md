# Licitacion -> Propuesta (RAG local)

App local-first para procesar documentos de una licitacion, extraer una lista de
items y generar una propuesta tecnica con citas trazables.

El backend ahora usa:

- un servidor LLM local OpenAI-compatible
- Docling para OCR/parseo cuando esta disponible
- embeddings locales y busqueda hibrida para RAG
- checkpoints por fase
- exportacion a `.docx`

`Open WebUI` puede usarse como interfaz opcional para explorar el corpus local,
pero el flujo productivo de licitaciones vive en este backend.

## Que hace

1. Carga los documentos de la licitacion desde la web o por CLI.
2. Convierte PDFs y otros formatos a texto utilizable para RAG.
3. Construye un corpus local con embeddings.
4. Extrae una lista consolidada de items:
   - Hardware
   - Software
   - Otros
5. Propone el indice de secciones de la propuesta tecnica.
6. Genera, por seccion, requisitos y propuesta con citas `[n]`.
7. Produce un resumen ejecutivo.
8. Guarda resultados en `Output/<ID-de-la-licitacion>/` y exporta `.docx`.

## Arquitectura

- `server.py` expone la API HTTP para el frontend.
- `licitacion_a_propuesta.py` contiene el pipeline local RAG y la exportacion.
- `Frontend/` muestra progreso, resultado y re-procesado selectivo.

## Requisitos

- Ubuntu 22.04+ o similar
- Python 3.11+
- Un servidor LLM local OpenAI-compatible
- Un modelo cuantizado de 27B a 32B como objetivo principal

### Modelos recomendados

Para esta maquina, el objetivo razonable es la banda 27B-32B:

- `Gemma 4 31B Dense` como candidato principal si tu runtime lo soporta.
- `Qwen3-32B-Instruct` como alternativa generalista muy fuerte.
- `DeepSeek-R1-Distill-Qwen-32B` como opcion de razonamiento.

Si el modelo es demasiado pesado, baja a una variante cuantizada mas agresiva
o cambia a un runtime local con mejor offload de CPU/RAM.

## Variables de entorno

El backend se configura con estas variables:

- `LOCAL_LLM_BASE_URL` -> endpoint OpenAI-compatible local
- `LOCAL_LLM_API_KEY` -> clave dummy o la que pida tu servidor
- `LOCAL_LLM_MODEL` -> nombre exacto del modelo local
- `LOCAL_LLM_TIMEOUT` -> timeout de peticiones al modelo
- `LOCAL_LLM_MAX_CONCURRENCY` -> concurrencia de llamadas al modelo
- `RAG_EMBED_MODEL` -> modelo de embeddings local
- `RAG_TOP_K` -> numero de fragmentos recuperados por consulta
- `RAG_CHUNK_SIZE` -> tamano de chunk
- `RAG_CHUNK_OVERLAP` -> solape entre chunks
- `RAG_EMBED_BATCH` -> batch de embeddings
- `RAG_HYBRID_WEIGHT` -> peso de embeddings frente a coincidencia lexica
- `JOB_EXECUTION_LIMIT` -> cantidad de trabajos simultaneos

Valores sugeridos para empezar:

```bash
export LOCAL_LLM_BASE_URL="http://127.0.0.1:11434/v1"
export LOCAL_LLM_API_KEY="local"
export LOCAL_LLM_MODEL="qwen3:14b"
export RAG_EMBED_MODEL="BAAI/bge-m3"
export RAG_HYBRID_WEIGHT=0.75
export JOB_EXECUTION_LIMIT=2
export LOCAL_LLM_MAX_CONCURRENCY=2
```

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Instala y levanta tu servidor LLM local preferido antes de procesar.

`docling` habilita parseo estructurado y OCR local. Si falla o no esta
instalado, el pipeline cae a `pypdf`/`markitdown`, con menor calidad en PDFs
escaneados.

## Uso con la web

Backend:

```bash
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd Frontend
pnpm install
pnpm dev -- --host 0.0.0.0
```

Abre la URL que imprime Vite.

### Windows: un solo script

`start.bat` en la raiz del repo levanta ambos servicios de una vez: instala
dependencias del Frontend si falta `node_modules`, abre el frontend (`pnpm dev`)
en una ventana nueva y corre el backend (`uvicorn --reload --port 8000`) en la
ventana actual.

```bat
start.bat
```

## Open WebUI

Si quieres una interfaz adicional para hablar con el mismo stack local, puedes
levantar `Open WebUI` y apuntarlo al mismo backend LLM local.

La integracion tipica es:

- tu runtime local expone un endpoint OpenAI-compatible
- `Open WebUI` se conecta a ese endpoint
- este repo usa el mismo endpoint para el pipeline de licitaciones

## Uso solo por CLI

```bash
python licitacion_a_propuesta.py bases.pdf anexo.pdf
```

Los resultados quedan en `Output/<ID-de-la-licitacion>/`.

## API

| Endpoint | Descripcion |
|---|---|
| `POST /api/process` | Sube archivos y lanza el pipeline |
| `GET /api/status/{job_id}` | Progreso y fase |
| `GET /api/result/{job_id}` | JSON estructurado con secciones y citas |
| `POST /api/reprocess` | Re-procesa secciones especificas |
| `GET /api/reprocess-status/{id}` | Estado del re-proceso |
| `GET /api/export/{job_id}` | Genera y descarga el `.docx` actual |
| `GET /api/download/{job_id}/{id}` | Descarga un `.docx` generado |
| `GET /api/health` | Health check |

## Salida

Cada trabajo deja:

- `result.json` como fuente de verdad
- `result_v<n>.json` para historial
- `checkpoints/` con los textos intermedios
- `Propuesta_Tecnica_<ID>.docx`
- `Lista_Items_<ID>.docx`

## Notas

- El visor conserva las citas `[n]` y el re-procesado selectivo.
- Si el modelo omite marcadores de cita, el backend agrega citas visibles a las
  lineas sustantivas usando la evidencia recuperada.
- El pipeline no depende de servicios cloud.
- La calidad final depende de la combinacion entre el modelo local y el RAG.
