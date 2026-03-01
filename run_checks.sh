#!/usr/bin/env bash
set -e

echo "==> Installing tools..."
pip install --quiet black flake8 isort pytest bandit pip-audit

echo "==> Import consistency checks..."
cd app/backend && python -c "from app import app"
cd ..
python -c "from cli.main import main"
python -c "from telegram.bot import main"
cd ..

echo "==> Black..."
black --check ./app

echo "==> Flake8..."
flake8 --ignore=E203,E501,W291,W293,W391,F541,E402,W503,F401 ./app

echo "==> Pytest..."
pytest --maxfail=1 --disable-warnings -v

echo "==> Bandit..."
bandit -r ./app -ll -ii

echo "==> Pip-audit..."
pip-audit

echo ""
echo "All checks passed."