"""FastAPI Router - Endpoints avec Dependency Injection"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import (
    get_default_llm_service, 
    get_llm_service_from_config,
    llm_provider
)
from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.llm_service_factory import LLMServiceFactory
from src.domain.agent_orchestrator import AgentOrchestrator
from src.infrastructure.tool_executor import ToolExecutor
from src.models.data_contracts import (
    HealthResponse,
    ServiceTestRequest,
    ServiceTestResponse,
    ProvidersResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ErrorResponse,
    OrchestrationRequest,
    OrchestrationResponse
)

# Création du router
router = APIRouter()


@router.get("/", summary="Page d'accueil")
async def root():
    """Endpoint racine avec liens de navigation"""
    return {
        "message": "🤖 A-IR-OB1 - AI Agent Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "test_service": "/test-service",
            "providers": "/providers",
            "chat": "/chat"
        },
        "repository": "https://github.com/sylvainbonnecarrere/A-IR-OB1"
    }


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """Vérification de santé de l'application"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.post("/test-service", response_model=ServiceTestResponse, summary="Test LLM Service")
async def test_llm_service(
    request: ServiceTestRequest = ServiceTestRequest(),
    llm_service: LLMServiceInterface = Depends(get_default_llm_service)
):
    """Test du service LLM avec injection de dépendances"""
    try:
        # Test simple du service
        response = await llm_service.simple_completion(request.message)
        
        return ServiceTestResponse(
            success=True,
            response=response,
            provider=llm_service.get_provider_name(),
            error=None
        )
    except Exception as e:
        return ServiceTestResponse(
            success=False,
            response=None,
            provider=llm_service.get_provider_name(),
            error=str(e)
        )


@router.get("/providers", response_model=ProvidersResponse, summary="Available LLM Providers")
async def get_providers():
    """Liste des fournisseurs LLM disponibles"""
    providers = LLMServiceFactory.get_available_providers()
    return ProvidersResponse(
        providers=providers,
        default="openai",
        count=len(providers)
    )


@router.post("/chat", response_model=ChatResponse, summary="Chat with LLM")
async def chat_completion(
    request: ChatRequest,
    llm_service: LLMServiceInterface = Depends(get_default_llm_service)
):
    """Endpoint de chat avec LLM"""
    try:
        # Créer le message pour le LLM
        messages = [ChatMessage(role="user", content=request.message)]
        
        # Appel au service LLM
        response = await llm_service.chat_completion(
            messages=messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.get("/providers/info", summary="Detailed Provider Information")
async def get_providers_info():
    """Informations détaillées sur tous les fournisseurs"""
    try:
        info = LLMServiceFactory.get_provider_info()
        return {
            "providers": info,
            "count": len(info),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")


@router.post("/providers/{provider}/test", response_model=ServiceTestResponse, summary="Test Specific Provider")
async def test_specific_provider(
    provider: str,
    request: ServiceTestRequest = ServiceTestRequest()
):
    """Test d'un fournisseur spécifique"""
    try:
        # Obtenir le service pour ce fournisseur
        llm_service = LLMServiceFactory.create_service(provider)
        
        # Test du service
        response = await llm_service.simple_completion(request.message)
        
        return ServiceTestResponse(
            success=True,
            response=response,
            provider=provider,
            error=None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return ServiceTestResponse(
            success=False,
            response=None,
            provider=provider,
            error=str(e)
        )


@router.get("/debug/factory", summary="Factory Debug Info")
async def debug_factory():
    """Informations de debug sur la factory"""
    return {
        "available_providers": LLMServiceFactory.get_available_providers(),
        "cache_size": len(LLMServiceFactory._instances),
        "registered_adapters": list(LLMServiceFactory._providers.keys()),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# JALON 2.5 - ENDPOINT D'ORCHESTRATION AVEC BOUCLE REACT
# ============================================================================

def get_tool_executor() -> ToolExecutor:
    """
    Dependency pour obtenir une instance de ToolExecutor
    
    Returns:
        ToolExecutor: Instance configurée avec les outils disponibles
    """
    return ToolExecutor()


@router.post("/api/orchestrate", response_model=OrchestrationResponse, summary="Agent Orchestration with ReAct Loop")
async def orchestrate_agent(
    request: OrchestrationRequest,
    llm_service: LLMServiceInterface = Depends(get_default_llm_service),
    tool_executor: ToolExecutor = Depends(get_tool_executor)
):
    """
    Endpoint principal d'orchestration d'agent avec boucle ReAct
    
    Ce endpoint coordonne les services LLM et d'exécution d'outils pour implémenter
    une boucle complète de Reasoning + Acting (ReAct):
    
    1. **Reasoning**: L'agent analyse la requête et décide des actions
    2. **Acting**: Exécution des outils nécessaires
    3. **Feedback**: Rétro-injection des résultats pour la prochaine itération
    4. **Repeat**: Répétition jusqu'à obtention d'une réponse finale
    
    Args:
        request: Requête d'orchestration contenant le message et la configuration
        llm_service: Service LLM injecté (par défaut OpenAI)
        tool_executor: Exécuteur d'outils injecté
        
    Returns:
        OrchestrationResponse: Réponse finale après boucle ReAct complète
        
    Raises:
        HTTPException: En cas d'erreur lors de l'orchestration
        
    Example:
        ```json
        {
            "message": "Quelle est l'heure maintenant ?",
            "agent_config": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "tools_enabled": true,
                "available_tools": ["get_current_time"]
            },
            "conversation_history": []
        }
        ```
    """
    try:
        # Validation de la configuration
        if not request.agent_config:
            raise HTTPException(
                status_code=400, 
                detail="Configuration agent requise pour l'orchestration"
            )
        
        # Création de l'orchestrateur avec injection de dépendances
        orchestrator = AgentOrchestrator(
            llm_service=llm_service,
            tool_executor=tool_executor
        )
        
        # Construction de l'historique avec le message utilisateur
        history = list(request.conversation_history)
        if request.message:
            history.append(ChatMessage(role="user", content=request.message))
        
        # Exécution de la boucle ReAct
        response = await orchestrator.run_orchestration(
            config=request.agent_config,
            history=history
        )
        
        return response
        
    except HTTPException:
        # Re-lancer les HTTPException directement
        raise
    except Exception as e:
        # Capturer toutes les autres erreurs
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de l'orchestration: {str(e)}"
        )