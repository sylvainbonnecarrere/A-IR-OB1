"""FastAPI Router - Endpoints avec Dependency Injection"""

from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from src.api.dependencies import (
    get_default_llm_service, 
    get_llm_service_from_config,
    get_tool_executor,
    llm_provider
)
from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.llm_service_factory import LLMServiceFactory
from src.domain.agent_orchestrator import AgentOrchestrator
from src.domain.agent_router import AgentRouter
from src.domain.history_summarizer import HistorySummarizer
from src.infrastructure.tool_executor import ToolExecutor
from src.infrastructure.session_manager import InMemorySessionManager
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
    OrchestrationResponse,
    AgentDefinition,
    AgentConfig,
    LLMProvider,
    Session,
    HistoryConfig,
    SessionCreateRequest,
    SessionResponse
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


@router.post("/api/orchestrate", response_model=OrchestrationResponse, summary="Multi-Agent Orchestration with Router + ReAct Loop")
async def orchestrate_agent(
    request: OrchestrationRequest,
    llm_service: LLMServiceInterface = Depends(get_default_llm_service),
    tool_executor: ToolExecutor = Depends(get_tool_executor)
):
    """
    Endpoint principal d'orchestration multi-agents avec routeur intelligent
    
    Ce endpoint implémente le nouveau flux à 2 niveaux:
    
    **Niveau 1 - Routeur (Moteur de Décision):**
    1. Analyse l'intention utilisateur via Function Calling
    2. Sélectionne l'agent spécialisé le plus approprié
    3. Retourne la configuration optimale pour cet agent
    
    **Niveau 2 - Orchestrateur (Moteur d'Exécution):**
    1. **Reasoning**: L'agent sélectionné analyse la requête
    2. **Acting**: Exécution des outils spécialisés de l'agent
    3. **Feedback**: Rétro-injection des résultats
    4. **Repeat**: Répétition jusqu'à obtention d'une réponse finale
    
    Args:
        request: Requête d'orchestration contenant le message
        llm_service: Service LLM pour le routeur (modèle rapide)
        tool_executor: Exécuteur d'outils injecté
        
    Returns:
        OrchestrationResponse: Réponse finale après routage + boucle ReAct
        
    Raises:
        HTTPException: En cas d'erreur lors de l'orchestration
        
    Example:
        ```json
        {
            "message": "Quelle est l'heure maintenant ?",
            "conversation_history": []
        }
        ```
        
    Note: 
        La configuration agent_config est maintenant déterminée automatiquement
        par le routeur en fonction de l'intention détectée dans le message.
    """
    try:
        # ========================================
        # ÉTAPE 1: ROUTAGE INTELLIGENT
        # ========================================
        
        # Création du routeur avec un LLM rapide pour la décision
        router_service = LLMServiceFactory.create_service(LLMProvider.OPENAI)
        agent_router = AgentRouter(router_service)
        
        # Définition des agents spécialisés disponibles
        available_agents = _get_demo_agents()
        
        # Message utilisateur pour le routage
        user_message = ChatMessage(role="user", content=request.message)
        
        # Sélection de l'agent approprié via Function Calling
        selected_agent = await agent_router.dispatch(user_message, available_agents)
        
        print(f"🎯 Agent sélectionné: {selected_agent.agent_name}")
        print(f"📋 Description: {selected_agent.description}")
        
        # ========================================
        # ÉTAPE 2: ORCHESTRATION SPÉCIALISÉE
        # ========================================
        
        # Création du service LLM spécialisé pour l'agent sélectionné
        specialized_service = LLMServiceFactory.create_service(
            selected_agent.default_config.provider
        )
        
        # Création de l'orchestrateur avec le service spécialisé
        orchestrator = AgentOrchestrator(
            llm_service=specialized_service,
            tool_executor=tool_executor
        )
        
        # Construction de l'historique avec le message utilisateur
        history = list(request.conversation_history)
        if request.message:
            history.append(ChatMessage(role="user", content=request.message))
        
        # Exécution de la boucle ReAct avec la configuration de l'agent sélectionné
        response = await orchestrator.run_orchestration(
            config=selected_agent.default_config,
            history=history
        )
        
        # Enrichissement de la réponse avec les informations de routage
        response.provider = f"{response.provider} (via {selected_agent.agent_name})"
        
        return response
        
    except HTTPException:
        # Re-lancer les HTTPException directement
        raise
    except Exception as e:
        # Capturer toutes les autres erreurs
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de l'orchestration multi-agents: {str(e)}"
        )


