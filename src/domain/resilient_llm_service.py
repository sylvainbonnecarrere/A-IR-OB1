"""
Service de Résilience LLM avec Retry et Backoff (JALON 4.2)

Ce module implémente un service d'enveloppement autour des services LLM existants
pour fournir une résilience aux erreurs temporaires via un pattern de retry 
avec backoff exponentiel configurable.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Type
from datetime import datetime

from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.llm_service_factory import LLMServiceFactory
from src.domain.tracer import Tracer
from src.models.data_contracts import (
    AgentConfig, 
    RetryConfig, 
    OrchestrationRequest, 
    OrchestrationResponse,
    AgentExecutionError
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResilientLLMService:
    """
    Service de résilience pour les appels LLM avec retry et backoff (JALON 4.2)
    
    Ce service encapsule les appels LLM avec une logique de retry configurable,
    un backoff exponentiel et un traçage complet via le Tracer.
    
    Fonctionnalités:
    - Retry configurable par agent via RetryConfig
    - Backoff exponentiel: delay_base * (2 ** (attempt - 1))
    - Traçage de chaque tentative, délai et résultat
    - Gestion d'erreurs finales sécurisée
    """
    
    def __init__(self, tracer: Optional[Tracer] = None):
        """
        Initialise le service résilient
        
        Args:
            tracer: Instance de tracer pour l'observabilité (optionnel)
        """
        self.tracer = tracer
        
        # Définition des erreurs temporaires qui justifient un retry
        self.retriable_errors = (
            # Erreurs de réseau temporaires
            ConnectionError,
            TimeoutError,
            # Erreurs HTTP temporaires (seront étendues selon les besoins)
            Exception  # Pour l'instant, on considère toutes les exceptions comme retriables
        )
    
    async def resilient_chat_completion(
        self, 
        config: AgentConfig, 
        request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """
        Effectue un appel LLM résilient avec retry et backoff
        
        Args:
            config: Configuration d'agent incluant RetryConfig
            request: Requête d'orchestration
            
        Returns:
            Réponse d'orchestration réussie
            
        Raises:
            AgentExecutionError: Après épuisement des tentatives de retry
        """
        retry_config = config.retry_config
        llm_service = None
        last_error = None
        
        for attempt in range(1, retry_config.max_attempts + 1):
            try:
                # Traçage du début de tentative
                if self.tracer:
                    await self.tracer.log_step(
                        component="ResilientLLMService",
                        event="retry_attempt_start",
                        details={
                            "attempt": attempt,
                            "max_attempts": retry_config.max_attempts,
                            "provider": config.provider.value if config.provider else "unknown"
                        }
                    )
                
                # Création du service LLM pour cette tentative
                if llm_service is None:
                    llm_service = LLMServiceFactory.create_service(config.provider)
                
                logger.info(f"🔄 Tentative {attempt}/{retry_config.max_attempts} - Appel LLM {config.provider.value}")
                
                # Appel LLM réel
                response = await llm_service.orchestration_completion(request)
                
                # Succès - Traçage et retour
                if self.tracer:
                    await self.tracer.log_step(
                        component="ResilientLLMService",
                        event="llm_call_success",
                        details={
                            "attempt": attempt,
                            "provider": config.provider.value if config.provider else "unknown",
                            "response_length": len(response.content) if response.content else 0
                        }
                    )
                
                logger.info(f"✅ Appel LLM réussi à la tentative {attempt}")
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Échec tentative {attempt}/{retry_config.max_attempts}: {str(e)}")
                
                # Traçage de l'échec
                if self.tracer:
                    await self.tracer.log_step(
                        component="ResilientLLMService",
                        event="retry_attempt_failed",
                        details={
                            "attempt": attempt,
                            "error_type": type(e).__name__,
                            "error_message": str(e)[:200]  # Limiter la taille pour la sécurité
                        }
                    )
                
                # Si c'est la dernière tentative, ne pas attendre
                if attempt >= retry_config.max_attempts:
                    break
                
                # Calcul du délai de backoff exponentiel
                delay = retry_config.delay_base * (2 ** (attempt - 1))
                
                # Traçage du délai
                if self.tracer:
                    await self.tracer.log_step(
                        component="ResilientLLMService",
                        event="retry_backoff_delay",
                        details={
                            "delay_seconds": delay,
                            "attempt": attempt,
                            "backoff_formula": f"{retry_config.delay_base} * (2 ** {attempt - 1})"
                        }
                    )
                
                logger.info(f"⏳ Attente de {delay:.1f}s avant la tentative {attempt + 1}")
                await asyncio.sleep(delay)
        
        # Toutes les tentatives ont échoué - Gestion d'erreur finale
        error_message = self._create_safe_error_message(last_error, retry_config.max_attempts)
        
        # Traçage de l'échec final
        if self.tracer:
            await self.tracer.log_step(
                component="ResilientLLMService",
                event="max_retries_exceeded",
                details={
                    "max_attempts": retry_config.max_attempts,
                    "final_error_type": type(last_error).__name__ if last_error else "Unknown",
                    "safe_error_message": error_message
                }
            )
        
        logger.error(f"❌ Échec définitif après {retry_config.max_attempts} tentatives")
        
        # Lever une exception sécurisée
        raise AgentExecutionError(
            message=error_message,
            original_error=last_error,
            attempts=retry_config.max_attempts
        )
    
    def _create_safe_error_message(self, error: Optional[Exception], attempts: int) -> str:
        """
        Crée un message d'erreur sécurisé sans fuite d'informations sensibles
        
        Args:
            error: Erreur originale
            attempts: Nombre de tentatives effectuées
            
        Returns:
            Message d'erreur sécurisé pour l'utilisateur
        """
        if error is None:
            return f"Service LLM indisponible après {attempts} tentatives"
        
        error_type = type(error).__name__
        
        # Messages sécurisés selon le type d'erreur
        safe_messages = {
            "ConnectionError": "Erreur de connexion au service LLM",
            "TimeoutError": "Délai d'attente dépassé pour le service LLM",
            "HTTPException": "Erreur de communication avec le service LLM",
            "ValueError": "Erreur de configuration ou de données",
            "KeyError": "Erreur de configuration manquante",
        }
        
        base_message = safe_messages.get(error_type, "Erreur technique du service LLM")
        
        return f"{base_message} (après {attempts} tentatives)"
    
    def is_retriable_error(self, error: Exception) -> bool:
        """
        Détermine si une erreur justifie une nouvelle tentative
        
        Args:
            error: Exception à analyser
            
        Returns:
            True si l'erreur est considérée comme temporaire
        """
        # Pour l'instant, considérer la plupart des erreurs comme retriables
        # À affiner selon les types d'erreurs spécifiques des APIs LLM
        return isinstance(error, self.retriable_errors)


class ResilientServiceFactory:
    """
    Factory pour créer des services résilients avec traçage
    """
    
    @staticmethod
    def create_resilient_service(tracer: Optional[Tracer] = None) -> ResilientLLMService:
        """
        Crée une instance de service résilient
        
        Args:
            tracer: Instance de tracer (optionnel)
            
        Returns:
            Service résilient configuré
        """
        return ResilientLLMService(tracer=tracer)