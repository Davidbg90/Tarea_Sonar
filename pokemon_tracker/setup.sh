#!/bin/bash
# Pokemon Card Price Tracker — setup script for Raspberry Pi OS
set -e

echo "==================================================="
echo "  Pokemon Card Price Tracker — Instalacion"
echo "==================================================="

# Python 3
if ! command -v python3 &>/dev/null; then
    echo "Instalando Python 3..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip
fi

# Tkinter (puede no estar incluido en versiones mínimas de Pi OS)
python3 -c "import tkinter" 2>/dev/null || {
    echo "Instalando python3-tk..."
    sudo apt-get install -y python3-tk
}

# Dependencias Python
echo "Instalando paquetes Python..."
pip3 install --break-system-packages -r requirements.txt 2>/dev/null \
    || pip3 install -r requirements.txt

# Crear .env si no existe
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  IMPORTANTE: Edita .env con tus credenciales de CardMarket:"
    echo "    nano .env"
    echo ""
    echo "  Puedes obtener las credenciales en:"
    echo "    https://www.cardmarket.com/en/Pokemon/Account/API"
    echo ""
fi

# Inicializar base de datos
python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from database import init_db
init_db()
print('Base de datos inicializada.')
"

echo ""
echo "Instalacion completada."
echo ""
echo "Para iniciar la aplicacion:"
echo "  python3 main.py"
echo ""
echo "Interfaz web disponible en: http://<IP-de-la-Pi>:5000"
