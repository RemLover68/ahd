#!/usr/bin/env python3
"""
licitacion_a_propuesta.py

Lógica central que automatiza el flujo de NotebookLM (librería de Teng Lin,
notebooklm-py) para procesar los documentos de una licitación:

  1. Crea un notebook y sube los documentos (PDFs).
  2. Envía el primer mensaje: pide la lista completa de ítems/requisitos.
  3. Espera la respuesta.
  4. Envía el segundo mensaje: pide redactar la propuesta del oferente.
  5. Guarda los resultados como .docx con formato bonito dentro de
     Output/<ID-de-la-licitación>/.

Se usa tanto desde la línea de comandos como desde el backend (server.py).

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
import re
import unicodedata
from pathlib import Path

from notebooklm import NotebookLMClient

# --------------------------------------------------------------------------- #
# Mensajes que se le mandan a NotebookLM (tal cual los pidió el usuario)
# --------------------------------------------------------------------------- #

MENSAJE_1 = (
    "quiero que me hagas una lista de todos y cada uno de los ítems que pide "
    "la licitación, todo lo requerido por el oferente y las condiciones. que "
    "esté totalmente completo, revisado, ordenado según el orden requerido de las secciones y que no falte ni se invente ninguno."
)

MENSAJE_2 = (
    "ok ahora quiero que tomes el output que acabas de darme y escribas una "
    "propuesta desde el punto de vista del oferente: si pide que se suministre "
    "x cosa, que se haga una propuesta que diga por ejemplo \"se oferta...\" "
    "\"se instalarán...\" \"se proveerá...\" y que cuente con cada uno de todos "
    "los puntos que piden y mantenga el orden requerido."
)

# Documentos por defecto (los que están en el repositorio). Solo se usan si se
# invoca el CLI sin argumentos; el backend siempre recibe archivos subidos.
DOCS_POR_DEFECTO = [
    "Bases_2378-57-L126.pdf",
    "decreto_exento_3892_O_243_obligacion_prs.pdf",
    "decreto_exento_3892_Torniquetes.pdf",
]

# Carpeta raíz donde se guardan todos los resultados (una subcarpeta por licitación).
OUTPUT_ROOT = "Output"


# --------------------------------------------------------------------------- #
# Identificación de la licitación
# --------------------------------------------------------------------------- #

# Formatos típicos de ID de licitación de Mercado Público (Chile), p. ej.:
#   2378-57-L126, 1057823-9-LP24, 750-12-LE23
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
    """Busca el ID de la licitación dentro de los PDFs.

    Devuelve el primer ID que calce con el formato de Mercado Público, o None
    si no encuentra ninguno.
    """
    for ruta in documentos:
        ruta = Path(ruta)
        if ruta.suffix.lower() != ".pdf":
            continue
        # Primero probamos con el propio nombre del archivo (suele traer el ID).
        m = _PATRON_ID_LICITACION.search(ruta.name)
        if m:
            return m.group(0)
        # Si no, miramos dentro del contenido.
        texto = _extraer_texto_pdf(ruta)
        m = _PATRON_ID_LICITACION.search(texto)
        if m:
            return m.group(0)
    return None


def _sanitizar(nombre):
    """Convierte un texto en un nombre de carpeta/archivo seguro."""
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = nombre.encode("ascii", "ignore").decode("ascii")
    nombre = re.sub(r"[^\w\s.-]", "", nombre).strip()
    nombre = re.sub(r"[\s]+", "_", nombre)
    return nombre or "licitacion"


def nombre_licitacion(documentos):
    """Determina el nombre identificador de la licitación.

    Usa el ID encontrado en los PDFs; si no encuentra ninguno, usa el nombre
    (sin extensión) del primer documento.
    """
    lic_id = extraer_id_licitacion(documentos)
    if lic_id:
        return _sanitizar(lic_id)
    if documentos:
        return _sanitizar(Path(documentos[0]).stem)
    return "licitacion"


# --------------------------------------------------------------------------- #
# Flujo principal contra NotebookLM
# --------------------------------------------------------------------------- #

def _noop(progreso, mensaje):  # callback de progreso por defecto
    pass


async def procesar(documentos, nombre_notebook, on_progress=_noop):
    """Sube los documentos, manda los dos mensajes y devuelve (lista_items, propuesta)."""
    # Según la versión de notebooklm-py, from_storage() puede ser síncrono (devuelve
    # el cliente/context manager directo) o asíncrono (devuelve una corrutina que hay
    # que await-ear). Soportamos ambos casos.
    import inspect

    cliente_cm = NotebookLMClient.from_storage()
    if inspect.iscoroutine(cliente_cm):
        cliente_cm = await cliente_cm

    async with cliente_cm as client:
        # 1. Crear el notebook
        on_progress(5, "Creando notebook")
        print(f"→ Creando notebook: {nombre_notebook!r}")
        nb = await client.notebooks.create(nombre_notebook)
        print(f"  notebook id: {nb.id}")

        # 2. Subir cada documento y esperar a que NotebookLM lo procese
        total = max(len(documentos), 1)
        for i, ruta in enumerate(documentos):
            ruta = Path(ruta)
            if not ruta.exists():
                raise FileNotFoundError(f"No se encontró el documento: {ruta}")
            on_progress(10 + int(40 * i / total), f"Subiendo {ruta.name}")
            print(f"→ Subiendo documento: {ruta.name}")
            source = await client.sources.add_file(nb.id, ruta)
            await client.sources.wait_until_ready(nb.id, source.id)
            print(f"  listo: {ruta.name}")

        # 3. Primer mensaje: lista de ítems requeridos
        on_progress(55, "Extrayendo requerimientos de la licitación")
        print("→ Enviando primer mensaje (lista de ítems de la licitación)...")
        r1 = await _ask_con_reintentos(client, nb.id, MENSAJE_1)
        print("  respuesta 1 recibida.")

        # 4. Segundo mensaje: redactar la propuesta del oferente.
        #    El chat de NotebookLM mantiene el contexto de la conversación dentro
        #    del mismo notebook, así que basta con mandar el mensaje tal cual
        #    ("el output que acabas de darme"). NO reenviamos la respuesta
        #    anterior: hacerlo genera un prompt enorme que NotebookLM responde
        #    vacío (ChatResponseParseError).
        on_progress(78, "Redactando la propuesta del oferente")
        print("→ Enviando segundo mensaje (redacción de la propuesta)...")
        r2 = await _ask_con_reintentos(client, nb.id, MENSAJE_2)
        print("  respuesta 2 recibida.")

        return r1.answer, r2.answer


async def _ask_con_reintentos(client, nb_id, mensaje, intentos=4):
    """Envía un mensaje al chat reintentando ante respuestas vacías/no parseables.

    El error ChatResponseParseError suele ser intermitente (la API devuelve un
    stream vacío). Reintentamos con backoff exponencial antes de fallar.
    """
    from notebooklm.exceptions import ChatResponseParseError

    for intento in range(1, intentos + 1):
        try:
            return await client.chat.ask(nb_id, mensaje)
        except ChatResponseParseError:
            if intento == intentos:
                raise
            espera = 2 ** intento  # 2s, 4s, 8s...
            print(f"  respuesta vacía, reintentando en {espera}s "
                  f"(intento {intento}/{intentos - 1})...")
            await asyncio.sleep(espera)


# --------------------------------------------------------------------------- #
# Orquestación de alto nivel (usada por el CLI y por el backend)
# --------------------------------------------------------------------------- #

async def generar_propuesta(documentos, output_root=OUTPUT_ROOT, on_progress=_noop,
                            nombre_notebook=None):
    """Procesa la licitación de punta a punta y guarda los .docx.

    Devuelve un dict con el id de la licitación, la carpeta de salida y la lista
    de archivos generados (cada uno con id, título, descripción y ruta).
    """
    documentos = [Path(d) for d in documentos]

    on_progress(2, "Identificando la licitación")
    lic = nombre_licitacion(documentos)
    if nombre_notebook is None:
        nombre_notebook = f"Licitación {lic}"

    carpeta = Path(output_root) / lic
    carpeta.mkdir(parents=True, exist_ok=True)

    lista_items, propuesta = await procesar(documentos, nombre_notebook, on_progress)

    on_progress(92, "Generando documentos .docx")
    fecha = _dt.date.today().strftime("%d/%m/%Y")

    ruta_propuesta = carpeta / f"Propuesta_Tecnica_{lic}.docx"
    guardar_docx("Propuesta Técnica del Oferente", propuesta, str(ruta_propuesta))

    ruta_items = carpeta / f"Lista_Items_{lic}.docx"
    guardar_docx("Ítems Requeridos por la Licitación", lista_items, str(ruta_items))

    on_progress(100, "Proceso finalizado")

    return {
        "licitacion": lic,
        "carpeta": str(carpeta),
        "archivos": [
            {
                "id": "propuesta",
                "title": "Propuesta técnica",
                "description": "Propuesta técnica del oferente, punto por punto.",
                "filename": ruta_propuesta.name,
                "path": str(ruta_propuesta),
                "date": fecha,
            },
            {
                "id": "items",
                "title": "Lista de ítems",
                "description": "Ítems y condiciones requeridos por la licitación.",
                "filename": ruta_items.name,
                "path": str(ruta_items),
                "date": fecha,
            },
        ],
    }


# --------------------------------------------------------------------------- #
# Generación del .docx con formato bonito
# --------------------------------------------------------------------------- #

def guardar_docx(titulo, contenido, ruta_salida):
    """Convierte el texto (markdown sencillo) en un .docx con formato."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    doc = Document()

    # --- Estilo base del documento ---
    base = doc.styles["Normal"]
    base.font.name = "Calibri"
    base.font.size = Pt(11)

    # --- Portada / título ---
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

    # --- Cuerpo: parseo de markdown sencillo ---
    for linea in contenido.splitlines():
        _agregar_linea(doc, linea)

    doc.save(ruta_salida)
    print(f"→ Documento guardado en: {ruta_salida}")


