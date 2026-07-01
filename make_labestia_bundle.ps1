$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundle = Join-Path $repo 'labestia_bundle'

if (Test-Path $bundle) {
    Remove-Item -LiteralPath $bundle -Recurse -Force
}

New-Item -ItemType Directory -Path $bundle | Out-Null
New-Item -ItemType Directory -Path (Join-Path $bundle 'Frontend') | Out-Null

$rootFiles = @(
    'server.py',
    'licitacion_a_propuesta.py',
    'requirements.txt',
    'README.md',
    'start.bat',
    '.gitignore',
    'lista_items_licitacion.docx',
    'propuesta_oferente.docx'
)

foreach ($file in $rootFiles) {
    Copy-Item -LiteralPath (Join-Path $repo $file) -Destination (Join-Path $bundle $file) -Force
}

Copy-Item -LiteralPath (Join-Path $repo 'scripts') -Destination (Join-Path $bundle 'scripts') -Recurse -Force

$frontendFiles = @(
    '.gitignore',
    'ATTRIBUTIONS.md',
    'default_shadcn_theme.css',
    'index.html',
    'package.json',
    'pnpm-lock.yaml',
    'pnpm-workspace.yaml',
    'postcss.config.mjs',
    'README.md',
    'vite.config.ts'
)

foreach ($file in $frontendFiles) {
    Copy-Item -LiteralPath (Join-Path $repo "Frontend\$file") -Destination (Join-Path $bundle "Frontend\$file") -Force
}

Copy-Item -LiteralPath (Join-Path $repo 'Frontend\src') -Destination (Join-Path $bundle 'Frontend\src') -Recurse -Force

$setup = @'
# Local deploy

1. Move this folder to `~/Desktop/03 AHD` on the target Ubuntu machine.

2. Install Node.js on that machine:

   sudo apt update
   sudo apt install -y nodejs npm

3. Create the Python virtualenv and install backend deps:

   cd ~/Desktop/03\ AHD
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

4. Install frontend deps:

   cd Frontend
   npm install
   cd ..

5. Start or point to a local OpenAI-compatible LLM server.

   Example environment:

   export LOCAL_LLM_BASE_URL="http://127.0.0.1:11434/v1"
   export LOCAL_LLM_API_KEY="local"
   export LOCAL_LLM_MODEL="gemma-4-31b"

6. Start the backend:

   source .venv/bin/activate
   uvicorn server:app --host 0.0.0.0 --port 8000

7. Start the frontend in another terminal:

   cd ~/Desktop/03\ AHD/Frontend
   npm run dev -- --host 0.0.0.0

8. Optional: run Open WebUI against the same local LLM server.

Notes:
- This bundle intentionally excludes `.venv`, `node_modules`, `Output/`, and
  other generated artifacts.
- The backend now works without external auth or cloud flow.
'@

Set-Content -LiteralPath (Join-Path $bundle 'SETUP_LABESTIA.txt') -Value $setup -Encoding UTF8

Write-Host "Created bundle at: $bundle"
