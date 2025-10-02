"""Adaptateur Grok - Implémentation de l'interface LLM pour xAI Grok (OpenAI-compatible)"""

import os
import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from src.domain.llm_service_interface import LLMServiceInterface
from src.models.data_contracts import (
    ChatMessage, ChatResponse, ToolDefinition, ToolCall, 
    OrchestrationRequest, OrchestrationResponse
)
from src.infrastructure.secure_api_key_handler import (
    SecureAPIKeyHandler, ProviderType, APIKeyError
)

logger = logging.getLogger(__name__)


class GrokAdapter(LLMServiceInterface):
    """Adaptateur pour l'API xAI Grok (compatible OpenAI) avec sécurisation des clés API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'adaptateur Grok avec validation sécurisée des clés API
        
        Args:
            api_key: Clé API xAI (optionnel, peut être définie via GROK_API_KEY)
            
        Raises:
            APIKeyError: Si la clé API est manquante ou invalide
        """
        try:
            # Validation sécurisée de la clé API
            raw_key = api_key or os.getenv("GROK_API_KEY")
            self.secure_handler = SecureAPIKeyHandler()
            self.api_key = self.secure_handler.validate_api_key(raw_key, ProviderType.GROK)
            
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1"
            )
            self.default_model = "grok-3-latest"
            
            logger.info(f"Grok adapter initialized with key: {self.secure_handler.mask_api_key(self.api_key)}")
            
        except APIKeyError as e:
            logger.error(f"Failed to initialize Grok adapter: {e}")
            raise

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_version: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ChatResponse:
        """Génère une réponse via l'API Grok avec support des outils (limité selon la doc)"""
        if not self.client:
            logger.error(f"Grok client not initialized - key: {self.secure_handler.mask_api_key(self.api_key) if hasattr(self, 'secure_handler') else 'MISSING'}")
            raise APIKeyError("Grok API key not configured")

        # Conversion des messages Pydantic vers le format OpenAI
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Paramètres de la requête
        params = {
            "model": model_version,
            "messages": openai_messages,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature
            
        # Note: Selon la doc, Grok ne supporte pas le Function Calling
        # Mais on garde l'interface cohérente pour l'extensibilité future
        if tools:
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                # Grok ne supporte pas les tools selon la doc
                # On pourrait les ignorer ou lever un warning
                print("Warning: Grok ne supporte pas le Function Calling selon la documentation")

        try:
            response = await self.client.chat.completions.create(**params)
            
            return ChatResponse(
                content=response.choices[0].message.content,
                provider=self.get_provider_name(),
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            )
        except Exception as e:
            raise Exception(f"Grok API error: {str(e)}")

    async def format_tools_for_llm(self, tool_definitions: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convertit nos ToolDefinition internes vers le format OpenAI (pour compatibilité future)
        
        Note: Grok ne supporte pas le Function Calling selon la documentation actuelle,
        mais on maintient l'interface pour la cohérence et l'extensibilité future.
        
        Args:
            tool_definitions: Liste des définitions d'outils internes
            
        Returns:
            Liste des outils au format OpenAI (non utilisée par Grok actuellement)
        """
        formatted_tools = []
        
        for tool in tool_definitions:
            try:
                # Format OpenAI standard (même si non supporté par Grok actuellement)
                tool_schema = tool.get_tool_schema()
                formatted_tools.append(tool_schema)
            except Exception as e:
                # Log l'erreur mais continue avec les autres outils
                print(f"Erreur lors du formatage de l'outil {tool.name}: {e}")
                continue
                
        return formatted_tools

    async def orchestration_completion(
        self,
        request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """
        Méthode d'orchestration complète (sans support des outils pour Grok)
        
        Args:
            request: Requête d'orchestration avec configuration et outils
            
        Returns:
            Réponse d'orchestration sans appels d'outils
        """
        if not self.client:
            raise Exception("Grok API key not configured")

        # Construire les messages avec l'historique
        messages = list(request.conversation_history)
        messages.append(ChatMessage(role="user", content=request.message))

        # Conversion des messages Pydantic vers le format OpenAI
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Paramètres de base
        params = {
            "model": request.agent_config.model_version,
            "messages": openai_messages,
            "max_tokens": request.agent_config.max_tokens,
            "temperature": request.agent_config.temperature,
        }

        # Note: Grok ne supporte pas les outils selon la documentation
        if request.agent_config.tools_enabled and request.agent_config.available_tools:
            print("Warning: Grok ne supporte pas le Function Calling - les outils seront ignorés")

        try:
            response = await self.client.chat.completions.create(**params)
            message = response.choices[0].message

            # Pas de tool calls pour Grok
            tool_calls = []
            requires_tool_execution = False

            return OrchestrationResponse(
                content=message.content,
                tool_calls=tool_calls,
                provider=self.get_provider_name(),
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                requires_tool_execution=requires_tool_execution
            )
        except Exception as e:
            raise Exception(f"Grok API error: {str(e)}")

    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """Génère une réponse simple à partir d'un prompt"""
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, **kwargs)
        return response.content

    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        return "grok"

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles Grok disponibles"""
        return [
            "grok-3-latest",
            "grok-vision-latest",
            "grok-2-image"
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le service Grok est disponible"""
        return self.client is not None and self.api_key is not None

    def get_model_name(self) -> str:
        """Retourne le nom du modèle par défaut"""
        return self.default_model