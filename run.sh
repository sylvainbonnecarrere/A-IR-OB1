#!/bin/bash
# Script de démarrage pour A-IR-OB1
echo "============================================"
echo "   A-IR-OB1 - AI Agent Orchestrator"
echo "============================================"
echo

# Vérification de l'environnement virtuel
if [ ! -d ".venv" ]; then
    echo "[ERREUR] Environnement virtuel non trouvé"
    echo "Veuillez exécuter ./setup.sh d'abord"
    exit 1
fi

# Activation de l'environnement virtuel
echo "[INFO] Activation de l'environnement virtuel..."
source .venv/bin/activate

# Démarrage de l'application
echo "[INFO] Démarrage de l'application..."
echo
echo "Serveur disponible sur : http://localhost:8000"
echo "Documentation API : http://localhost:8000/docs"
echo
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo

python main.py