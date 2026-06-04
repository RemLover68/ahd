#!/usr/bin/env python3
"""
licitacion_a_propuesta.py

Lógica central que automatiza el flujo de NotebookLM (librería de Teng Lin,
notebooklm-py) para procesar los documentos de una licitación.

En vez de pedir toda la propuesta en un único turno (lo que produce respuestas
poco profundas, porque NotebookLM tiene un tope de longitud por respuesta y
tiende a resumir), se usa un PIPELINE POR SECCIONES con CHECKPOINTS:

  Fase 0  Subir los documentos al notebook.
  Fase 1  Lista completa de ítems/requisitos de la licitación.
  Fase 2  Índice de secciones/subsistemas (lo define NotebookLM).
  Fase 3  Por cada sección: requisitos exhaustivos          -> checkpoint.
  Fase 4  Por cada sección: propuesta del oferente          -> checkpoint.
  Fase 5  Por cada sección: matriz de cumplimiento          -> checkpoint.
  Fase 6  Resumen ejecutivo + ensamblado de los .docx finales.

Cada resultado intermedio se guarda en Output/<ID>/checkpoints/, de modo que un
fallo no bota todo el trabajo y se pueda auditar/regenerar por partes.

Salidas en Output/<ID-de-la-licitación>/:
  - Propuesta_Tecnica_<ID>.docx
  - Lista_Items_<ID>.docx
  - Matriz_Cumplimiento_<ID>.docx

Uso (CLI):
    python licitacion_a_propuesta.py
    python licitacion_a_propuesta.py doc1.pdf doc2.pdf

Requisitos:
    pip install -r requirements.txt
    playwright install chromium
    notebooklm login        # autenticación con Google (una sola vez)
"""

import argparse
import asyncio
import datetime as _dt
import inspect
import re
import unicodedata
from pathlib import Path

from notebooklm import NotebookLMClient

# --------------------------------------------------------------------------- #
# Prompts
# --------------------------------------------------------------------------- #

# Fase 1: lista completa de ítems (igual que la versión original).
# Directiva común: evita que NotebookLM se trabe en si los documentos son o no
# "bases de licitación" (a veces son PID / términos de referencia) y pida
# confirmación en vez de hacer la tarea. Se añade a todos los prompts.
_DIRECTIVA = (
    " IMPORTANTE: trabaja directamente con el contenido de los documentos "
    "entregados, sean bases de licitación, términos de referencia o proyectos "
    "de ingeniería de detalle (PID). Entrega de inmediato lo solicitado: NO "
    "pidas confirmación, NO hagas preguntas de vuelta y NO comentes sobre la "
    "naturaleza, tipo o destinatario de los documentos; usa lo que contienen."
)

MENSAJE_LISTA = (
    "quiero que me hagas una lista de todos y cada uno de los ítems, "
    "requerimientos técnicos, equipos, funcionalidades, especificaciones y "
    "condiciones que establecen los documentos para quien debe ejecutar la "
    "obra/servicio. que esté totalmente completa, revisada, con cantidades, "
    "normas y modelos cuando aparezcan, ordenada según el orden de las "
    "secciones de los documentos y que no falte ni se invente ninguno."
    + _DIRECTIVA
)

# Fase 2: índice de secciones (NotebookLM las define).
MENSAJE_INDICE = (
    "A partir de las fuentes, dame únicamente el ÍNDICE de las secciones o "
    "subsistemas técnicos que cubren los documentos y que debe abordar la "
    "propuesta técnica. Devuélvelo como una lista numerada, una sección por "
    "línea, SOLO los títulos, sin ninguna descripción, sin detalle y sin "
    "sub-puntos." + _DIRECTIVA
)

# Fase 6: resumen ejecutivo.
MENSAJE_RESUMEN = (
    "Redacta un breve resumen ejecutivo (máximo 200 palabras) de la propuesta "
    "técnica del oferente, destacando el alcance general y los principales "
    "sistemas y equipos ofertados." + _DIRECTIVA
)


