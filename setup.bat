@echo off
:: Script d'installation automatique pour A-IR-OB1
:: Ce script configure automatiquement l'environnement Python et installe toutes les dépendances

echo ============================================
echo  A-IR-OB1 - AI Agent Orchestrator Setup
echo ============================================
echo.

:: Vérification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou non accessible
    echo Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

echo [OK] Python détecté
python --version

:: Création de l'environnement virtuel
echo.
echo [ÉTAPE 1/4] Création de l'environnement virtuel...
if exist .venv (
    echo Environnement virtuel existant détecté, suppression...
    rmdir /s /q .venv
)

python -m venv .venv
if errorlevel 1 (
    echo [ERREUR] Échec de création de l'environnement virtuel
    pause
    exit /b 1
)
echo [OK] Environnement virtuel créé

:: Activation de l'environnement virtuel
echo.
echo [ÉTAPE 2/4] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERREUR] Échec d'activation de l'environnement virtuel
    pause
    exit /b 1
)
echo [OK] Environnement virtuel activé

:: Mise à jour de pip
echo.
echo [ÉTAPE 3/4] Mise à jour de pip...
python -m pip install --upgrade pip
echo [OK] pip mis à jour

:: Installation des dépendances
echo.
echo [ÉTAPE 4/4] Installation des dépendances...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERREUR] Échec d'installation des dépendances
    pause
    exit /b 1
)
echo [OK] Dépendances installées

:: Configuration optionnelle des clés API
echo.
echo ============================================
echo        Configuration (Optionnel)
echo ============================================
echo.
echo Pour utiliser OpenAI, vous pouvez définir votre clé API :
echo 1. Créer un fichier .env dans ce dossier
echo 2. Ajouter : OPENAI_API_KEY=votre_clé_ici
echo.
echo Ou utiliser la variable d'environnement :
echo set OPENAI_API_KEY=votre_clé_ici
echo.

:: Succès
echo ============================================
echo            Installation Terminée !
echo ============================================
echo.
echo L'application est prête à être utilisée.
echo.
echo Pour démarrer l'application :
echo   1. run.bat
echo   ou
echo   2. .venv\Scripts\activate && python main.py
echo.
echo Documentation disponible après démarrage :
echo   http://localhost:8000/docs
echo.
pause