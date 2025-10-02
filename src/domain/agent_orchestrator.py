"""Agent Orchestrator - Moteur d'agent gérant la boucle ReAct (Reasoning + Acting)"""

from typing import List, Optional, TYPE_CHECKING
import asyncio
import logging
from datetime import datetime
from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.tracer import Tracer  # JALON 4.1-B: Intégration du traçage
from src.domain.resilient_llm_service import ResilientLLMService  # JALON 4.2: Service résilient
from src.infrastructure.tool_executor import ToolExecutor
from src.models.data_contracts import (
    AgentConfig, 
    ChatMessage, 
    OrchestrationRequest,
    OrchestrationResponse,
    ToolCall,
    ToolResult,
    Session,
    AgentExecutionError  # JALON 4.2: Exception de résilience
)

if TYPE_CHECKING:
    from .history_summarizer import HistorySummarizer

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrateur d'agent responsable de la coordination des services LLM et d'exécution d'outils.
    Implémente la boucle ReAct (Reasoning + Acting) avec gestion multi-tours.
    """
    
    def __init__(
        self, 
        llm_service: LLMServiceInterface, 
        tool_executor: ToolExecutor,
        history_summarizer: Optional['HistorySummarizer'] = None
    ):
        """
        Initialise l'orchestrateur avec injection de dépendances
        
        Args:
            llm_service: Service LLM injecté (interface)
            tool_executor: Exécuteur d'outils injecté
            history_summarizer: Service de synthèse d'historique (optionnel)
        """
        self.llm_service = llm_service
        self.tool_executor = tool_executor
        self.history_summarizer = history_summarizer
        
        # JALON 4.2: Service résilient pour les appels LLM
        self.resilient_service: Optional[ResilientLLMService] = None
        
        # Configuration pour la limitation des boucles
        self.max_iterations = 3
    
    def _initialize_resilient_service(self, tracer: Optional[Tracer] = None) -> None:
        """
        Initialise le service résilient si nécessaire (JALON 4.2)
        
        Args:
            tracer: Instance de tracer pour l'observabilité
        """
        if self.resilient_service is None:
            self.resilient_service = ResilientLLMService(tracer=tracer)
        self.max_iterations = 3  # Limite pour éviter les boucles infinies
    
    async def run_orchestration(
        self, 
        config: AgentConfig, 
        history: List[ChatMessage],
        tracer: Optional[Tracer] = None
    ) -> OrchestrationResponse:
        """
        Méthode principale d'orchestration gérant la boucle ReAct avec durcissement sécuritaire
        
        Args:
            config: Configuration de l'agent
            history: Historique de conversation
            tracer: Tracer optionnel pour l'observabilité (JALON 4.1-B)
            
        Returns:
            Réponse finale d'orchestration
            
        Flow:
            1. Itération (max 3 tours)
            2. Appel LLM -> Check Tool Call -> Exécution Outil -> Rétro-injection
            3. Répétition jusqu'à réponse texte finale
            
        Sécurité:
            - Gestion robuste des erreurs avec arrêt d'urgence
            - Protection contre les boucles infinies
            - Isolation des erreurs d'outils
        """
        logger.info(f"🚀 Début orchestration avec {len(history)} messages d'historique")
        
        # JALON 4.1-B: Traçage du début de l'orchestration principale
        if tracer:
            await tracer.log_orchestration_start(
                agent_name=config.agent_name,
                iteration=1
            )
        
        current_history = history.copy()
        iteration = 0
        total_tool_calls = 0
        max_total_tool_calls = 10  # Protection contre l'abus d'outils
        
        # Validation préliminaire
        try:
            if not config:
                raise ValueError("Configuration requise pour l'orchestration")
            # L'historique peut être vide pour une nouvelle session
            if history is None:
                raise ValueError("Historique requis (peut être vide) pour l'orchestration")
        except Exception as e:
            logger.error(f"❌ Erreur validation préliminaire: {str(e)}")
            return self._create_error_response(
                f"Erreur de validation: {str(e)}", 
                config, 
                "VALIDATION_ERROR"
            )
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"🔄 Itération {iteration}/{self.max_iterations}")
            
            try:
                # === PHASE 1: REASONING - Appel LLM ===
                # JALON 4.1-B: Traçage de l'appel LLM
                if tracer:
                    await tracer.log_llm_call(
                        provider=self.llm_service.get_provider_name(),
                        model=config.model_version if hasattr(config, 'model_version') else "unknown",
                        prompt_length=sum(len(msg.content) for msg in current_history)
                    )
                
                # JALON 4.2: Appel LLM résilient avec retry/backoff
                llm_response = await self._call_llm_with_config_safe(config, current_history, tracer)
                
                if llm_response is None:
                    logger.error("❌ Réponse LLM nulle - Arrêt d'urgence")
                    return self._create_error_response(
                        "Erreur LLM: réponse nulle obtenue", 
                        config, 
                        "LLM_NULL_RESPONSE"
                    )
                
                logger.info(f"📝 Réponse LLM - Tool calls: {len(llm_response.tool_calls)}, "
                           f"Requires execution: {llm_response.requires_tool_execution}")
                
                # === PHASE 2: CHECK - Analyse de la réponse ===
                if not llm_response.requires_tool_execution or not llm_response.tool_calls:
                    # Réponse finale en texte - Fin de la boucle ReAct
                    logger.info("✅ Réponse finale obtenue - Fin de l'orchestration")
                    
                    # JALON 4.1-B: Traçage de la réponse finale
                    if tracer:
                        await tracer.log_final_response(
                            response_length=len(llm_response.content),
                            total_steps=iteration
                        )
                    
                    return llm_response
                
                # Protection contre l'abus d'outils
                total_tool_calls += len(llm_response.tool_calls)
                if total_tool_calls > max_total_tool_calls:
                    logger.warning(f"⚠️ Limite d'outils atteinte ({total_tool_calls})")
                    return self._create_error_response(
                        f"Limite d'exécutions d'outils atteinte ({max_total_tool_calls})",
                        config,
                        "TOO_MANY_TOOL_CALLS"
                    )
                
                # === PHASE 3: ACTING - Exécution des outils ===
                logger.info(f"🔧 Exécution de {len(llm_response.tool_calls)} outil(s)")
                
                # JALON 4.1-B: Traçage de l'exécution d'outils
                if tracer:
                    for tool_call in llm_response.tool_calls:
                        await tracer.log_tool_execution(
                            tool_name=tool_call.function.name,
                            tool_arguments=tool_call.function.arguments
                        )
                
                tool_results = await self._execute_tool_calls_safe(llm_response.tool_calls)
                
                if tool_results is None:
                    logger.error("❌ Échec critique d'exécution d'outils")
                    return self._create_error_response(
                        "Erreur critique lors de l'exécution des outils",
                        config,
                        "TOOL_EXECUTION_CRITICAL_FAILURE"
                    )
                
                # === PHASE 4: FEEDBACK - Rétro-injection des résultats ===
                await self._inject_tool_results_to_history(
                    current_history, 
                    llm_response.tool_calls, 
                    tool_results
                )
                
                logger.info(f"🔄 Résultats injectés - Préparation itération suivante")
                
            except Exception as e:
                logger.error(f"❌ Erreur critique durant l'itération {iteration}: {str(e)}")
                
                # JALON 4.1-B: Traçage des erreurs
                if tracer:
                    await tracer.log_error(
                        error_type="ITERATION_CRITICAL_ERROR",
                        error_message=str(e)
                    )
                
                return self._create_error_response(
                    f"Erreur critique itération {iteration}: {str(e)}", 
                    config, 
                    "ITERATION_CRITICAL_ERROR"
                )
        
        # Limite d'itérations atteinte - Arrêt de sécurité
        logger.warning(f"⚠️ Limite d'itérations atteinte ({self.max_iterations})")
        return self._create_error_response(
            f"Limite d'itérations atteinte ({self.max_iterations}). "
            f"L'agent n'a pas pu converger vers une réponse finale. "
            f"Cela peut indiquer une boucle logique dans le raisonnement.",
            config,
            "MAX_ITERATIONS_EXCEEDED"
        )
    
    
    def _create_error_response(
        self, 
        error_message: str, 
        config: AgentConfig, 
        error_code: str = "UNKNOWN_ERROR"
    ) -> OrchestrationResponse:
        """
        Crée une réponse d'erreur structurée pour l'orchestration
        
        Args:
            error_message: Message d'erreur descriptif
            config: Configuration de l'agent
            error_code: Code d'erreur pour le diagnostic
            
        Returns:
            OrchestrationResponse d'erreur structurée
        """
        return OrchestrationResponse(
            content=f"[ERREUR ORCHESTRATION - {error_code}] {error_message}",
            tool_calls=[],
            provider=self.llm_service.get_provider_name(),
            model=config.model_version if config else "unknown",
            usage={"error": True, "error_code": error_code},
            requires_tool_execution=False
        )
    
    async def _call_llm_with_config_safe(
        self, 
        config: AgentConfig, 
        history: List[ChatMessage],
        tracer: Optional[Tracer] = None
    ) -> Optional[OrchestrationResponse]:
        """
        Version sécurisée de l'appel LLM avec résilience et gestion robuste des erreurs (JALON 4.2)
        
        Args:
            config: Configuration de l'agent
            history: Historique de conversation
            tracer: Tracer pour l'observabilité
            
        Returns:
            Réponse du LLM ou None en cas d'erreur critique
        """
        try:
            # JALON 4.2: Utilisation du service résilient
            self._initialize_resilient_service(tracer)
            
            # Construction de la requête d'orchestration
            request = OrchestrationRequest(
                message="",  # Le message utilisateur est déjà dans l'historique
                agent_config=config,
                conversation_history=history
            )
            
            # Appel résilient avec retry et backoff
            return await self.resilient_service.resilient_chat_completion(config, request)
            
        except AgentExecutionError as e:
            # JALON 4.2: Gestion sécurisée des erreurs finales de résilience
            logger.error(f"❌ Échec définitif appel LLM après retry: {str(e)}")
            
            # Traçage de l'erreur finale sécurisée
            if tracer:
                await tracer.log_error(
                    error_type="RESILIENT_LLM_FAILURE",
                    error_message=f"Échec définitif après {e.attempts} tentatives: {e.message}"
                )
            
            return None
            
        except Exception as e:
            # Autres erreurs non prévues
            logger.error(f"❌ Erreur critique inattendue appel LLM: {str(e)}")
            
            if tracer:
                await tracer.log_error(
                    error_type="UNEXPECTED_LLM_ERROR",
                    error_message=f"Erreur inattendue: {type(e).__name__}"
                )
            
            return None
    
    async def _execute_tool_calls_safe(self, tool_calls: List[ToolCall]) -> Optional[List[ToolResult]]:
        """
        Version sécurisée de l'exécution d'outils avec isolation des erreurs
        
        Args:
            tool_calls: Liste des appels d'outils à exécuter
            
        Returns:
            Liste des résultats ou None en cas d'erreur critique
        """
        try:
            if not tool_calls:
                return []
            
            # Limitation du nombre d'outils par appel
            max_concurrent_tools = 5
            if len(tool_calls) > max_concurrent_tools:
                logger.warning(f"⚠️ Limitation à {max_concurrent_tools} outils par appel")
                tool_calls = tool_calls[:max_concurrent_tools]
            
            # Exécution avec timeout global
            timeout_seconds = 30  # 30 secondes max pour tous les outils
            
            results = await asyncio.wait_for(
                self._execute_tool_calls(tool_calls),
                timeout=timeout_seconds
            )
            
            return results
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout exécution outils ({timeout_seconds}s)")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur critique exécution outils: {str(e)}")
            return None
    
    async def _execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Exécute tous les appels d'outils en parallèle
        
        Args:
            tool_calls: Liste des appels d'outils à exécuter
            
        Returns:
            Liste des résultats d'exécution
        """
        if not tool_calls:
            return []
        
        # Exécution parallèle des outils via asyncio.gather
        tasks = [
            self.tool_executor.execute_tool(tool_call) 
            for tool_call in tool_calls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traitement des exceptions éventuelles
        tool_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Erreur outil {tool_calls[i].tool_name}: {str(result)}")
                tool_results.append(ToolResult(
                    tool_call_id=tool_calls[i].id,
                    success=False,
                    result=None,
                    error=str(result)
                ))
            else:
                tool_results.append(result)
        
        return tool_results
    
    async def _inject_tool_results_to_history(
        self, 
        history: List[ChatMessage], 
        tool_calls: List[ToolCall],
        tool_results: List[ToolResult]
    ) -> None:
        """
        Injecte les résultats d'outils dans l'historique pour rétro-alimentation
        
        Args:
            history: Historique de conversation à modifier
            tool_calls: Appels d'outils effectués
            tool_results: Résultats d'exécution correspondants
        """
        # D'abord, ajouter le message assistant avec les tool_calls
        tool_calls_content = self._format_tool_calls_for_history(tool_calls)
        history.append(ChatMessage(
            role="assistant",
            content=tool_calls_content
        ))
        
        # Ensuite, ajouter les résultats des outils
        for tool_result in tool_results:
            result_content = self._format_tool_result_for_history(tool_result)
            history.append(ChatMessage(
                role="tool",
                content=result_content
            ))
        
        logger.info(f"📝 {len(tool_results)} résultat(s) d'outil ajouté(s) à l'historique")
    
    def _format_tool_calls_for_history(self, tool_calls: List[ToolCall]) -> str:
        """
        Formate les appels d'outils pour l'historique de conversation
        
        Args:
            tool_calls: Liste des appels d'outils
            
        Returns:
            Représentation textuelle des appels d'outils
        """
        if not tool_calls:
            return "Aucun outil appelé"
        
        formatted_calls = []
        for call in tool_calls:
            args_str = ", ".join([f"{k}={v}" for k, v in call.arguments.items()])
            formatted_calls.append(f"{call.tool_name}({args_str})")
        
        return f"Appel d'outils: {', '.join(formatted_calls)}"
    
    def _format_tool_result_for_history(self, tool_result: ToolResult) -> str:
        """
        Formate un résultat d'outil pour l'historique de conversation
        
        Args:
            tool_result: Résultat d'exécution d'outil
            
        Returns:
            Représentation textuelle du résultat
        """
        if tool_result.success:
            return f"Résultat outil: {tool_result.result}"
        else:
            return f"Erreur outil: {tool_result.error}"
    
    def _create_error_response(
        self, 
        error_message: str, 
        config: AgentConfig, 
        error_code: str = "GENERAL_ERROR"
    ) -> OrchestrationResponse:
        """
        Crée une réponse d'erreur sécurisée pour l'utilisateur (JALON 4.2)
        
        Args:
            error_message: Message d'erreur sécurisé
            config: Configuration d'agent
            error_code: Code d'erreur technique
            
        Returns:
            Réponse d'orchestration avec message d'erreur
        """
        safe_message = (
            f"❌ Je rencontre actuellement des difficultés techniques. "
            f"{error_message}. Veuillez réessayer dans quelques instants."
        )
        
        return OrchestrationResponse(
            content=safe_message,
            tool_calls=[],
            requires_tool_execution=False,
            agent_name=config.agent_name if hasattr(config, 'agent_name') else "assistant",
            processing_info={
                "error_code": error_code,
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def run_orchestration_with_session(
        self, 
        request: OrchestrationRequest, 
        session: Session,
        tracer: Optional[Tracer] = None  # JALON 4.1-B: Traçage optionnel
    ) -> OrchestrationResponse:
        """
        Version avec session : orchestre la boucle ReAct avec synthèse automatique d'historique
        
        Args:
            request: Requête d'orchestration
            session: Session avec historique persistant
            tracer: Tracer optionnel pour l'observabilité (JALON 4.1-B)
            
        Returns:
            Réponse finale d'orchestration avec session mise à jour
            
        Flow:
            1. Synthèse de l'historique si seuils dépassés
            2. Orchestration standard avec historique synthétisé
            3. Ajout du message utilisateur et de la réponse à la session
        """
        logger.info(f"🔄 Orchestration avec session {session.session_id}")
        
        # JALON 4.1-B: Traçage du début de l'orchestration
        if tracer:
            await tracer.log_orchestration_start(
                agent_name=session.agent_name,
                iteration=1
            )
        
        # Synthèse automatique de l'historique si nécessaire
        if self.history_summarizer:
            await self.history_summarizer.summarize_if_needed(session, tracer)
        
        # Utilisation de la config d'agent fournie ou création d'une config par défaut
        if request.agent_config:
            config = request.agent_config
        else:
            # Configuration par défaut si aucune fournie
            config = AgentConfig()
        
        response = await self.run_orchestration(config, session.history, tracer)
        
        # Ajout des messages à la session
        user_message = ChatMessage(
            role="user",
            content=request.message
        )
        session.history.append(user_message)
        
        assistant_message = ChatMessage(
            role="assistant", 
            content=response.content
        )
        session.history.append(assistant_message)
        
        # Mise à jour des métriques de session
        session.last_message_at = datetime.now()
        metrics = session.get_history_metrics()
        
        # JALON 4.1-B: Traçage de la réponse finale
        if tracer:
            await tracer.log_final_response(
                response_length=len(response.content),
                total_steps=len(session.trace) if session.trace else 0
            )
        
        logger.info(f"✅ Session {session.session_id} mise à jour: {metrics['messages']} messages")
        
        return response