def _prompt_requisitos(seccion):
    return (
        f"Enfócate EXCLUSIVAMENTE en la sección: «{seccion}».\n"
        "Lista de forma exhaustiva y detallada TODOS los ítems, equipos, "
        "cantidades, marcas o modelos (si la fuente los indica), normas y "
        "estándares, valores numéricos, características técnicas y condiciones "
        "que los documentos establecen para esta sección. Un punto por "
        "requisito. No resumas, no agrupes, no omitas ninguno y no inventes "
        "nada. Cita la fuente cuando corresponda." + _DIRECTIVA
    )


def _prompt_propuesta(seccion, requisitos):
    return (
        f"Redacta la propuesta técnica del oferente EXCLUSIVAMENTE para la "
        f"sección «{seccion}», respondiendo punto por punto a CADA uno de los "
        "siguientes requisitos. Usa un estilo propositivo: «se proveerá…», «se "
        "instalará…», «se ofertará…». Mantén todo el nivel de detalle "
        "(cantidades, modelos, normas, valores) y no omitas ningún punto."
        + _DIRECTIVA +
        "\n\n--- Requisitos de esta sección ---\n"
        f"{_truncar(requisitos)}"
    )


def _prompt_matriz(seccion, requisitos):
    return (
        f"Para la sección «{seccion}», genera una matriz de cumplimiento en "
        "formato de tabla Markdown con EXACTAMENTE estas columnas:\n"
        "| Requisito | Cumplimiento | Referencia |\n"
        "Una fila por requisito. En 'Cumplimiento' indica cómo lo cumple el "
        "oferente (empieza con CUMPLE y una breve explicación). En 'Referencia' "
        "indica la fuente. No omitas requisitos y responde SOLO con la tabla."
        + _DIRECTIVA +
        "\n\n--- Requisitos de esta sección ---\n"
        f"{_truncar(requisitos)}"
    )


# Límite de caracteres al re-inyectar requisitos en un prompt (evita que el
# prompt crezca tanto que NotebookLM devuelva una respuesta vacía).
_MAX_CTX = 4000
# Tope mucho más chico para el reintento de rescate, cuando ya fallaron varios
# intentos con el contexto normal.
_MAX_CTX_RESCATE = 1800
# Máximo de secciones a procesar (cota de seguridad para no dispararse).
_MAX_SECCIONES = 20


def _truncar(texto, limite=_MAX_CTX):
    if texto and len(texto) > limite:
        return texto[:limite] + "\n[...]"
    return texto


# Documentos por defecto (solo para el CLI sin argumentos).
DOCS_POR_DEFECTO = [
    "Bases_2378-57-L126.pdf",
    "decreto_exento_3892_O_243_obligacion_prs.pdf",
    "decreto_exento_3892_Torniquetes.pdf",
]

# Carpeta raíz donde se guardan los resultados (una subcarpeta por licitación).
OUTPUT_ROOT = "Output"


# --------------------------------------------------------------------------- #
# Identificación de la licitación
# --------------------------------------------------------------------------- #

# IDs típicos de Mercado Público (Chile), p. ej.: 2378-57-L126, 1057823-9-LP24
_PATRON_ID_LICITACION = re.compile(r"\b\d{3,8}-\d{1,4}-[A-Z]{1,3}\d{1,4}\b")


def _extraer_texto_pdf(ruta, max_paginas=6):
    """Devuelve el texto de las primeras páginas de un PDF (o '' si no se puede)."""
    try:
        from pypdf import PdfReader

        lector = PdfReader(str(ruta))
        paginas = lector.pages[:max_paginas]
        return "\n".join((p.extract_text() or "") for p in paginas)
    except Exception:
        return ""


