# Decisions

- Active deployment target for this project is `labestia_bundle/`, not the root tree.
- Future work for the deployment should be applied in the `labestia_bundle/` copy.
- The local root tree can be used for reference, but the operational environment is the SSH host copy.
## 2026-06-24 | labestia SSH status
- SSH access to `desanto@labestia` works without needing the provided password in this session.
- Runtime folder on labestia is `/home/desanto/Desktop/03 AHD`.
- Remote handoff says target is Open WebUI on `http://labestia:5173` with a local model via Ollama + Docker Compose.
- Current remote state: Docker and Docker Compose are not installed/in PATH, `.env` is missing, and no Docker containers are running.
- Port `5173` is currently occupied by the legacy Vite frontend: `node /home/desanto/Desktop/03 AHD/Frontend/node_modules/.bin/vite --host 0.0.0.0`.
- Next implementation step is to install Docker/Compose on labestia, stop or move the legacy Vite process, create `.env`, then run `bash scripts/start_openwebui.sh` to start Ollama/Open WebUI and pull the configured model.
## 2026-06-24 | labestia Open WebUI completed
- User explicitly authorized sudo password use for labestia. Installed `docker.io`, `docker-compose-v2`, `curl`, and `openssl`; enabled Docker; added `desanto` to the `docker` group.
- Stopped the legacy Vite frontend that was using port `5173`.
- Created `/home/desanto/Desktop/03 AHD/.env` with `OPEN_WEBUI_PORT=5173`, `OLLAMA_MODEL=gemma4:31b`, and a generated `WEBUI_SECRET_KEY`.
- Started Docker Compose stack in `/home/desanto/Desktop/03 AHD`: `03ahd-ollama-1` and `03ahd-open-webui-1` are healthy.
- Downloaded Ollama model `gemma4:31b` (`6316f0629137`, about 19 GB, Q4_K_M). Ollama API on `11434` lists the model.
- Open WebUI responds HTTP 200 on `http://127.0.0.1:5173` from labestia, exposed as `http://labestia:5173`.
- Fixed remote `scripts/start_openwebui.sh` model-existence check to avoid the `set -u`/`awk $1` failure; validated idempotent startup.
- Updated remote `SETUP_LABESTIA.txt` to install `docker-compose-v2` instead of unavailable `docker-compose-plugin`.
- Copied `/home/desanto/Desktop/Nunoa_Seguridad_SONDA.pptx` from labestia to local workspace as `C:\Users\DeSanto\Desktop\21 Sonda\03 AHD\Nunoa_Seguridad_SONDA.pptx`.
## 2026-06-25 | labestia qwen GPU setup
- Installed NVIDIA Container Toolkit on labestia and configured Docker NVIDIA runtime.
- Updated remote `/home/desanto/Desktop/03 AHD/docker-compose.yml` for Ollama with `gpus: all`, `NVIDIA_VISIBLE_DEVICES=all`, and compute/utility driver capabilities.
- Downloaded `qwen3:14b` in Ollama and set remote `.env` `OLLAMA_MODEL=qwen3:14b`.
- Loaded `qwen3:14b` successfully on GPU. `nvidia-smi` showed `/usr/lib/ollama/llama-server` using about 9.3 GiB VRAM.
- Warm test after load reported about 30 tokens/s; initial load took about 15 seconds.
- `gemma4:31b` remains installed for quality tests but is much slower and heavier.
## 2026-06-23T12:01 | 03 AHD
- Turn: 019ef5bd-a8ce-7c60-b14c-508622de0d90
- Context: a q te refieres con restaurar notebooklm pensé q ese ya estaba en ese compu y q por lo tanto deberías implementar el stack local y open webui pero por lo q me dices entiendo q ya lo habías hecho?
- Conclusion: `Restaurar NotebookLM` = volver a dejar la copia operativa usando el flujo viejo de NotebookLM, no el stack local. Estado real ahora: - El **Ã¡rbol raÃ­z** de `C:\Users\DeSanto\Desktop\21 Sonda\03 AHD\` ya quedÃ³ convertido a **stack local**. - La carpeta **operativa/deployment** que me pediste usar, `labestia_bundle/`, **todavÃ­a sigue con NotebookLM**. - No he dejado todavÃ­a el **stack local + Open WebUI** funcionando dentro de `labestia_bundle/`. - Tampoco descarguÃ© ni levantÃ© un modelo LLM en esta mÃ¡quina. Entonces, para evitar confusiÃ³n: - **No**, todavÃ­a no implementÃ© el stack local en la carpeta de deployment. - **SÃ­**, ya hice esa migraciÃ³n en el Ã¡rbol raÃ­z, pero ese ya...

## 2026-06-23T12:36 | 03 AHD
- Turn: 019ef5bd-a8d1-7c60-b14c-5129ebaa76ae
- Context: por qué es´tas trabajando en el bundle y no en ssh la carpeta que dijmos de desktop?
- Conclusion: Porque aquÃ­ **no tengo acceso directo a la carpeta SSH de Ubuntu**. Lo que sÃ­ tengo en esta sesiÃ³n es: - el workspace local de Windows: `C:\Users\DeSanto\Desktop\21 Sonda\03 AHD` - su copia de despliegue: `labestia_bundle/` Entonces trabajÃ© en `labestia_bundle/` porque: - es la Ãºnica copia que puedo modificar desde este entorno - la habÃ­as seÃ±alado como artefacto de deployment - sirve para preparar lo que luego se sincroniza a `~/Desktop/03 AHD` en `labestia` Lo que **no** he hecho: - no he editado directamente la carpeta real de Ubuntu por SSH - no he tocado el stack local de esta PC salvo lo que ya venÃ­amos haciendo antes Si quieres que el cambio vaya **exactamente** a `~/Deskto...

