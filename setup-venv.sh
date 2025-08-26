#!/bin/bash
# Script per setup Virtual Environment DevStack Health Monitor

echo "🐍 Setup Virtual Environment per DevStack Health Monitor"
echo "======================================================="

# Vai alla directory del progetto
cd /opt/stack/devstack-health-monitor/backend

# 1. Installa python3-venv se non presente
echo "📦 Installazione python3-venv..."
sudo apt update
sudo apt install -y python3-venv python3-full

# 2. Crea virtual environment
echo "🏗️ Creazione virtual environment..."
python3 -m venv venv

# 3. Attiva virtual environment
echo "⚡ Attivazione virtual environment..."
source venv/bin/activate

# 4. Aggiorna pip
echo "🔄 Aggiornamento pip..."
pip install --upgrade pip

# 5. Installa requirements
echo "📋 Installazione requirements..."
pip install -r requirements.txt

echo ""
echo "✅ Setup completato!"
echo ""
echo "🚀 Per attivare il virtual environment in futuro:"
echo "   cd /opt/stack/devstack-health-monitor/backend"
echo "   source venv/bin/activate"
echo ""
echo "🎯 Per avviare l'applicazione:"
echo "   python main.py"