def extraer_id_licitacion(documentos):
    """Busca el ID de la licitación en el nombre o contenido de los PDFs."""
    for ruta in documentos:
        ruta = Path(ruta)
        if ruta.suffix.lower() != ".pdf":
            continue
        m = _PATRON_ID_LICITACION.search(ruta.name)
        if m:
            return m.group(0)
        m = _PATRON_ID_LICITACION.search(_extraer_texto_pdf(ruta))
        if m:
            return m.group(0)
    return None


def _sanitizar(nombre):
    """Convierte un texto en un nombre de carpeta/archivo seguro."""
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = nombre.encode("ascii", "ignore").decode("ascii")
    nombre = re.sub(r"[^\w\s.-]", "", nombre).strip()
    nombre = re.sub(r"\s+", "_", nombre)
    return nombre or "licitacion"


def nombre_licitacion(documentos):
    """ID de la licitación (de los PDFs) o, si no se encuentra, nombre del 1er archivo."""
    lic_id = extraer_id_licitacion(documentos)
    if lic_id:
        return _sanitizar(lic_id)
    if documentos:
        return _sanitizar(Path(documentos[0]).stem)
    return "licitacion"


# --------------------------------------------------------------------------- #
# Utilidades de NotebookLM
# --------------------------------------------------------------------------- #

def _noop(progreso, mensaje):  # callback de progreso por defecto
    pass


async def _abrir_cliente():
    """Abre el cliente soportando from_storage() síncrono o asíncrono según versión."""
    cm = NotebookLMClient.from_storage()
    if inspect.iscoroutine(cm):
        cm = await cm
    return cm


def _excepciones_de_parseo():
    """Excepción(es) de respuesta vacía/no parseable de notebooklm (varía por versión)."""
    try:
        import notebooklm.exceptions as exc
    except Exception:
        return (Exception,)

    candidatos = ["ChatResponseParseError", "ResponseParseError",
                  "ChatParseError", "ParseError"]
    encontradas = tuple(
        getattr(exc, n) for n in candidatos
        if isinstance(getattr(exc, n, None), type)
    )
    if encontradas:
        return encontradas
    base = getattr(exc, "NotebookLMError", None)
    return (base,) if isinstance(base, type) else (Exception,)


# Marcadores de una respuesta "evasiva": NotebookLM, en vez de hacer la tarea,
# pide confirmación o comenta que los documentos no son lo que cree el prompt.
_MARCADORES_EVASION = (
    "por favor confírma", "confírmamelo", "confírmame", "¿quieres que",
    "¿deseas que", "¿te gustaría", "si tu objetivo es", "con gusto elaborar",
    "no contienen las bases", "no corresponden a las bases", "puedo elaborar",
    "házmelo saber", "avísame si", "me confirmas", "¿procedo",
)
# Confirmación que se manda para destrabar una respuesta evasiva.
_MENSAJE_CONFIRMACION = (
    "Sí, procede ahora. Entrega directamente y por completo el contenido "
    "solicitado en mi mensaje anterior, sin pedir confirmación, sin hacer "
    "preguntas y sin comentar sobre el tipo de documento."
)


def _es_evasiva(texto):
    if not texto:
        return False
    t = texto.lower()
    return any(m in t for m in _MARCADORES_EVASION)


async def _ask(client, nb_id, mensaje, intentos=4, anti_evasion=True):
    """Envía un mensaje al chat reintentando ante respuestas vacías/no parseables.

    Si la respuesta resulta evasiva (pide confirmación en vez de hacer la tarea),
    manda una confirmación y usa esa segunda respuesta.
    """
    errores = _excepciones_de_parseo()
    for intento in range(1, intentos + 1):
        try:
            r = await client.chat.ask(nb_id, mensaje)
            respuesta = r.answer
            if anti_evasion and _es_evasiva(respuesta):
                print("  ⚠ respuesta evasiva (pidió confirmación); insistiendo...")
                r2 = await client.chat.ask(nb_id, _MENSAJE_CONFIRMACION)
                if r2.answer and not _es_evasiva(r2.answer):
                    return r2.answer
            return respuesta
        except errores:
            if intento == intentos:
                raise
            espera = 2 ** intento  # 2s, 4s, 8s...
            print(f"  respuesta vacía, reintentando en {espera}s "
                  f"(intento {intento}/{intentos - 1})...")
            await asyncio.sleep(espera)