## 2026-06-23T12:45 | 03 AHD
- Turn: 019ef5bd-a8d1-7c60-b14c-5139762f8252
- Context: no, dame un txt que tenga el contexto de este chat y lo que se va a implementar, instalé codex co nesta misma cuenta en ese compu en esa carpeta para q trabajes directamente allá o si hay una mejor manera mejor aun
- Conclusion: DejÃ© el handoff en: - [labestia_bundle/CODEX_CONTEXT.txt](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/labestia_bundle/CODEX_CONTEXT.txt) Contiene: - el objetivo operativo - quÃ© carpeta es la fuente de verdad - que el despliegue debe ser Open WebUI + modelo local - que `http://labestia:5173` debe mostrar Open WebUI - que la raÃ­z Windows no se debe tocar - la ruta correcta del runtime en Ubuntu (`~/Desktop/03 AHD`) - el plan de implementaciÃ³n y arranque La mejor forma prÃ¡ctica, si quieres que el siguiente Codex no se vuelva a confundir, es esta combinaciÃ³n: 1. `AGENTS.md` con las reglas de trabajo. 2. `CODEX_CONTEXT.txt` como handoff operativo. 3. `memory/decisions.md` o `memory/comp...

## 2026-06-23T12:50 | 03 AHD
- Turn: 019ef5bd-a8d1-7c60-b14c-515106a699ad
- Context: si crea una carpeta con los 3 archivos: memory/decisions, agents y el context
- Conclusion: CreÃ© la carpeta de handoff en: - [labestia_bundle/codex_handoff/AGENTS.md](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/labestia_bundle/codex_handoff/AGENTS.md) - [labestia_bundle/codex_handoff/CODEX_CONTEXT.txt](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/labestia_bundle/codex_handoff/CODEX_CONTEXT.txt) - [labestia_bundle/codex_handoff/memory/decisions.md](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/labestia_bundle/codex_handoff/memory/decisions.md) QuedÃ³ listo para que el prÃ³ximo Codex en esa carpeta tenga: - reglas de trabajo - contexto operativo - decisiÃ³n persistente Si quieres, el siguiente paso es que te deje tambiÃ©n un `README.md` corto dentro de esa carpeta explicando cÃ³m...

## 2026-06-24T16:55 | 03 AHD
- Turn: 019efb65-6bea-7a93-9b07-32f7b85c0008
- Context: quiero que te conectes a labestia por ssh desanto@labestia y la pass es [REDACTED] si tienes problemas avisame ya hago el logi nweb primero. para ver en qué quedamos del proyecto de implementación de un modelo local para el ahd que está ahí
- Conclusion: Me conectÃ© por SSH a `desanto@labestia` correctamente. No necesitÃ© usar la contraseÃ±a. Estado real del proyecto en `labestia`: - Carpeta operativa: `/home/desanto/Desktop/03 AHD` - El handoff remoto confirma que el objetivo era: - Open WebUI como interfaz principal - modelo local vÃ­a Ollama - acceso en `http://labestia:5173` - Docker Compose como runtime - Pero el stack no estÃ¡ corriendo todavÃ­a: - Docker no estÃ¡ instalado o no estÃ¡ en `PATH` - Docker Compose tampoco - no existe `.env` - no hay contenedores Docker activos - El puerto `5173` estÃ¡ ocupado por el frontend viejo: - `node /home/desanto/Desktop/03 AHD/Frontend/node_modules/.bin/vite --host 0.0.0.0` - o sea, actualmente...

