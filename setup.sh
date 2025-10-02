#!/bin/bash
# Script d'installation automatique pour A-IR-OB1
# Ce script configure automatiquement l'environnement Python et installe toutes les dépendances

echo "============================================"
echo "  A-IR-OB1 - AI Agent Orchestrator Setup"
echo "============================================"
echo

# Vérification de Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERREUR] Python n'est pas installé ou non accessible"
    echo "Veuillez installer Python 3.8+ depuis https://python.org"
    exit 1
fi

# Utiliser python3 si disponible, sinon python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "[OK] Python détecté"
$PYTHON_CMD --version

# Création de l'environnement virtuel
echo
echo "[ÉTAPE 1/4] Création de l'environnement virtuel..."
if [ -d ".venv" ]; then
    echo "Environnement virtuel existant détecté, suppression..."
    rm -rf .venv
fi

$PYTHON_CMD -m venv .venv
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec de création de l'environnement virtuel"
    exit 1
fi
echo "[OK] Environnement virtuel créé"

# Activation de l'environnement virtuel
echo
echo "[ÉTAPE 2/4] Activation de l'environnement virtuel..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec d'activation de l'environnement virtuel"
    exit 1
fi
echo "[OK] Environnement virtuel activé"

# Mise à jour de pip
echo
echo "[ÉTAPE 3/4] Mise à jour de pip..."
python -m pip install --upgrade pip
echo "[OK] pip mis à jour"

# Installation des dépendances
echo
echo "[ÉTAPE 4/4] Installation des dépendances..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec d'installation des dépendances"
    exit 1
fi
echo "[OK] Dépendances installées"

# Configuration optionnelle des clés API
echo
echo "============================================"
echo "        Configuration (Optionnel)"
echo "============================================"
echo
echo "Pour utiliser OpenAI, vous pouvez définir votre clé API :"
echo "1. Créer un fichier .env dans ce dossier"
echo "2. Ajouter : OPENAI_API_KEY=votre_clé_ici"
echo
echo "Ou utiliser la variable d'environnement :"
echo "export OPENAI_API_KEY=votre_clé_ici"
echo

# Succès
echo "============================================"
echo "            Installation Terminée !"
echo "============================================"
echo
echo "L'application est prête à être utilisée."
echo
echo "Pour démarrer l'application :"
echo "  1. ./run.sh"
echo "  ou"
echo "  2. source .venv/bin/activate && python main.py"
echo
echo "Documentation disponible après démarrage :"
echo "  http://localhost:8000/docs"
echo