def _parsear_indice(texto):
    """Extrae los títulos de sección de la respuesta de índice de NotebookLM."""
    secciones = []
    for linea in texto.splitlines():
        l = linea.strip()
        if not l:
            continue
        # "1. Título", "1) Título", "- Título", "* Título", "## Título"
        m = re.match(r"^\s*(?:\d+[.)]|[-*•]|#+)\s+(.*)$", l)
        titulo = (m.group(1) if m else l).strip()
        titulo = titulo.strip("*").strip()
        # Descartamos líneas que claramente no son títulos.
        if len(titulo) < 3 or len(titulo) > 160:
            continue
        if titulo.lower().startswith(("a continuación", "estas son", "el índice",
                                      "aquí", "la propuesta")):
            continue
        secciones.append(titulo)
        if len(secciones) >= _MAX_SECCIONES:
            break
    return secciones


# --------------------------------------------------------------------------- #
# Pipeline contra NotebookLM
# --------------------------------------------------------------------------- #

def _leer_si_existe(ruta):
    p = Path(ruta)
    if p.exists() and p.stat().st_size > 0:
        texto = p.read_text(encoding="utf-8")
        # Un checkpoint evasivo (NotebookLM pidió confirmación) se considera
        # inválido, para que al reanudar se vuelva a pedir en lugar de heredarlo.
        if _es_evasiva(texto):
            print(f"  ⚠ checkpoint evasivo, se regenerará: {Path(ruta).name}")
            return None
        return texto
    return None


def _leer_cuerpo_checkpoint(ruta):
    """Lee un checkpoint y devuelve el contenido sin el encabezado '# Sección'."""
    texto = _leer_si_existe(ruta)
    if texto is None:
        return None
    lineas = texto.splitlines()
    if lineas and lineas[0].startswith("# "):
        # Saltamos el encabezado y la línea en blanco que le sigue.
        return "\n".join(lineas[2:] if len(lineas) > 1 and lineas[1] == "" else lineas[1:])
    return texto


async def _ask_con_rescate(client, nb_id, mensaje_normal, mensaje_rescate):
    """Intenta el prompt normal; si falla, hace un último intento con uno más chico."""
    try:
        return await _ask(client, nb_id, mensaje_normal)
    except Exception as exc:
        print(f"  ⚠ falló con contexto normal ({exc}); rescate con contexto reducido...")
        await asyncio.sleep(5)
        return await _ask(client, nb_id, mensaje_rescate, intentos=2)


