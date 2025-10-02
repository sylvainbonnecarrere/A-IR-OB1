"""Dependency Injection pour FastAPI"""

from typing import Optional
from fastapi import Depends, HTTPException
from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.llm_service_factory import LLMServiceFactory
from src.models.data_contracts import LLMProvider


def get_llm_service_from_config(
    provider: Optional[str] = None
) -> LLMServiceInterface:
    """
    Dependency pour obtenir un service LLM basé sur la configuration
    
    Args:
        provider: Fournisseur LLM optionnel
        
    Returns:
        LLMServiceInterface: Instance du service LLM
        
    Raises:
        HTTPException: Si le fournisseur n'est pas disponible
    """
    try:
        if provider:
            return LLMServiceFactory.create_service(provider)
        else:
            return LLMServiceFactory.get_default_service()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create LLM service: {str(e)}")


def get_default_llm_service() -> LLMServiceInterface:
    """
    Dependency pour obtenir le service LLM par défaut
    
    Returns:
        LLMServiceInterface: Service par défaut (OpenAI)
    """
    return get_llm_service_from_config()


def get_openai_service() -> LLMServiceInterface:
    """
    Dependency pour obtenir spécifiquement le service OpenAI
    
    Returns:
        LLMServiceInterface: Service OpenAI
    """
    return get_llm_service_from_config(LLMProvider.OPENAI.value)


# Types pour l'injection de dépendances
DefaultLLMService = Depends(get_default_llm_service)
OpenAIService = Depends(get_openai_service)


class LLMServiceProvider:
    """Fournisseur de services LLM avec configuration avancée"""
    
    def __init__(self, default_provider: str = LLMProvider.OPENAI.value):
        self.default_provider = default_provider
    
    def get_service(self, provider: Optional[str] = None) -> LLMServiceInterface:
        """
        Obtient un service LLM
        
        Args:
            provider: Fournisseur spécifique ou None pour le défaut
            
        Returns:
            LLMServiceInterface: Instance du service
        """
        return LLMServiceFactory.create_service(
            provider or self.default_provider
        )
    
    def get_all_services(self) -> dict[str, LLMServiceInterface]:
        """
        Obtient tous les services LLM disponibles
        
        Returns:
            dict: Dictionnaire provider -> service
        """
        services = {}
        for provider in LLMServiceFactory.get_available_providers():
            try:
                services[provider] = LLMServiceFactory.create_service(provider)
            except Exception:
                # Ignorer les services non configurés
                pass
        return services


# Instance globale du fournisseur
llm_provider = LLMServiceProvider()