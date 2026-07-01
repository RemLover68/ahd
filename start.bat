@echo off
cd /d "%~dp0"

if not exist "Frontend\node_modules" (
    echo Instalando dependencias del Frontend por primera vez...
    pushd Frontend
    call pnpm install
    popd
)

echo Iniciando Frontend (nueva ventana)...
start "AHD Frontend" cmd /k "cd /d "%~dp0Frontend" && pnpm dev"

echo Iniciando Backend (log aqui abajo)...
echo.
uvicorn server:app --reload --port 8000
