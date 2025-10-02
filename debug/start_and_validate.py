"""
Script de validation manuelle du Jalon 1.3.

Ce script démarre le serveur et affiche les URLs à tester.
"""

import sys
import os

# Ajouter le répertoire courant au PYTHONPATH
sys.path.insert(0, os.getcwd())

import uvicorn

if __name__ == "__main__":
    print("🚀 Démarrage du serveur FastAPI pour validation du Jalon 1.3")
    print("=" * 60)
    print("\n📍 URLs à tester :")
    print("   Health Check: http://127.0.0.1:8000/api/health")
    print("   Endpoint racine: http://127.0.0.1:8000/api/")
    print("   Documentation: http://127.0.0.1:8000/docs")
    print("   Redoc: http://127.0.0.1:8000/redoc")
    print("\n🎯 Réponse attendue pour /api/health :")
    print('   {"status": "ok", "service": "orchestrator"}')
    print("\n⏹️  Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 60)
    
    # Démarrage du serveur
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )