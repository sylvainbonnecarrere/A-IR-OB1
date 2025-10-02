"""
Point d'entrée principal de l'application FastAPI d'orchestration d'agents IA.

Ce fichier configure et démarre l'application FastAPI avec uvicorn.
Il inclut la configuration CORS et intègre le routeur principal.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire courant au PYTHONPATH
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.api.router import router


class UTF8EnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour forcer l'encodage UTF-8 sur toutes les requêtes et réponses
    
    Sécurité:
        - Force charset=utf-8 dans Content-Type
        - Assure la cohérence d'encodage
        - Protège contre les problèmes d'encoding
    """
    
    async def dispatch(self, request: Request, call_next):
        # Traitement de la requête
        response = await call_next(request)
        
        # Force UTF-8 dans les headers de réponse
        if response.headers.get("content-type"):
            content_type = response.headers["content-type"]
            if "charset" not in content_type and "application/json" in content_type:
                response.headers["content-type"] = f"{content_type}; charset=utf-8"
            elif "text/" in content_type and "charset" not in content_type:
                response.headers["content-type"] = f"{content_type}; charset=utf-8"
        
        # Headers de sécurité supplémentaires
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


def create_app() -> FastAPI:
    """
    Créé et configure l'application FastAPI.
    
    Returns:
        FastAPI: Instance de l'application configurée
    """
    # Initialisation de l'application FastAPI
    app = FastAPI(
        title="Orchestrator Agent API",
        description="API pour l'orchestration d'agents IA avec support multi-LLM",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configuration CORS pour le développement
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À restreindre en production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware de sécurité UTF-8 (Jalon 2.6)
    app.add_middleware(UTF8EnforcementMiddleware)
    
    # Inclusion du routeur principal
    app.include_router(router, prefix="/api")
    
    return app


# Création de l'instance de l'application
app = create_app()


if __name__ == "__main__":
    # Configuration d'encodage système
    import locale
    import os
    
    # Force UTF-8 pour les variables d'environnement
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # Tentative de configuration locale UTF-8
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            pass  # Garder la locale par défaut si UTF-8 non disponible
    
    # Démarrage de l'application avec uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Rechargement automatique en développement
        log_level="info",
        # Configuration explicite d'encodage
        access_log=True
    )