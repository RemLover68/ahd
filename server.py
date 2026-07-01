#!/usr/bin/env python3
"""
server.py — Backend HTTP (FastAPI) para la app de Licitación → Propuesta.

  POST /api/process                  -> sube archivos, lanza procesamiento, devuelve job_id
  GET  /api/status/{job_id}          -> fase, progreso y mensaje del trabajo
  GET  /api/result/{job_id}          -> JSON estructurado con secciones y citas
  POST /api/reprocess                -> re-procesa secciones específicas, devuelve reprocess_id
  GET  /api/reprocess-status/{rid}   -> estado del re-proceso
  POST /api/export/{job_id}          -> genera .docx desde result.json actual y lo descarga
  GET  /api/download/{job_id}/{rid}  -> descarga .docx generado originalmente
  GET  /api/health                   -> ping

Ejecutar:
    pip install -r requirements.txt
    uvicorn server:app --reload --port 8000
"""

import asyncio
import os
import json
import logging
import shutil
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import licitacion_a_propuesta as core

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = Path(core.OUTPUT_ROOT) / ".jobs"
JOB_EXECUTION_LIMIT = asyncio.Semaphore(max(1, int(os.environ.get("JOB_EXECUTION_LIMIT", "2"))))
JOBS: dict[str, dict] = {}


def _nuevo_job(documentos: list | None = None) -> str:
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "phase": "queued",
        "progress": 0,
        "message": "Esperando cupo de ejecucion",
        "licitacion": None,
        "results": [],
        "error": None,
        "paths": {},
        "result_path": None,
        "carpeta": None,
        "documentos": [str(d) for d in (documentos or [])],
    }
    return job_id


async def _ejecutar(job_id: str, documentos: list):
    estado = JOBS[job_id]

    def on_progress(progreso, mensaje):
        estado["progress"] = progreso
        estado["message"] = mensaje
        log.info("[%s] %3d%% — %s", job_id, progreso, mensaje)

    try:
        log.info("[%s] Iniciando procesamiento de %d documento(s)",
                 job_id, len(documentos))
        estado["phase"] = "queued"
        estado["message"] = "Esperando cupo de ejecucion"
        async with JOB_EXECUTION_LIMIT:
            estado["phase"] = "processing"
            estado["message"] = "Preparando corpus local"
            resultado = await core.generar_propuesta(
                documentos,
                on_progress=on_progress,
            )
        estado["licitacion"] = resultado["licitacion"]
        estado["carpeta"] = resultado.get("carpeta")
        estado["result_path"] = resultado.get("result_path")
        estado["paths"] = {a["id"]: a["path"] for a in resultado.get("archivos", [])}
        estado["results"] = [
            {k: a[k] for k in ("id", "title", "description", "filename", "date")}
            for a in resultado.get("archivos", [])
        ]
        estado["phase"] = "completed"
        estado["progress"] = 100
        estado["message"] = "Proceso finalizado"
        log.info("[%s] Completado. Licitación=%s, carpeta=%s",
                 job_id, resultado["licitacion"], resultado["carpeta"])
    except Exception as exc:
        tb = traceback.format_exc()
        log.error("[%s] Falló el procesamiento:\n%s", job_id, tb)
        estado["phase"] = "error"
        estado["error"] = f"{type(exc).__name__}: {exc}"
        estado["trace"] = tb
        estado["message"] = "Ocurrio un error al procesar"


