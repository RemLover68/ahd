#!/usr/bin/env python3
"""
server.py — Backend HTTP (FastAPI) para la app de Licitación → Propuesta.

Expone la lógica de licitacion_a_propuesta.py al frontend:

  POST /api/process            -> sube archivos, lanza el procesamiento y
                                  devuelve un job_id.
  GET  /api/status/{job_id}    -> estado del trabajo (progreso, mensaje,
                                  resultados o error).
  GET  /api/download/{job_id}/{result_id} -> descarga el .docx generado.

El procesamiento de NotebookLM es lento (sube documentos + 2 mensajes con
reintentos), así que corre en segundo plano y el frontend hace polling.

Ejecutar:
    pip install -r requirements.txt
    playwright install chromium
    notebooklm login            # autenticación con Google (una sola vez)
    uvicorn server:app --reload --port 8000
"""

import asyncio
import logging
import shutil
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import licitacion_a_propuesta as core

# --------------------------------------------------------------------------- #
# Logging: a consola y a backend.log
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backend.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("licitacion.backend")

app = FastAPI(title="Licitación → Propuesta")

# CORS abierto para desarrollo (el frontend corre en otro puerto con Vite).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta de trabajo: subidas temporales por job dentro de Output/.jobs/.
JOBS_DIR = Path(core.OUTPUT_ROOT) / ".jobs"

# Estado de los trabajos en memoria (suficiente para un solo proceso/uso local).
JOBS: dict[str, dict] = {}


def _nuevo_job():
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "phase": "processing",   # processing | completed | error
        "progress": 0,
        "message": "En cola",
        "licitacion": None,
        "results": [],
        "error": None,
        "paths": {},             # result_id -> ruta absoluta del .docx
    }
    return job_id


async def _ejecutar(job_id, documentos):
    """Tarea de fondo: corre el flujo y va actualizando el estado del job."""
    estado = JOBS[job_id]

    def on_progress(progreso, mensaje):
        estado["progress"] = progreso
        estado["message"] = mensaje
        log.info("[%s] %3d%% — %s", job_id, progreso, mensaje)

    try:
        log.info("[%s] Iniciando procesamiento de %d documento(s)",
                 job_id, len(documentos))
        resultado = await core.generar_propuesta(documentos, on_progress=on_progress)
        estado["licitacion"] = resultado["licitacion"]
        estado["paths"] = {a["id"]: a["path"] for a in resultado["archivos"]}
        estado["results"] = [
            {k: a[k] for k in ("id", "title", "description", "filename", "date")}
            for a in resultado["archivos"]
        ]
        estado["phase"] = "completed"
        estado["progress"] = 100
        estado["message"] = "Proceso finalizado"
        log.info("[%s] Completado. Licitación=%s, carpeta=%s",
                 job_id, resultado["licitacion"], resultado["carpeta"])
    except Exception as exc:  # noqa: BLE001 — queremos reportar cualquier fallo
        tb = traceback.format_exc()
        log.error("[%s] Falló el procesamiento:\n%s", job_id, tb)
        estado["phase"] = "error"
        estado["error"] = f"{type(exc).__name__}: {exc}"
        estado["trace"] = tb
        estado["message"] = "Ocurrió un error al procesar"


@app.post("/api/process")
async def process(files: list[UploadFile]):
    """Recibe los documentos subidos y lanza el procesamiento en segundo plano."""
    if not files:
        raise HTTPException(status_code=400, detail="No se subió ningún archivo")

    job_id = _nuevo_job()
    subida = JOBS_DIR / job_id
    subida.mkdir(parents=True, exist_ok=True)

    documentos = []
    for archivo in files:
        destino = subida / Path(archivo.filename).name
        with destino.open("wb") as f:
            shutil.copyfileobj(archivo.file, f)
        documentos.append(destino)

    log.info("[%s] Recibidos %d archivo(s): %s", job_id, len(documentos),
             ", ".join(d.name for d in documentos))

    # Lanzamos la tarea sin esperar a que termine.
    asyncio.create_task(_ejecutar(job_id, documentos))

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def status(job_id: str):
    estado = JOBS.get(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    # Devolvemos todo menos las rutas absolutas internas.
    return {k: v for k, v in estado.items() if k != "paths"}


@app.get("/api/download/{job_id}/{result_id}")
async def download(job_id: str, result_id: str):
    estado = JOBS.get(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    ruta = estado["paths"].get(result_id)
    if not ruta or not Path(ruta).exists():
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return FileResponse(
        ruta,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(ruta).name,
    )


@app.get("/api/health")
async def health():
    return {"ok": True}