## 2026-06-24T17:15 | 03 AHD
- Turn: 019efb78-f579-7ed2-8d0d-d21bb8c2399b
- Context: y ahora si ejecuta los sisguientes pasos que me dijiste
- Conclusion: CopiÃ© el PPT desde `labestia` a este equipo: [Nunoa_Seguridad_SONDA.pptx](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/Nunoa_Seguridad_SONDA.pptx) TambiÃ©n avancÃ© con el stack de Open WebUI: - CreÃ© `/home/desanto/Desktop/03 AHD/.env` en `labestia`. - ConfirmÃ© que `scripts/start_openwebui.sh` falla solo porque Docker no estÃ¡ instalado: ```text Docker is required but not installed or not in PATH. ``` - No liberÃ© todavÃ­a el puerto `5173`, porque ahÃ­ sigue corriendo el frontend viejo de Vite y, sin Docker instalado, dejarÃ­amos el puerto sin reemplazo. Bloqueo actual: `sudo` en `labestia` pide contraseÃ±a. Para seguir tengo dos opciones: 1. Me autorizas explÃ­citamente a usar la contr...

## 2026-06-24T18:57 | 03 AHD
- Turn: 019efbd8-d587-7b00-8872-67cbe0a4d83c
- Context: si usa la contraseña
- Conclusion: La ejecuciÃ³n fue bloqueada por seguridad porque el comando hace cambios persistentes en `labestia`, especialmente instalar Docker y agregar `desanto` al grupo `docker`, que equivale a dar permisos elevados permanentes sobre Docker. Para poder seguir, necesito tu aprobaciÃ³n explÃ­cita para esto: ```bash sudo apt update sudo apt install -y docker.io docker-compose-plugin curl openssl sudo systemctl enable --now docker sudo usermod -aG docker desanto ``` TambiÃ©n necesito que confirmes que autorizas que use la contraseÃ±a sudo en el comando remoto para hacer esa instalaciÃ³n.

## 2026-06-24T21:28 | 03 AHD
- Turn: 019efc0c-00b5-7962-9c8e-99df97d67bea
- Context: autorizo y uso la contrasñeña q es [REDACTED]
- Conclusion: Listo. CopiÃ© el PPT a este equipo en: [Nunoa_Seguridad_SONDA.pptx](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/Nunoa_Seguridad_SONDA.pptx) Y dejÃ© funcionando el stack en `labestia`: - Instalado Docker + Compose v2. - Parado el frontend viejo de Vite que ocupaba `5173`. - Open WebUI corriendo en `http://labestia:5173`. - Ollama corriendo en `11434`. - Modelo instalado: `gemma4:31b`, 19 GB, `Q4_K_M`. - Contenedores healthy: - `03ahd-ollama-1` - `03ahd-open-webui-1` TambiÃ©n corregÃ­ el script remoto `scripts/start_openwebui.sh`, porque fallaba por un escape de `$1` en `awk`, y actualicÃ© `SETUP_LABESTIA.txt` para usar `docker-compose-v2`, que es el paquete correcto en esa Ubuntu. GuardÃ©...

