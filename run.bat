@echo off
chcp 65001 >nul
echo ======================================
echo   Spot On! — Iniciando backend...
echo ======================================

cd /d "%~dp0backend"

REM Copy .env.example to .env if no .env exists
if not exist ".env" (
  if exist ".env.example" (
    copy ".env.example" ".env" >nul
    echo [INFO] Arquivo .env criado a partir de .env.example
    echo        Edite backend\.env e adicione sua FOOTBALL_DATA_API_KEY
    echo        (sem chave, dados de demonstracao serao usados)
    echo.
  )
)

REM Create virtualenv if it doesn't exist
if not exist ".venv" (
  echo [*] Criando ambiente virtual...
  python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [*] Instalando dependencias...
pip install -r requirements.txt -q

echo.
echo [OK] Servidor rodando em http://127.0.0.1:8000
echo      Abra frontend\index.html no navegador
echo.

uvicorn main:app --reload --port 8000

pause