async def _ejecutar_pipeline(documentos, nombre_notebook, carpeta, on_progress):
    """Corre el pipeline reanudando desde checkpoints existentes."""
    ckpt = Path(carpeta) / "checkpoints"
    (ckpt / "01_requisitos").mkdir(parents=True, exist_ok=True)
    (ckpt / "02_propuesta").mkdir(parents=True, exist_ok=True)
    (ckpt / "03_matriz").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Pre-escaneo de checkpoints: ¿qué hay que pedirle a NotebookLM?
    # ------------------------------------------------------------------ #
    lista_items = _leer_si_existe(ckpt / "00_lista_items.md")
    indice_raw = _leer_si_existe(ckpt / "00_indice_secciones.md")
    resumen = _leer_si_existe(ckpt / "04_resumen.md")
    secciones = _parsear_indice(indice_raw) if indice_raw else None

    def _ruta_seccion(idx, seccion, sub):
        slug = f"{idx + 1:02d}_{_sanitizar(seccion)[:40]}"
        return ckpt / sub / f"{slug}.md"

    # ¿Necesitamos abrir el notebook? Solo si falta cualquier salida.
    necesita_chat = lista_items is None or indice_raw is None or resumen is None
    if secciones:
        for i, s in enumerate(secciones):
            if (_leer_cuerpo_checkpoint(_ruta_seccion(i, s, "01_requisitos")) is None
                    or _leer_cuerpo_checkpoint(_ruta_seccion(i, s, "02_propuesta")) is None
                    or _leer_cuerpo_checkpoint(_ruta_seccion(i, s, "03_matriz")) is None):
                necesita_chat = True
                break
    else:
        necesita_chat = True

    if not necesita_chat:
        print("→ Todos los checkpoints presentes: se ensambla sin tocar NotebookLM.")
        on_progress(95, "Reanudando desde checkpoints")
        datos = [{
            "seccion": s,
            "requisitos": _leer_cuerpo_checkpoint(_ruta_seccion(i, s, "01_requisitos")),
            "propuesta": _leer_cuerpo_checkpoint(_ruta_seccion(i, s, "02_propuesta")),
            "matriz": _leer_cuerpo_checkpoint(_ruta_seccion(i, s, "03_matriz")),
        } for i, s in enumerate(secciones)]
        return {"lista_items": lista_items, "resumen": resumen, "secciones": datos}

    # ------------------------------------------------------------------ #
    # Abrimos el cliente y ejecutamos solo lo que falta.
    # ------------------------------------------------------------------ #
    cliente_cm = await _abrir_cliente()
    async with cliente_cm as client:
        on_progress(5, "Creando notebook")
        nb = await client.notebooks.create(nombre_notebook)
        print(f"  notebook id: {nb.id}")

        total_docs = max(len(documentos), 1)
        for i, ruta in enumerate(documentos):
            ruta = Path(ruta)
            if not ruta.exists():
                raise FileNotFoundError(f"No se encontró el documento: {ruta}")
            on_progress(8 + int(22 * i / total_docs), f"Subiendo {ruta.name}")
            print(f"→ Subiendo documento: {ruta.name}")
            source = await client.sources.add_file(nb.id, ruta)
            await client.sources.wait_until_ready(nb.id, source.id)

        # Fase 1: lista completa de ítems.
        if lista_items is None:
            on_progress(32, "Extrayendo la lista de ítems de la licitación")
            lista_items = await _ask(client, nb.id, MENSAJE_LISTA)
            (ckpt / "00_lista_items.md").write_text(lista_items, encoding="utf-8")
        else:
            print("✓ checkpoint: lista de ítems (saltando)")
            on_progress(32, "Lista de ítems (desde checkpoint)")

        # Fase 2: índice de secciones.
        if indice_raw is None:
            on_progress(38, "Determinando las secciones de la propuesta")
            indice_raw = await _ask(client, nb.id, MENSAJE_INDICE)
            (ckpt / "00_indice_secciones.md").write_text(indice_raw, encoding="utf-8")
            secciones = _parsear_indice(indice_raw)
        else:
            print("✓ checkpoint: índice de secciones (saltando)")

        if not secciones:
            secciones = ["Propuesta técnica general"]
        print(f"  secciones detectadas: {len(secciones)}")

        # Fases 3-5: por cada sección, requisitos + propuesta + matriz.
        datos = []
        fallos = []
        n = len(secciones)
        for idx, seccion in enumerate(secciones):
            base = 40 + int(50 * idx / n)
            ruta_req = _ruta_seccion(idx, seccion, "01_requisitos")
            ruta_prop = _ruta_seccion(idx, seccion, "02_propuesta")
            ruta_mat = _ruta_seccion(idx, seccion, "03_matriz")

            requisitos = _leer_cuerpo_checkpoint(ruta_req)
            if requisitos is None:
                on_progress(base, f"Requisitos: {seccion}")
                print(f"→ [{idx+1}/{n}] Requisitos: {seccion}")
                try:
                    requisitos = await _ask(client, nb.id, _prompt_requisitos(seccion))
                    ruta_req.write_text(f"# {seccion}\n\n{requisitos}", encoding="utf-8")
                except Exception as exc:
                    print(f"  ✗ requisitos fallaron: {exc}")
                    fallos.append((seccion, "requisitos", str(exc)))
                    datos.append({"seccion": seccion, "requisitos": None,
                                  "propuesta": None, "matriz": None})
                    continue
            else:
                print(f"✓ [{idx+1}/{n}] requisitos (desde checkpoint): {seccion}")

            propuesta = _leer_cuerpo_checkpoint(ruta_prop)
            if propuesta is None:
                on_progress(base + 3, f"Propuesta: {seccion}")
                print(f"→ [{idx+1}/{n}] Propuesta: {seccion}")
                try:
                    propuesta = await _ask_con_rescate(
                        client, nb.id,
                        _prompt_propuesta(seccion, requisitos),
                        _prompt_propuesta(
                            seccion,
                            _truncar(requisitos, _MAX_CTX_RESCATE)),
                    )
                    ruta_prop.write_text(f"# {seccion}\n\n{propuesta}", encoding="utf-8")
                except Exception as exc:
                    print(f"  ✗ propuesta falló incluso con rescate: {exc}")
                    fallos.append((seccion, "propuesta", str(exc)))
                    propuesta = None
            else:
                print(f"✓ [{idx+1}/{n}] propuesta (desde checkpoint): {seccion}")

            matriz = _leer_cuerpo_checkpoint(ruta_mat)
            if matriz is None:
                on_progress(base + 6, f"Matriz: {seccion}")
                print(f"→ [{idx+1}/{n}] Matriz: {seccion}")
                try:
                    matriz = await _ask_con_rescate(
                        client, nb.id,
                        _prompt_matriz(seccion, requisitos),
                        _prompt_matriz(
                            seccion,
                            _truncar(requisitos, _MAX_CTX_RESCATE)),
                    )
                    ruta_mat.write_text(f"# {seccion}\n\n{matriz}", encoding="utf-8")
                except Exception as exc:
                    print(f"  ✗ matriz falló incluso con rescate: {exc}")
                    fallos.append((seccion, "matriz", str(exc)))
                    matriz = None
            else:
                print(f"✓ [{idx+1}/{n}] matriz (desde checkpoint): {seccion}")

            datos.append({
                "seccion": seccion,
                "requisitos": requisitos,
                "propuesta": propuesta,
                "matriz": matriz,
            })

        # Fase 6: resumen ejecutivo.
        if resumen is None:
            on_progress(92, "Redactando el resumen ejecutivo")
            try:
                resumen = await _ask(client, nb.id, MENSAJE_RESUMEN)
                (ckpt / "04_resumen.md").write_text(resumen, encoding="utf-8")
            except Exception as exc:
                print(f"  ✗ resumen falló: {exc}")
                resumen = "_Resumen ejecutivo no disponible (falló su generación)._"
                fallos.append(("(resumen ejecutivo)", "resumen", str(exc)))
        else:
            print("✓ checkpoint: resumen ejecutivo (saltando)")

        if fallos:
            print("\n⚠ Pipeline completado con fallos parciales:")
            for s, etapa, err in fallos:
                print(f"   - {s} [{etapa}]: {err}")
            (ckpt / "_fallos.md").write_text(
                "\n".join(f"- **{s}** [{e}]: {er}" for s, e, er in fallos),
                encoding="utf-8")

        return {"lista_items": lista_items, "resumen": resumen, "secciones": datos}


