"""
Service de Traçabilité (Tracing) - Observabilité du Flux d'Orchestration

Ce module implémente le système de traçage léger mais complet pour rendre
chaque cycle d'orchestration observable pour le débogage et l'analyse.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from src.models.data_contracts import TraceStep, SessionManager
from src.infrastructure.monitoring import get_metrics_collector  # JALON 4.3: Intégration métriques

logger = logging.getLogger(__name__)


class Tracer:
    """
    Service de traçage pour l'observabilité du flux d'orchestration
    
    Le Tracer s'intègre nativement dans les Sessions et utilise le SessionManager
    pour la persistance des traces. Il permet de suivre chaque étape du cycle
    d'exécution : Router → Orchestrator → LLM → Tools → Response.
    """
    
    def __init__(self, session_id: UUID, session_manager: SessionManager):
        """
        Initialise le service de traçage pour une session donnée
        
        Args:
            session_id: UUID de la session à tracer
            session_manager: Manager pour la persistance des sessions
        """
        self.session_id = session_id
        self.session_manager = session_manager
        self.logger = logging.getLogger(f"{__name__}.{session_id}")
    
    async def log_step(
        self, 
        component: str, 
        event: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Enregistre une étape de traçage dans la session
        
        Cette méthode constitue le cœur du système de traçabilité :
        1. Récupère la session via le SessionManager
        2. Crée un nouveau TraceStep avec horodatage
        3. Ajoute l'étape à la trace de la session
        4. Sauvegarde la session mise à jour
        
        Args:
            component: Nom du composant (Router/Orchestrator/LLM/etc.)
            event: Type d'événement (start/decision/call/response/error)
            details: Détails optionnels spécifiques à l'étape
            
        Raises:
            Exception: Si la session n'existe pas ou erreur de persistance
        """
        try:
            # Récupérer la session actuelle
            session = await self.session_manager.get_session(self.session_id)
            
            if not session:
                raise ValueError(f"Session {self.session_id} not found for tracing")
            
            # Créer une nouvelle étape de trace
            trace_step = TraceStep(
                timestamp=datetime.now(),
                component=component,
                event=event,
                details=details or {}
            )
            
            # Ajouter l'étape à la trace de la session
            session.trace.append(trace_step)
            
            # Sauvegarder la session mise à jour
            await self.session_manager.save_session(session)
            
            # JALON 4.3: Collecte de métriques Prometheus en parallèle du traçage
            self._collect_metrics_from_trace_step(component, event, details or {})
            
            # Log pour le développement (avec masquage des données sensibles)
            safe_details = self._sanitize_details_for_logging(details or {})
            self.logger.debug(
                f"Trace step recorded: {component}.{event} - {safe_details}"
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to log trace step {component}.{event}: {str(e)}"
            )
            # Ne pas lever l'exception pour ne pas casser le flux principal
            # Le tracing est auxiliaire, pas critique
    
    async def log_router_start(self, request_summary: str) -> None:
        """Log le début du processus de routage"""
        await self.log_step(
            component="AgentRouter",
            event="routing_start",
            details={"request_summary": request_summary}
        )
    
    async def log_router_decision(self, agent_name: str, confidence: float = None) -> None:
        """Log la décision de routage"""
        details = {"selected_agent": agent_name}
        if confidence is not None:
            details["confidence"] = confidence
            
        await self.log_step(
            component="AgentRouter",
            event="routing_decision",
            details=details
        )
    
    async def log_orchestration_start(self, agent_name: str, iteration: int = 1) -> None:
        """Log le début d'une itération d'orchestration"""
        await self.log_step(
            component="AgentOrchestrator",
            event="orchestration_start",
            details={"agent_name": agent_name, "iteration": iteration}
        )
    
    async def log_llm_call(self, provider: str, model: str, prompt_length: int) -> None:
        """Log un appel LLM"""
        await self.log_step(
            component="LLM",
            event="llm_call",
            details={
                "provider": provider,
                "model": model,
                "prompt_length": prompt_length
            }
        )
    
    async def log_llm_response(self, provider: str, response_length: int, tools_called: int = 0) -> None:
        """Log la réponse d'un LLM"""
        await self.log_step(
            component="LLM",
            event="llm_response",
            details={
                "provider": provider,
                "response_length": response_length,
                "tools_called": tools_called
            }
        )
    
    async def log_tool_execution(self, tool_name: str, success: bool, execution_time: float = None) -> None:
        """Log l'exécution d'un outil"""
        details = {"tool_name": tool_name, "success": success}
        if execution_time is not None:
            details["execution_time_ms"] = execution_time
            
        await self.log_step(
            component="ToolExecutor",
            event="tool_execution",
            details=details
        )
    
    async def log_summarization_trigger(self, reason: str, metrics: Dict[str, int]) -> None:
        """Log le déclenchement de la synthèse d'historique"""
        await self.log_step(
            component="HistorySummarizer",
            event="summarization_triggered",
            details={"reason": reason, "metrics": metrics}
        )
    
    async def log_summarization_complete(self, summary_length: int, original_messages: int) -> None:
        """Log la completion de la synthèse"""
        await self.log_step(
            component="HistorySummarizer",
            event="summarization_complete",
            details={
                "summary_length": summary_length,
                "original_messages": original_messages
            }
        )
    
    async def log_error(self, component: str, error_type: str, error_message: str) -> None:
        """Log une erreur dans le flux"""
        await self.log_step(
            component=component,
            event="error",
            details={
                "error_type": error_type,
                "error_message": error_message
            }
        )
    
    async def log_final_response(self, response_length: int, total_steps: int) -> None:
        """Log la réponse finale de l'orchestration"""
        await self.log_step(
            component="AgentOrchestrator",
            event="final_response",
            details={
                "response_length": response_length,
                "total_trace_steps": total_steps
            }
        )
    
    def _collect_metrics_from_trace_step(
        self, 
        component: str, 
        event: str, 
        details: Dict[str, Any]
    ) -> None:
        """
        Collecte les métriques Prometheus à partir d'une étape de trace (JALON 4.3)
        
        Cette méthode analyse les événements de trace et enregistre les métriques
        correspondantes dans le collecteur Prometheus pour l'observabilité.
        
        Args:
            component: Composant source de l'événement
            event: Type d'événement
            details: Détails de l'événement
        """
        try:
            metrics_collector = get_metrics_collector()
            
            # ===================================================================
            # MÉTRIQUES LLM
            # ===================================================================
            
            if event == "llm_call" and component in ["AgentOrchestrator", "ResilientLLMService"]:
                provider = details.get("provider", "unknown")
                model = details.get("model", "unknown")
                
                # Estimer la durée si on a des informations de latence
                if "prompt_length" in details:
                    # Estimation basique : 1s pour 1000 caractères de prompt
                    estimated_duration = details["prompt_length"] / 1000.0
                    metrics_collector.record_llm_call(
                        provider=provider,
                        model=model,
                        duration_seconds=estimated_duration,
                        status="initiated"
                    )
            
            elif event == "llm_call_success":
                provider = details.get("provider", "unknown")
                model = details.get("model", "unknown")
                response_length = details.get("response_length", 0)
                
                # Estimation de durée basée sur la longueur de réponse
                estimated_duration = max(0.5, response_length / 500.0)  # Min 0.5s
                
                metrics_collector.record_llm_call(
                    provider=provider,
                    model=model,
                    duration_seconds=estimated_duration,
                    status="success"
                )
            
            # ===================================================================
            # MÉTRIQUES ERREURS
            # ===================================================================
            
            elif event in ["retry_attempt_failed", "max_retries_exceeded"] and component == "ResilientLLMService":
                error_type = details.get("error_type", "unknown")
                metrics_collector.record_orchestrator_error(
                    error_type=error_type,
                    component=component
                )
            
            elif "error" in event.lower():
                error_type = details.get("error_type", event)
                metrics_collector.record_orchestrator_error(
                    error_type=error_type,
                    component=component
                )
            
            # ===================================================================
            # MÉTRIQUES RETRY
            # ===================================================================
            
            elif event == "retry_attempt_start" and component == "ResilientLLMService":
                provider = details.get("provider", "unknown")
                attempt = details.get("attempt", 1)
                
                metrics_collector.record_retry_attempt(
                    provider=provider,
                    attempt_number=attempt,
                    final_status="in_progress"
                )
            
            # ===================================================================
            # MÉTRIQUES OUTILS
            # ===================================================================
            
            elif event == "tool_execution" and component == "AgentOrchestrator":
                tool_name = details.get("tool_name", "unknown")
                # Estimation de durée d'exécution d'outil
                estimated_duration = 0.1  # 100ms par défaut
                
                metrics_collector.record_tool_execution(
                    tool_name=tool_name,
                    duration_seconds=estimated_duration,
                    status="success"
                )
            
            # ===================================================================
            # MÉTRIQUES ORCHESTRATION
            # ===================================================================
            
            elif event == "orchestration_start":
                agent_name = details.get("agent_name", "unknown")
                # La durée sera calculée lors du final_response
                
            elif event == "final_response":
                agent_name = details.get("agent_name", "unknown") 
                total_steps = details.get("total_steps", 1)
                
                # Estimation de durée basée sur le nombre d'étapes
                estimated_duration = total_steps * 2.0  # 2s par étape
                
                metrics_collector.record_orchestration_duration(
                    agent_name=agent_name,
                    duration_seconds=estimated_duration,
                    status="success"
                )
            
        except Exception as e:
            # Ne pas faire échouer le traçage si la collecte de métriques échoue
            logger.warning(f"Failed to collect metrics from trace step: {str(e)}")
    
    def _sanitize_details_for_logging(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie les détails pour le logging en masquant les données sensibles
        
        Args:
            details: Détails originaux
            
        Returns:
            Dict avec données sensibles masquées
        """
        sanitized = {}
        sensitive_keys = {'api_key', 'password', 'token', 'secret', 'credential'}
        
        for key, value in details.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "***MASKED***"
            elif isinstance(value, str) and len(value) > 100:
                # Tronquer les chaînes très longues
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
                
        return sanitized


class TracerFactory:
    """Factory pour créer des instances de Tracer"""
    
    @staticmethod
    def create_tracer(session_id: UUID, session_manager: SessionManager) -> Tracer:
        """
        Crée une nouvelle instance de Tracer
        
        Args:
            session_id: UUID de la session
            session_manager: Manager pour la persistance
            
        Returns:
            Instance de Tracer configurée
        """
        return Tracer(session_id, session_manager)