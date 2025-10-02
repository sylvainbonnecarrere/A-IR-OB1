"""
Script de test et validation pour le Jalon 1.3 - Microservice FastAPI minimal.

Ce script valide que :
1. L'application FastAPI démarre correctement
2. L'endpoint /health est accessible et retourne la bonne réponse
3. L'endpoint racine fonctionne
4. La documentation API est accessible

Usage: python debug/test_jalon_1_3.py
"""

import asyncio
import httpx
import time
from typing import Dict, Any


async def test_health_endpoint() -> Dict[str, Any]:
    """
    Teste l'endpoint de health check.
    
    Returns:
        Dict[str, Any]: Résultat du test
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/api/health")
            
            if response.status_code == 200:
                data = response.json()
                expected = {"status": "ok", "service": "orchestrator"}
                
                if data == expected:
                    return {
                        "test": "health_endpoint",
                        "status": "PASS",
                        "message": "Health check endpoint fonctionne correctement",
                        "data": data
                    }
                else:
                    return {
                        "test": "health_endpoint",
                        "status": "FAIL",
                        "message": f"Réponse incorrecte. Attendu: {expected}, Reçu: {data}",
                        "data": data
                    }
            else:
                return {
                    "test": "health_endpoint",
                    "status": "FAIL",
                    "message": f"Status code incorrect: {response.status_code}",
                    "data": None
                }
                
    except Exception as e:
        return {
            "test": "health_endpoint",
            "status": "ERROR",
            "message": f"Erreur lors du test: {str(e)}",
            "data": None
        }


async def test_root_endpoint() -> Dict[str, Any]:
    """
    Teste l'endpoint racine.
    
    Returns:
        Dict[str, Any]: Résultat du test
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/api/")
            
            if response.status_code == 200:
                data = response.json()
                required_keys = ["message", "version", "status"]
                
                if all(key in data for key in required_keys):
                    return {
                        "test": "root_endpoint",
                        "status": "PASS",
                        "message": "Endpoint racine fonctionne correctement",
                        "data": data
                    }
                else:
                    return {
                        "test": "root_endpoint",
                        "status": "FAIL",
                        "message": f"Clés manquantes dans la réponse. Attendu: {required_keys}",
                        "data": data
                    }
            else:
                return {
                    "test": "root_endpoint",
                    "status": "FAIL",
                    "message": f"Status code incorrect: {response.status_code}",
                    "data": None
                }
                
    except Exception as e:
        return {
            "test": "root_endpoint",
            "status": "ERROR",
            "message": f"Erreur lors du test: {str(e)}",
            "data": None
        }


async def test_docs_endpoint() -> Dict[str, Any]:
    """
    Teste l'accessibilité de la documentation.
    
    Returns:
        Dict[str, Any]: Résultat du test
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/docs")
            
            if response.status_code == 200:
                return {
                    "test": "docs_endpoint",
                    "status": "PASS",
                    "message": "Documentation API accessible",
                    "data": None
                }
            else:
                return {
                    "test": "docs_endpoint",
                    "status": "FAIL",
                    "message": f"Status code incorrect: {response.status_code}",
                    "data": None
                }
                
    except Exception as e:
        return {
            "test": "docs_endpoint",
            "status": "ERROR",
            "message": f"Erreur lors du test: {str(e)}",
            "data": None
        }


async def run_all_tests() -> None:
    """
    Exécute tous les tests de validation du Jalon 1.3.
    """
    print("🚀 Validation du Jalon 1.3 - Microservice FastAPI minimal")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_docs_endpoint
    ]
    
    results = []
    
    for test_func in tests:
        print(f"\n🔍 Exécution du test: {test_func.__name__}")
        result = await test_func()
        results.append(result)
        
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "ERROR": "🚨"
        }.get(result["status"], "❓")
        
        print(f"{status_icon} {result['status']}: {result['message']}")
        
        if result["data"]:
            print(f"   📄 Données: {result['data']}")
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    
    print(f"✅ Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 JALON 1.3 VALIDÉ - Le microservice FastAPI fonctionne correctement!")
        print("\nCommande de démarrage recommandée:")
        print("$env:PYTHONPATH = \"$(pwd)\"; uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez que l'application est démarrée.")
        print("Pour démarrer l'application:")
        print("$env:PYTHONPATH = \"$(pwd)\"; uvicorn main:app --reload --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    # Petit délai pour laisser le temps au serveur de démarrer
    print("⏳ Attente de 2 secondes pour le démarrage du serveur...")
    time.sleep(2)
    
    asyncio.run(run_all_tests())