def _get_demo_agents() -> list[AgentDefinition]:
    """
    Crée une liste d'agents de démonstration pour le Jalon 3.4
    
    Returns:
        List[AgentDefinition]: Liste des agents spécialisés disponibles
    """
    return [
        # Agent spécialisé dans les informations temporelles et système
        AgentDefinition(
            agent_name="Time_Info_Agent",
            description="Agent spécialisé dans les requêtes temporelles (heure, date, fuseaux horaires) et les informations système",
            default_config=AgentConfig(
                provider=LLMProvider.OPENAI,
                model_version="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=800,
                tools_enabled=True,
                available_tools=["get_current_time"],
                system_prompt="Tu es Time_Info_Agent, un assistant spécialisé dans les informations temporelles et système. Tu fournis des informations précises sur l'heure, la date, les fuseaux horaires et les données système. Utilise les outils disponibles pour obtenir des informations en temps réel."
            )
        ),
        
        # Agent généraliste pour les tâches de résumé et d'analyse textuelle
        AgentDefinition(
            agent_name="Text_Analysis_Agent", 
            description="Agent spécialisé dans l'analyse, le résumé et le traitement de texte. Idéal pour les tâches de rédaction, résumé, analyse littéraire et traitement linguistique",
            default_config=AgentConfig(
                provider=LLMProvider.GEMINI,
                model_version="gemini-2.0-flash-exp",
                temperature=0.7,
                max_tokens=1500,
                tools_enabled=False,  # Pas d'outils, focus sur le traitement textuel
                available_tools=[],
                system_prompt="Tu es Text_Analysis_Agent, un expert en analyse et traitement de texte. Tu excelles dans la rédaction, le résumé, l'analyse littéraire, la création de contenu et toutes les tâches liées au language. Tu fournis des réponses détaillées et bien structurées."
            )
        ),
        
        # Agent pour les calculs et la logique
        AgentDefinition(
            agent_name="Logic_Math_Agent",
            description="Agent spécialisé dans les calculs mathématiques, la logique, les problèmes analytiques et le raisonnement quantitatif",
            default_config=AgentConfig(
                provider=LLMProvider.ANTHROPIC,
                model_version="claude-3-opus-20240229",
                temperature=0.1,  # Température basse pour la précision
                max_tokens=1000,
                tools_enabled=False,
                available_tools=[],
                system_prompt="Tu es Logic_Math_Agent, un spécialiste des mathématiques et de la logique. Tu résous des problèmes quantitatifs, effectues des calculs complexes, analyses des données numériques et raisonnes de manière analytique. Tu donnes des réponses précises et détaillées avec des explications étape par étape."
            )
        )
    ]


# === Instances globales pour la gestion des sessions (Jalon 3.5) ===

# Configuration par défaut pour l'historique
DEFAULT_HISTORY_CONFIG = HistoryConfig(
    message_threshold=10,
    char_threshold=15000,
    summary_provider=LLMProvider.GEMINI,
    summary_model="gemini-2.0-flash-exp"
)

# Gestionnaire de sessions (en mémoire pour le développement)
session_manager = InMemorySessionManager()

# Service de synthèse d'historique
history_summarizer = HistorySummarizer(
    llm_service_factory=LLMServiceFactory(),
    default_config=DEFAULT_HISTORY_CONFIG
)


# === Endpoints de gestion des sessions (Jalon 3.5) ===

