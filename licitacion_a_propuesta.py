#!/usr/bin/env python3
"""
licitacion_a_propuesta.py

Script simple que automatiza el flujo de NotebookLM (librería de Teng Lin,
notebooklm-py) para procesar los documentos de una licitación:

  1. Crea un notebook y sube los documentos (PDFs).
  2. Envía el primer mensaje: pide la lista completa de ítems/requisitos.
  3. Espera la respuesta.
  4. Envía el segundo mensaje: pide redactar la propuesta del oferente.
  5. Guarda la respuesta final como un .docx con formato bonito.

Uso:
    python licitacion_a_propuesta.py
    python licitacion_a_propuesta.py doc1.pdf doc2.pdf --salida propuesta.docx

Requisitos:
    pip install "notebooklm-py[browser]" python-docx
    playwright install chromium
    notebooklm login        # autenticación con Google (una sola vez)
"""

import argparse
import asyncio
import datetime as _dt
from pathlib import Path

from notebooklm import NotebookLMClient

# --------------------------------------------------------------------------- #
# Mensajes que se le mandan a NotebookLM (tal cual los pidió el usuario)
# --------------------------------------------------------------------------- #

MENSAJE_1 = (
    "quiero que me hagas una lista de todos y cada uno de los ítems que pide "
    "la licitación, todo lo requerido por el oferente y las condiciones. que "
    "esté totalmente completo, revisado y no falte ni se invente ninguno."
)

MENSAJE_2 = (
    "ok ahroa quiero que tomes el output que acabas de darme y escribas una "
    "propuesta desde el punto de vista del oferente: si pide que se suministre "
    "x cosa, que se haga una propuesta que diga por ejemplo \"se oferta...\" "
    "\"se instalarán...\" \"se proveerá...\" y que cuente con cada uno de todos "
    "los puntos que piden."
)

# Documentos por defecto (los que están en el repositorio).
DOCS_POR_DEFECTO = [
    "Bases_2378-57-L126.pdf",
    "decreto_exento_3892_O_243_obligacion_prs.pdf",
    "decreto_exento_3892_Torniquetes.pdf",
]


# --------------------------------------------------------------------------- #
# Flujo principal contra NotebookLM
# --------------------------------------------------------------------------- #

async def procesar(documentos, nombre_notebook):
    """Sube los documentos, manda los dos mensajes y devuelve la propuesta final."""
    async with NotebookLMClient.from_storage() as client:
        # 1. Crear el notebook
        print(f"→ Creando notebook: {nombre_notebook!r}")
        nb = await client.notebooks.create(nombre_notebook)
        print(f"  notebook id: {nb.id}")

        # 2. Subir cada documento y esperar a que NotebookLM lo procese
        for ruta in documentos:
            ruta = Path(ruta)
            if not ruta.exists():
                raise FileNotFoundError(f"No se encontró el documento: {ruta}")
            print(f"→ Subiendo documento: {ruta.name}")
            source = await client.sources.add_file(nb.id, ruta)
            await client.sources.wait_until_ready(nb.id, source.id)
            print(f"  listo: {ruta.name}")

        # 3. Primer mensaje: lista de ítems requeridos
        print("→ Enviando primer mensaje (lista de ítems de la licitación)...")
        r1 = await _ask_con_reintentos(client, nb.id, MENSAJE_1)
        print("  respuesta 1 recibida.")

        # 4. Segundo mensaje: redactar la propuesta del oferente.
        #    El chat de NotebookLM mantiene el contexto de la conversación dentro
        #    del mismo notebook, así que basta con mandar el mensaje tal cual
        #    ("el output que acabas de darme"). NO reenviamos la respuesta
        #    anterior: hacerlo genera un prompt enorme que NotebookLM responde
        #    vacío (ChatResponseParseError).
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
        "--salida",
        default="propuesta_oferente.docx",
        help="Ruta del .docx de salida (por defecto: propuesta_oferente.docx).",
    )
    parser.add_argument(
        "--notebook",
        default="Licitación - Propuesta oferente",
        help="Nombre del notebook a crear en NotebookLM.",
    )
    args = parser.parse_args()

    lista_items, propuesta = asyncio.run(
        procesar(args.documentos, args.notebook)
    )

    # Guardamos la propuesta final (output del segundo mensaje) en .docx
    guardar_docx("Propuesta Técnica del Oferente", propuesta, args.salida)

    # Guardamos también la lista de ítems por si es útil de referencia.
    ruta_items = Path(args.salida).with_name("lista_items_licitacion.docx")
    guardar_docx("Ítems Requeridos por la Licitación", lista_items, str(ruta_items))


if __name__ == "__main__":
    main()
