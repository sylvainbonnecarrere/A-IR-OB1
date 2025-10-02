"""Factory Pattern pour les Services LLM"""

from typing import Dict, Type, Optional
from src.domain.llm_service_interface import LLMServiceInterface
from src.infrastructure.llm_providers.openai_adapter import OpenAIAdapter
from src.models.data_contracts import LLMProvider


class LLMServiceFactory:
    """Factory pour créer des instances de services LLM"""

    # Registry des adaptateurs disponibles
    _providers: Dict[str, Type[LLMServiceInterface]] = {
        LLMProvider.OPENAI.value: OpenAIAdapter,
        # Futurs adaptateurs à ajouter ici
        # LLMProvider.ANTHROPIC.value: AnthropicAdapter,
        # LLMProvider.GEMINI.value: GeminiAdapter,
    }

    # Cache des instances créées
    _instances: Dict[str, LLMServiceInterface] = {}

    @classmethod
    def create_service(
        self, 
        provider: str, 
        use_cache: bool = True,
        **kwargs
    ) -> LLMServiceInterface:
        """
        Crée une instance de service LLM
        
        Args:
            provider: Nom du fournisseur (openai, anthropic, etc.)
            use_cache: Utiliser le cache d'instances
            **kwargs: Arguments pour l'initialisation du service
            
        Returns:
            LLMServiceInterface: Instance du service
            
        Raises:
            ValueError: Si le fournisseur n'est pas supporté
        """
        if provider not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Provider '{provider}' not supported. Available: {available}")

        # Vérification du cache
        cache_key = f"{provider}_{hash(frozenset(kwargs.items()))}"
        if use_cache and cache_key in self._instances:
            return self._instances[cache_key]

        # Création de l'instance
        adapter_class = self._providers[provider]
        instance = adapter_class(**kwargs)

        # Mise en cache
        if use_cache:
            self._instances[cache_key] = instance

        return instance

    @classmethod
    def get_default_service(self, **kwargs) -> LLMServiceInterface:
        """
        Retourne le service par défaut (OpenAI)
        
        Args:
            **kwargs: Arguments pour l'initialisation
            
        Returns:
            LLMServiceInterface: Service par défaut
        """
        return self.create_service(LLMProvider.OPENAI.value, **kwargs)

    @classmethod
    def get_available_providers(self) -> list[str]:
        """
        Retourne la liste des fournisseurs disponibles
        
        Returns:
            list[str]: Liste des noms de fournisseurs
        """
        return list(self._providers.keys())

    @classmethod
    def register_provider(
        self, 
        name: str, 
        adapter_class: Type[LLMServiceInterface]
    ) -> None:
        """
        Enregistre un nouveau fournisseur
        
        Args:
            name: Nom du fournisseur
            adapter_class: Classe de l'adaptateur
        """
        self._providers[name] = adapter_class

    @classmethod
    def clear_cache(self) -> None:
        """Vide le cache des instances"""
        self._instances.clear()

    @classmethod
    def get_provider_info(self) -> Dict[str, Dict]:
        """
        Retourne les informations sur tous les fournisseurs
        
        Returns:
            Dict: Informations détaillées des fournisseurs
        """
        info = {}
        for name, adapter_class in self._providers.items():
            try:
                # Créer une instance temporaire pour obtenir les infos
                temp_instance = adapter_class()
                info[name] = {
                    "available_models": temp_instance.get_available_models(),
                    "is_healthy": temp_instance.is_healthy(),
                    "class": adapter_class.__name__
                }
            except Exception:
                info[name] = {
                    "available_models": [],
                    "is_healthy": False,
                    "class": adapter_class.__name__,
                    "error": "Failed to initialize"
                }
        return info