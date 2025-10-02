"""Interface LLM Service - Contrat pour tous les fournisseurs LLM"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.models.data_contracts import ChatMessage, ChatResponse


class LLMServiceInterface(ABC):
    """Interface abstraite pour tous les services LLM"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> ChatResponse:
        """
        Génère une réponse de chat completion
        
        Args:
            messages: Liste des messages de conversation
            model: Nom du modèle à utiliser (optionnel)
            max_tokens: Nombre maximum de tokens (optionnel)
            temperature: Température pour la génération (optionnel)
            
        Returns:
            ChatResponse: Réponse générée par le LLM
            
        Raises:
            Exception: En cas d'erreur lors de la génération
        """
        pass

    @abstractmethod
    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """
        Génère une réponse simple à partir d'un prompt
        
        Args:
            prompt: Prompt d'entrée
            **kwargs: Arguments additionnels
            
        Returns:
            str: Réponse générée
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Retourne le nom du fournisseur
        
        Returns:
            str: Nom du fournisseur (ex: "openai", "anthropic")
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Retourne la liste des modèles disponibles
        
        Returns:
            List[str]: Liste des noms de modèles
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Vérifie si le service est opérationnel
        
        Returns:
            bool: True si le service est disponible
        """
        pass