# --------------------------------------------------------------------------- #
# Orquestación de alto nivel (usada por el CLI y por el backend)
# --------------------------------------------------------------------------- #

async def generar_propuesta(documentos, output_root=OUTPUT_ROOT, on_progress=_noop,
                            nombre_notebook=None):
    """Procesa la licitación de punta a punta y guarda los .docx.

    Devuelve un dict con el id de la licitación, la carpeta de salida y la lista
    de archivos generados.
    """
    documentos = [Path(d) for d in documentos]

    on_progress(2, "Identificando la licitación")
    lic = nombre_licitacion(documentos)
    if nombre_notebook is None:
        nombre_notebook = f"Licitación {lic}"

    carpeta = Path(output_root) / lic
    carpeta.mkdir(parents=True, exist_ok=True)

    res = await _ejecutar_pipeline(documentos, nombre_notebook, carpeta, on_progress)

    on_progress(95, "Generando documentos .docx")
    fecha = _dt.date.today().strftime("%d/%m/%Y")

    sin_dato = "_Esta sección no se pudo generar en esta ejecución. " \
               "Re-ejecutar el proceso para reintentarla; el resto se conserva " \
               "desde los checkpoints._"

    # Propuesta técnica: resumen ejecutivo + propuesta de cada sección.
    cuerpo_propuesta = ["## Resumen ejecutivo", res["resumen"] or sin_dato, ""]
    for d in res["secciones"]:
        cuerpo_propuesta.append(f"## {d['seccion']}")
        cuerpo_propuesta.append(d["propuesta"] or sin_dato)
        cuerpo_propuesta.append("")
    ruta_propuesta = carpeta / f"Propuesta_Tecnica_{lic}.docx"
    guardar_docx("Propuesta Técnica del Oferente",
                 "\n".join(cuerpo_propuesta), str(ruta_propuesta))

    # Lista de ítems.
    ruta_items = carpeta / f"Lista_Items_{lic}.docx"
    guardar_docx("Ítems Requeridos por la Licitación",
                 res["lista_items"] or sin_dato, str(ruta_items))

    # Matriz de cumplimiento (tablas por sección).
    ruta_matriz = carpeta / f"Matriz_Cumplimiento_{lic}.docx"
    guardar_matriz_docx(
        "Matriz de Cumplimiento",
        [(d["seccion"], d["matriz"] or sin_dato) for d in res["secciones"]],
        str(ruta_matriz),
    )

    on_progress(100, "Proceso finalizado")

    return {
        "licitacion": lic,
        "carpeta": str(carpeta),
        "archivos": [
            {"id": "propuesta", "title": "Propuesta técnica",
             "description": "Propuesta del oferente, sección por sección y punto por punto.",
             "filename": ruta_propuesta.name, "path": str(ruta_propuesta), "date": fecha},
            {"id": "items", "title": "Lista de ítems",
             "description": "Ítems y condiciones requeridos por la licitación.",
             "filename": ruta_items.name, "path": str(ruta_items), "date": fecha},
            {"id": "matriz", "title": "Matriz de cumplimiento",
             "description": "Requisito → cumplimiento → referencia, por sección.",
             "filename": ruta_matriz.name, "path": str(ruta_matriz), "date": fecha},
        ],
    }


