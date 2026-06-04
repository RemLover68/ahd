# Licitación → Propuesta (NotebookLM)

Script simple que automatiza NotebookLM (usando la librería **notebooklm-py** de
Teng Lin) para procesar los documentos de una licitación y generar una propuesta
del oferente en formato `.docx`.

## ¿Qué hace?

1. Crea un notebook en NotebookLM.
2. Sube los documentos (PDFs) de la licitación.
3. Manda el primer mensaje pidiendo **la lista completa de ítems / requisitos**.
4. Espera la respuesta.
5. Manda el segundo mensaje pidiendo **redactar la propuesta del oferente**
   ("se oferta...", "se instalarán...", "se proveerá...").
6. Guarda el resultado final como un `.docx` con formato bonito
   (`propuesta_oferente.docx`) y también la lista de ítems
   (`lista_items_licitacion.docx`).

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
notebooklm login        # inicia sesión con Google (una sola vez)
```

## Uso

Con los PDFs que ya están en el repositorio:

```bash
python licitacion_a_propuesta.py
```

Con tus propios documentos y nombre de salida:

```bash
python licitacion_a_propuesta.py bases.pdf anexo.pdf --salida mi_propuesta.docx
```

Opciones:

| Opción       | Descripción                                  | Por defecto                       |
|--------------|----------------------------------------------|-----------------------------------|
| `documentos` | Archivos a subir                             | Los 3 PDFs de la licitación       |
| `--salida`   | Ruta del `.docx` de salida                   | `propuesta_oferente.docx`         |
| `--notebook` | Nombre del notebook en NotebookLM            | `Licitación - Propuesta oferente` |

## Nota

`notebooklm-py` es una librería **no oficial** que usa APIs internas de Google,
así que puede dejar de funcionar si Google cambia algo de su lado.