@router.post(
    "/sessions",
    response_model=SessionResponse,
    summary="Créer une nouvelle session",
    description="Crée une nouvelle session de conversation persistante pour un agent donné"
)
async def create_session(
    request: SessionCreateRequest,
    background_tasks: BackgroundTasks
) -> SessionResponse:
    """
    Crée une nouvelle session de conversation
    
    Args:
        request: Paramètres de création de session
        background_tasks: Tâches en arrière-plan pour initialisation
        
    Returns:
        Informations de la session créée
        
    Raises:
        HTTPException: En cas d'erreur de création
    """
    try:
        # Configuration d'historique (utilise celle fournie ou par défaut)
        history_config = request.history_config or DEFAULT_HISTORY_CONFIG
        
        # Création de la session
        session = await session_manager.create_new_session(
            agent_name=request.agent_name,
            history_config=history_config
        )
        
        # Tâche en arrière-plan pour logging
        background_tasks.add_task(
            _log_session_creation, 
            session.session_id, 
            request.agent_name
        )
        
        # Récupération des métriques
        metrics = session.get_history_metrics()
        
        return SessionResponse(
            session_id=session.session_id,
            agent_name=session.agent_name,
            total_messages=metrics["messages"],
            created_at=session.created_at,
            last_message_at=session.last_message_at,
            status="active",
            total_characters=metrics["chars"],
            total_words=metrics["words"],
            estimated_tokens=metrics["estimated_tokens"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur création session: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Récupérer une session",
    description="Récupère les informations d'une session existante par son ID"
)
async def get_session(session_id: str) -> SessionResponse:
    """
    Récupère une session par son ID
    
    Args:
        session_id: Identifiant unique de la session
        
    Returns:
        Informations de la session
        
    Raises:
        HTTPException: Si la session n'existe pas
    """
    try:
        # Validation de l'UUID
        uuid.UUID(session_id)
        
        # Récupération de la session
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} non trouvée"
            )
        
        # Récupération des métriques
        metrics = session.get_history_metrics()
        
        return SessionResponse(
            session_id=session.session_id,
            agent_name=session.agent_name,
            total_messages=metrics["messages"],
            created_at=session.created_at,
            last_message_at=session.last_message_at,
            status="active",
            total_characters=metrics["chars"],
            total_words=metrics["words"],
            estimated_tokens=metrics["estimated_tokens"]
        )
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format d'ID de session invalide"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur récupération session: {str(e)}"
        )


@router.post(
    "/sessions/{session_id}/orchestrate",
    response_model=OrchestrationResponse,
    summary="Orchestration avec session",
    description="Lance une orchestration dans le contexte d'une session persistante avec synthèse automatique"
)
async def orchestrate_with_session(
    session_id: str,
    request: OrchestrationRequest,
    background_tasks: BackgroundTasks,
    llm_service: LLMServiceInterface = Depends(get_llm_service_from_config),
    tool_executor: ToolExecutor = Depends(get_tool_executor)
) -> OrchestrationResponse:
    """
    Lance une orchestration dans une session persistante
    
    Args:
        session_id: ID de la session
        request: Requête d'orchestration
        background_tasks: Tâches asynchrones
        llm_service: Service LLM injecté
        tool_executor: Exécuteur d'outils injecté
        
    Returns:
        Réponse d'orchestration avec session mise à jour
        
    Raises:
        HTTPException: Si la session n'existe pas ou erreur d'orchestration
    """
    try:
        # Validation et récupération de session
        uuid.UUID(session_id)
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} non trouvée"
            )
        
        # Création de l'orchestrateur avec synthèse d'historique
        orchestrator = AgentOrchestrator(
            llm_service=llm_service,
            tool_executor=tool_executor,
            history_summarizer=history_summarizer
        )
        
        # Orchestration avec session
        response = await orchestrator.run_orchestration_with_session(
            request=request,
            session=session
        )
        
        # Sauvegarde asynchrone de la session mise à jour
        background_tasks.add_task(
            _update_session_async,
            session_id,
            session
        )
        
        return response
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format d'ID de session invalide"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur orchestration avec session: {str(e)}"
        )


# === Fonctions utilitaires pour tâches en arrière-plan ===

async def _log_session_creation(session_id: str, agent_name: str):
    """Log la création d'une session"""
    print(f"📝 Session créée: {session_id} pour agent {agent_name}")


async def _update_session_async(session_id: str, session: Session):
    """Met à jour une session de manière asynchrone"""
    try:
        await session_manager.update_session(session)
        print(f"💾 Session {session_id} sauvegardée avec {session.total_messages} messages")
    except Exception as e:
        print(f"❌ Erreur sauvegarde session {session_id}: {e}")