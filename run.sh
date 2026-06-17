#!/bin/bash

set -e

echo "======================================"
echo "  Spot On! — Iniciando backend..."
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"

# Copy .env.example to .env if no .env exists
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "ℹ️  Arquivo .env criado a partir de .env.example"
  echo "   Edite backend/.env e adicione sua FOOTBALL_DATA_API_KEY"
  echo "   (sem chave, dados de demonstração serão usados)"
  echo ""
fi

# Create virtualenv if it doesn't exist
if [ ! -d .venv ]; then
  echo "🐍 Criando ambiente virtual..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Instalando dependências..."
pip install -r requirements.txt -q

echo ""
echo "🚀 Servidor rodando em http://127.0.0.1:8000"
echo "   Abra frontend/index.html no navegador"
echo ""
uvicorn main:app --reload --port 8000