def _agregar_linea(doc, linea):
    """Interpreta una línea de markdown sencillo y la agrega al documento."""
    from docx.shared import Pt

    texto = linea.rstrip()
    if not texto.strip():
        return

    stripped = texto.lstrip()

    # Encabezados markdown: #, ##, ###
    if stripped.startswith("#"):
        nivel = len(stripped) - len(stripped.lstrip("#"))
        titulo = stripped[nivel:].strip()
        doc.add_heading(titulo, level=min(nivel, 4))
        return

    # Viñetas: -, *, •
    if stripped[:2] in ("- ", "* ") or stripped.startswith("• "):
        p = doc.add_paragraph(style="List Bullet")
        _runs_con_negrita(p, stripped[2:].strip())
        return

    # Listas numeradas: "1. ", "2) ", etc.
    if _es_lista_numerada(stripped):
        contenido = stripped.split(None, 1)[1] if " " in stripped else stripped
        p = doc.add_paragraph(style="List Number")
        _runs_con_negrita(p, contenido)
        return

    # Párrafo normal
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
        # Las posiciones impares estaban entre ** ** → negrita
        if i % 2 == 1:
            run.bold = True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Procesa una licitación en NotebookLM y genera la propuesta en .docx"
    )
    parser.add_argument(
        "documentos",
        nargs="*",
        default=DOCS_POR_DEFECTO,
        help="Documentos a subir (por defecto: los PDFs de la licitación en el repo).",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_ROOT,
        help=f"Carpeta raíz de salida (por defecto: {OUTPUT_ROOT}).",
    )
    args = parser.parse_args()

    resultado = asyncio.run(
        generar_propuesta(args.documentos, output_root=args.output)
    )

    print(f"\n✓ Licitación: {resultado['licitacion']}")
    print(f"✓ Carpeta:   {resultado['carpeta']}")
    for a in resultado["archivos"]:
        print(f"  - {a['title']}: {a['path']}")


if __name__ == "__main__":
    main()