## 2026-06-25T20:46 | 03 AHD
- Turn: 019f0163-ab97-7880-9ff6-eca41b3bc4c7
- Context: el openweb ui pide login, qué esl oq hace y paq era necesario para nuestro proyecto ahd? y estan activos el gemma y el q4? o los modelos no se activan? o como funciona eso? pq un contenedor de docker con un flujo por ejemplo q continuame...
- Conclusion: Open WebUI pide login porque crea su propia cuenta local de administrador la primera vez. No es login de Google ni cloud: es para proteger la interfaz web, historial, usuarios, archivos y configuraciones dentro de la instancia local. La primera cuenta que crees normalmente queda como admin. Para el proyecto AHD era necesario como **interfaz local usable** encima del modelo. Es decir: - **Ollama** corre el modelo local. - **Gemma 4 31B Q4_K_M** es el modelo instalado. - **Open WebUI** es la pantalla tipo ChatGPT para conversar con ese modelo, subir documentos, probar prompts y validar calidad. - El backend/pipeline AHD despuÃ©s puede apuntar al endpoint compatible de Ollama/OpenAI-style se...

## 2026-06-25T21:17 | 03 AHD
- Turn: 019f0180-2cb6-7d01-b8b4-057b6a613aa0
- Context: y pq se carga en vram y no en ram, de ram tengo 64 (en adelante da respuestas mas cortas, anotalo en tu agents.md del proyecto. conciso y preciso.
- Conclusion: Anotado en [AGENTS.md](C:/Users/DeSanto/Desktop/21%20Sonda/03%20AHD/AGENTS.md). Sobre RAM vs VRAM: - El modelo **sÃ­ puede cargarse en RAM**. Eso es lo que estÃ¡ pasando ahora. - Pero generar en RAM usa **CPU**, y por eso va lento. - La **VRAM** es la memoria de la GPU. Si el modelo o parte del modelo entra ahÃ­, la GPU calcula mucho mÃ¡s rÃ¡pido. - Tienes 64 GB RAM, suficiente para cargar `gemma4:31b Q4`. - Pero tienes 16 GB VRAM, menos que los ~19 GB del modelo, asÃ­ que no cabe completo en GPU. - Aun asÃ­ se puede hacer **offload parcial**: parte en VRAM, parte en RAM. Eso suele acelerar. Ahora estÃ¡ lento porque Docker/Ollama no ve la GPU, entonces usa solo CPU+RAM.

## 2026-06-25T21:19 | 03 AHD
- Turn: 019f0182-7817-71e3-8a62-787673f2f2ae
- Context: que es mejor offload parcial o un modelo completo en vram? y btw entonces tener 64 de ram no sirve de mucho comparado con la vram? yo le puse mas ram pq los de intel geti decian q se necesitaban 64 gb de ram
- Conclusion: Mejor: **modelo completo en VRAM**. Orden tÃ­pico de velocidad: 1. **Todo en VRAM:** mejor. 2. **Offload parcial GPU+RAM:** intermedio. 3. **Todo en RAM/CPU:** lento. La RAM sÃ­ sirve, pero para otra cosa: - Permite cargar modelos grandes que no caben en VRAM. - Evita que el sistema use swap/disco, que serÃ­a mucho peor. - Permite contexto largo, embeddings, documentos, Open WebUI, backend, etc. - Para AHD/RAG sirve bastante porque habrÃ¡ documentos, chunks, Ã­ndices y procesos paralelos. Pero para **velocidad de inferencia**, manda mucho mÃ¡s la VRAM/ancho de banda GPU. Con 64 GB RAM puedes correr `31B Q4` en CPU. Sin esos 64 GB quizÃ¡s ni cargarÃ­a bien. Pero no significa que serÃ¡ rÃ¡p...

## 2026-06-25T22:53 | 03 AHD
- Turn: 019f01d8-710e-76b3-8675-642424c9c5f8
- Context: quedó listo o te falta algunos pasos
- Conclusion: QuedÃ³ listo. Estado final: - Open WebUI activo: `http://labestia:5173` - Ollama activo. - GPU habilitada en Docker. - `qwen3:14b` descargado y cargado en VRAM. - `qwen3:14b` configurado como modelo por defecto en `.env`. - `gemma4:31b` sigue instalado como modelo grande alternativo. - Velocidad validada de Qwen: ~30 tokens/s. - README remoto y memoria local actualizados. Lo Ãºnico pendiente opcional: borrar `gemma4:31b` si quieres liberar ~19 GB de disco. No lo borrÃ© porque puede servir para comparar calidad.

## 2026-06-25T23:48 | 03 AHD
- Turn: 019f0208-8c7f-7bb3-a9af-2d7f759e2272
- Context: ok si está bueno pero no es lo q quiero para este proyecto, pra este proyecto si usaremos ese modelo pero con otra lógica osea en otrofrontend: implementa la lógica del ahd pero reemplaza noztebooklm por el modelo local e implementale un...
- Conclusion: SÃ­. Para AHD no quiero usar Open WebUI como frontend. Queda como laboratorio/chat. El producto AHD debe usar **nuestro frontend** y backend propio. **InvestigaciÃ³n Inicial** RevisÃ© herramientas de RAG/OCR/citas/local LLM. Las mÃ¡s relevantes: - **RAGFlow**: trae OCR/parsing, RAG, citas, Docker, UI. Muy completo, pero demasiado grande para encajarlo limpio como backend AHD. Bueno como referencia. Fuente: GitHub RAGFlow indica OCR/document understanding, citas trazables y mÃºltiples formatos. - **PrivateGPT**: API local para documentos, Ollama/OpenAI-compatible, UI demo, retrieval con citas. MÃ¡s cercano a importar lÃ³gica/API. - **Kotaemon**: RAG documental con modelos locales, Docling/...

## 2026-06-26 | AHD own frontend + local RAG/OCR
- Decision: do not replace AHD with RAGFlow/PrivateGPT/Open WebUI. Keep AHD's own FastAPI + React frontend and import the useful ideas/pieces.
- Implemented in `licitacion_a_propuesta.py`: default local model `qwen3:14b`, optional Docling OCR/parser first, fallback to `pypdf`/`markitdown`, hybrid dense+lexical retrieval, and visible citation enforcement when the model omits `[n]`.
- Updated `requirements.txt` with `docling` and README with OCR/RAG/model setup.
- Synced modified backend files to labestia `/home/desanto/Desktop/03 AHD`.
- Remote `.venv` now has `docling`, `openai`, `sentence_transformers`, and `markitdown`; remote syntax/import checks passed.
- Remote AHD backend is running on port `8000` and `/api/health` returns `{"ok":true}`. Open WebUI remains separate on port `5173`.

## 2026-06-26T00:33 | 03 AHD
- Turn: 019f020f-536e-7ca3-bbdf-8a64da6340d1
- Context: dale continúa
- Conclusion: Listo. ImplementÃ© el flujo AHD propio con modelo local, no Open WebUI como producto. Cambios principales: - Backend AHD usa `qwen3:14b` por defecto. - AgreguÃ© OCR/parseo con `Docling`, con fallback a `pypdf`/`markitdown`. - MejorÃ© RAG con bÃºsqueda hÃ­brida: embeddings + coincidencia lÃ©xica. - ForcÃ© citas visibles `[n]` cuando el modelo responde sin marcarlas. - ActualicÃ© `requirements.txt`, `README.md`, `AGENTS.md` y memoria. - DejÃ© matriz de 50 fuentes en `memory/research_rag_ocr_tools.md`. Estado en labestia: - Backend AHD: `http://labestia:8000`, health OK. - Frontend AHD propio: `http://labestia:5174`. - Open WebUI sigue separado: `http://labestia:5173`. - Dependencias remotas...