# --------------------------------------------------------------------------- #
# Generación de .docx con formato bonito
# --------------------------------------------------------------------------- #

def _nuevo_doc(titulo):
    """Crea un documento con estilo base y portada."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    doc = Document()
    base = doc.styles["Normal"]
    base.font.name = "Calibri"
    base.font.size = Pt(11)

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t.add_run(titulo)
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fecha = _dt.date.today().strftime("%d-%m-%Y")
    srun = sub.add_run(f"Propuesta del oferente · {fecha}")
    srun.italic = True
    srun.font.size = Pt(11)
    srun.font.color.rgb = RGBColor(0x70, 0x70, 0x70)

    doc.add_paragraph()  # espacio
    return doc


def guardar_docx(titulo, contenido, ruta_salida):
    """Convierte texto (markdown sencillo) en un .docx con formato."""
    doc = _nuevo_doc(titulo)
    for linea in contenido.splitlines():
        _agregar_linea(doc, linea)
    doc.save(ruta_salida)
    print(f"→ Documento guardado en: {ruta_salida}")


def guardar_matriz_docx(titulo, secciones_tablas, ruta_salida):
    """Genera un .docx con una tabla de cumplimiento por sección."""
    doc = _nuevo_doc(titulo)
    for seccion, tabla_md in secciones_tablas:
        doc.add_heading(seccion, level=2)
        filas = _parsear_tabla_md(tabla_md)
        if filas:
            _agregar_tabla(doc, filas)
        else:
            # Si no vino como tabla, lo volcamos como texto para no perderlo.
            for linea in tabla_md.splitlines():
                _agregar_linea(doc, linea)
        doc.add_paragraph()
    doc.save(ruta_salida)
    print(f"→ Documento guardado en: {ruta_salida}")


def _parsear_tabla_md(texto):
    """Extrae las filas de una tabla Markdown (lista de listas de celdas)."""
    filas = []
    for linea in texto.splitlines():
        l = linea.strip()
        if not l.startswith("|"):
            continue
        celdas = [c.strip() for c in l.strip("|").split("|")]
        # Saltar la fila separadora (---|---).
        if celdas and all(set(c) <= set("-: ") and c != "" for c in celdas):
            continue
        filas.append(celdas)
    return filas


def _agregar_tabla(doc, filas):
    """Agrega una tabla al documento (primera fila como encabezado en negrita)."""
    ncols = max(len(f) for f in filas)
    tabla = doc.add_table(rows=0, cols=ncols)
    tabla.style = "Table Grid"
    for i, fila in enumerate(filas):
        celdas = tabla.add_row().cells
        for j in range(ncols):
            valor = fila[j].replace("**", "") if j < len(fila) else ""
            celda = celdas[j]
            celda.text = ""
            run = celda.paragraphs[0].add_run(valor)
            if i == 0:
                run.bold = True


def _agregar_linea(doc, linea):
    """Interpreta una línea de markdown sencillo y la agrega al documento."""
    texto = linea.rstrip()
    if not texto.strip():
        return

    stripped = texto.lstrip()

    if stripped.startswith("#"):
        nivel = len(stripped) - len(stripped.lstrip("#"))
        titulo = stripped[nivel:].strip()
        doc.add_heading(titulo, level=min(nivel, 4))
        return

    if stripped[:2] in ("- ", "* ") or stripped.startswith("• "):
        p = doc.add_paragraph(style="List Bullet")
        _runs_con_negrita(p, stripped[2:].strip())
        return

    if _es_lista_numerada(stripped):
        contenido = stripped.split(None, 1)[1] if " " in stripped else stripped
        p = doc.add_paragraph(style="List Number")
        _runs_con_negrita(p, contenido)
        return

    p = doc.add_paragraph()
    _runs_con_negrita(p, stripped)


def _es_lista_numerada(texto):
    cabeza = texto.split(None, 1)[0] if texto.split() else ""
    return cabeza[:-1].isdigit() and cabeza[-1:] in (".", ")")


def _runs_con_negrita(parrafo, texto):
    """Agrega texto a un párrafo respetando el **negrita** de markdown."""
    partes = texto.split("**")
    for i, parte in enumerate(partes):
        if not parte:
            continue
        run = parrafo.add_run(parte)
        if i % 2 == 1:
            run.bold = True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Procesa una licitación en NotebookLM y genera los .docx"
    )
    parser.add_argument("documentos", nargs="*", default=DOCS_POR_DEFECTO,
                        help="Documentos a subir (por defecto: los PDFs del repo).")
    parser.add_argument("--output", default=OUTPUT_ROOT,
                        help=f"Carpeta raíz de salida (por defecto: {OUTPUT_ROOT}).")
    args = parser.parse_args()

    def progreso(p, m):
        print(f"  [{p:3d}%] {m}")

    resultado = asyncio.run(
        generar_propuesta(args.documentos, output_root=args.output, on_progress=progreso)
    )

    print(f"\n✓ Licitación: {resultado['licitacion']}")
    print(f"✓ Carpeta:   {resultado['carpeta']}")
    for a in resultado["archivos"]:
        print(f"  - {a['title']}: {a['path']}")


if __name__ == "__main__":
    main()
