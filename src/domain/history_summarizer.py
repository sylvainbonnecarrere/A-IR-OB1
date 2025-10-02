"""
History Summarizer - Service de Synthèse Automatique de l'Historique

Ce module implémente la logique de synthèse automatique des conversations longues
pour maintenir une mémoire à long terme efficace tout en préservant les performances.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.llm_service_factory import LLMServiceFactory
from src.domain.tracer import Tracer  # JALON 4.1-B: Intégration du traçage
from src.models.data_contracts import (
    Session,
    HistoryConfig,
    ChatMessage,
    AgentConfig,
    OrchestrationRequest,
    SessionManager
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistorySummarizer:
    """
    Service de synthèse automatique de l'historique de conversation
    
    Ce service analyse l'historique d'une session et déclenche automatiquement
    une synthèse lorsque les seuils configurés sont dépassés, remplaçant
    l'historique long par un résumé concis.
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialise le service de synthèse
        
        Args:
            session_manager: Manager pour la persistance des sessions
        """
        self.session_manager = session_manager
    
    async def summarize_if_needed(self, session: Session, tracer: Optional[Tracer] = None) -> Session:
        """
        Vérifie et effectue la synthèse de l'historique si nécessaire
        
        Cette méthode constitue le cœur de la mémoire à long terme :
        1. Calcule les métriques de l'historique actuel
        2. Vérifie si les seuils sont dépassés
        3. Si oui, synthétise l'historique via un LLM spécialisé
        4. Remplace l'historique par le résumé + dernier message utilisateur
        5. Sauvegarde la session mise à jour
        
        Args:
            session: Session à analyser et potentiellement synthétiser
            
        Returns:
            Session: Session mise à jour (synthétisée ou inchangée)
        """
        if not session.history_config.enabled:
            logger.debug(f"Synthèse désactivée pour session {session.session_id}")
            return session
        
        # Vérification des seuils
        if not session.should_trigger_summarization():
            logger.debug(f"Seuils non atteints pour session {session.session_id}")
            return session
        
        # Calcul des métriques pour le logging
        metrics = session.get_history_metrics()
        logger.info(f"Déclenchement synthèse pour session {session.session_id}")
        logger.info(f"Métriques: {metrics}")
        
        # JALON 4.1-B: Traçage du début de synthèse
        if tracer:
            await tracer.log_step(
                component="HistorySummarizer",
                event="summarization_start",
                details={
                    "session_id": session.session_id,
                    "messages_count": metrics['messages'],
                    "tokens_count": metrics['tokens']
                }
            )
        
        try:
            # Synthèse de l'historique
            summary_message = await self._create_summary(session, tracer)
            
            # Préservation du dernier message utilisateur
            last_user_message = self._get_last_user_message(session.history)
            
            # Remplacement de l'historique
            new_history = [summary_message]
            if last_user_message:
                new_history.append(last_user_message)
            
            session.history = new_history
            session.updated_at = datetime.now().isoformat()
            
            # Sauvegarde de la session mise à jour
            await self.session_manager.save_session(session)
            
            logger.info(f"Synthèse réussie pour session {session.session_id}")
            logger.info(f"Historique réduit de {metrics['messages']} à {len(new_history)} messages")
            
            # JALON 4.1-B: Traçage de la synthèse réussie
            if tracer:
                await tracer.log_step(
                    component="HistorySummarizer",
                    event="summarization_success",
                    details={
                        "session_id": session.session_id,
                        "original_messages": metrics['messages'],
                        "new_messages": len(new_history),
                        "summary_length": len(summary_message.content)
                    }
                )
            
            return session
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse pour session {session.session_id}: {str(e)}")
            
            # JALON 4.1-B: Traçage des erreurs de synthèse
            if tracer:
                await tracer.log_error(
                    error_type="SUMMARIZATION_ERROR",
                    error_message=str(e)
                )
            
            # En cas d'erreur, on retourne la session inchangée
            return session
    
    async def _create_summary(self, session: Session, tracer: Optional[Tracer] = None) -> ChatMessage:
        """
        Génère le résumé de l'historique via un LLM de synthèse
        
        Args:
            session: Session contenant l'historique à synthétiser
            
        Returns:
            ChatMessage: Message de résumé créé par le LLM
            
        Raises:
            Exception: En cas d'erreur lors de l'appel au LLM
        """
        # Création du service LLM de synthèse
        summarizer_service = LLMServiceFactory.create_service(
            session.history_config.llm_provider
        )
        
        # Construction du prompt de synthèse
        history_text = self._format_history_for_summary(session.history)
        
        summary_messages = [
            ChatMessage(
                role="system", 
                content=session.history_config.system_prompt
            ),
            ChatMessage(
                role="user",
                content=f"Voici l'historique de conversation à synthétiser :\n\n{history_text}\n\nCrée un résumé concis qui préserve le contexte essentiel pour la suite de la conversation."
            )
        ]
        
        # Configuration pour la synthèse
        summary_config = AgentConfig(
            provider=session.history_config.llm_provider,
            model_version=session.history_config.model_version,
            temperature=0.3,  # Température basse pour cohérence
            max_tokens=1000,  # Résumé concis
            tools_enabled=False,  # Pas d'outils pour la synthèse
            system_prompt=session.history_config.system_prompt
        )
        
        # Requête de synthèse
        summary_request = OrchestrationRequest(
            message="",  # Message vide, tout est dans l'historique
            agent_config=summary_config,
            conversation_history=summary_messages
        )
        
        # Appel au LLM de synthèse
        response = await summarizer_service.orchestration_completion(summary_request)
        
        if not response.content:
            raise Exception("Le LLM de synthèse n'a pas généré de contenu")
        
        # Création du message de résumé
        summary_message = ChatMessage(
            role="assistant",
            content=f"[RÉSUMÉ AUTOMATIQUE] {response.content}"
        )
        
        return summary_message
    
    def _format_history_for_summary(self, history: list[ChatMessage]) -> str:
        """
        Formate l'historique pour le prompt de synthèse
        
        Args:
            history: Liste des messages à formater
            
        Returns:
            str: Historique formaté pour la synthèse
        """
        if not history:
            return "Aucun historique disponible."
        
        formatted_lines = []
        for i, message in enumerate(history, 1):
            role_emoji = {
                "user": "👤",
                "assistant": "🤖", 
                "system": "⚙️",
                "tool": "🔧"
            }.get(message.role, "❓")
            
            content = message.content or "[Contenu vide]"
            formatted_lines.append(f"{i}. {role_emoji} {message.role.upper()}: {content}")
        
        return "\n".join(formatted_lines)
    
    def _get_last_user_message(self, history: list[ChatMessage]) -> Optional[ChatMessage]:
        """
        Récupère le dernier message utilisateur de l'historique
        
        Args:
            history: Historique de conversation
            
        Returns:
            Optional[ChatMessage]: Dernier message utilisateur ou None
        """
        # Parcours en sens inverse pour trouver le dernier message utilisateur
        for message in reversed(history):
            if message.role == "user":
                return message
        return None
    
    def get_summarization_stats(self, session: Session) -> Dict[str, Any]:
        """
        Calcule des statistiques sur l'état de synthèse d'une session
        
        Args:
            session: Session à analyser
            
        Returns:
            Dict: Statistiques de synthèse
        """
        metrics = session.get_history_metrics()
        config = session.history_config
        
        return {
            "session_id": str(session.session_id),
            "summarization_enabled": config.enabled,
            "current_metrics": metrics,
            "thresholds": {
                "messages": config.message_threshold,
                "chars": config.char_threshold, 
                "words": config.word_threshold,
                "tokens": config.token_threshold
            },
            "threshold_status": {
                "messages": f"{metrics['messages']}/{config.message_threshold} ({'✅' if metrics['messages'] >= config.message_threshold else '⏳'})",
                "chars": f"{metrics['chars']}/{config.char_threshold} ({'✅' if metrics['chars'] >= config.char_threshold else '⏳'})",
                "words": f"{metrics['words']}/{config.word_threshold} ({'✅' if metrics['words'] >= config.word_threshold else '⏳'})",
                "tokens": f"{metrics['estimated_tokens']}/{config.token_threshold} ({'✅' if metrics['estimated_tokens'] >= config.token_threshold else '⏳'})"
            },
            "should_summarize": session.should_trigger_summarization(),
            "has_summary": any("[RÉSUMÉ AUTOMATIQUE]" in (msg.content or "") for msg in session.history)
        }