@app.post("/api/process")
async def process(files: list[UploadFile]):
    """Recibe los documentos subidos y lanza el procesamiento en segundo plano."""
    if not files:
        raise HTTPException(status_code=400, detail="No se subio ningun archivo")

    subida_dir = JOBS_DIR / uuid.uuid4().hex[:12]
    subida_dir.mkdir(parents=True, exist_ok=True)

    documentos = []
    for archivo in files:
        destino = subida_dir / Path(archivo.filename).name
        with destino.open("wb") as f:
            shutil.copyfileobj(archivo.file, f)
        documentos.append(destino)

    job_id = _nuevo_job(documentos)
    log.info("[%s] Recibidos %d archivo(s): %s", job_id, len(documentos),
             ", ".join(d.name for d in documentos))

    asyncio.create_task(_ejecutar(job_id, documentos))
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def status(job_id: str):
    estado = JOBS.get(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    return {k: v for k, v in estado.items() if k not in ("paths", "documentos")}


@app.get("/api/result/{job_id}")
async def result(job_id: str):
    """Devuelve el JSON estructurado con secciones y citas para el visor frontend."""
    estado = JOBS.get(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    result_path = estado.get("result_path")
    if not result_path or not Path(result_path).exists():
        raise HTTPException(status_code=404, detail="Resultado aún no disponible")
    return json.loads(Path(result_path).read_text(encoding="utf-8"))


class ReprocessRequest(BaseModel):
    job_id: str
    section_indices: list[int]


async def _ejecutar_reprocess(reprocess_id: str, job_id: str, section_indices: list[int]):
    estado_rep = JOBS[reprocess_id]
    estado_orig = JOBS.get(job_id)

    def on_progress(progreso, mensaje):
        estado_rep["progress"] = progreso
        estado_rep["message"] = mensaje
        log.info("[%s] re-proceso %3d%% — %s", reprocess_id, progreso, mensaje)

    try:
        carpeta = estado_orig.get("carpeta") if estado_orig else None
        documentos = estado_orig.get("documentos", []) if estado_orig else []
        if not carpeta or not Path(carpeta).exists():
            raise ValueError("Carpeta del trabajo original no disponible")

        estado_rep["phase"] = "queued"
        estado_rep["message"] = "Esperando cupo de ejecucion"
        async with JOB_EXECUTION_LIMIT:
            estado_rep["phase"] = "processing"
            estado_rep["message"] = "Reconstruyendo corpus local"
            await core.reprocessar_secciones(
                carpeta,
                section_indices,
                documentos,
                on_progress=on_progress,
            )

        # Propagar el result_path actualizado al job original.
        if estado_orig:
            estado_orig["result_path"] = str(Path(carpeta) / "result.json")

        estado_rep["phase"] = "completed"
        estado_rep["progress"] = 100
        estado_rep["message"] = "Re-proceso finalizado"
        log.info("[%s] Re-proceso completado (secciones: %s)", reprocess_id, section_indices)
    except Exception as exc:
        tb = traceback.format_exc()
        log.error("[%s] Falló el re-proceso:\n%s", reprocess_id, tb)
        estado_rep["phase"] = "error"
        estado_rep["error"] = f"{type(exc).__name__}: {exc}"
        estado_rep["trace"] = tb
        estado_rep["message"] = "Error en el re-proceso"


@app.post("/api/reprocess")
async def reprocess(req: ReprocessRequest):
    """Re-procesa secciones específicas de un trabajo completado."""
    if req.job_id not in JOBS:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    if not req.section_indices:
        raise HTTPException(status_code=400, detail="section_indices vacio")

    reprocess_id = _nuevo_job()
    log.info("[%s] Iniciando re-proceso de secciones %s para job %s",
             reprocess_id, req.section_indices, req.job_id)

    asyncio.create_task(_ejecutar_reprocess(reprocess_id, req.job_id, req.section_indices))
    return {"reprocess_id": reprocess_id}


@app.get("/api/reprocess-status/{reprocess_id}")
async def reprocess_status(reprocess_id: str):
    estado = JOBS.get(reprocess_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="reprocess_id no encontrado")
    return {k: v for k, v in estado.items() if k not in ("paths", "documentos")}


@app.get("/api/export/{job_id}")
async def export_docx(job_id: str):
    """Genera un .docx desde el result.json actual y lo descarga."""
    estado = JOBS.get(job_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    result_path = estado.get("result_path")
    if not result_path or not Path(result_path).exists():
        raise HTTPException(status_code=404, detail="Resultado no disponible")

    result_data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    carpeta = Path(result_path).parent
    ruta_docx = core.generar_docx_desde_resultado(result_data, carpeta)

    return FileResponse(
        str(ruta_docx),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=ruta_docx.name,
    )


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
