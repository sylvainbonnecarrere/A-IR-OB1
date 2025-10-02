"""Adaptateur Mistral - Implémentation de l'interface LLM pour Mistral avec Function Calling"""

import os
import logging
from typing import List, Optional, Dict, Any
from mistralai.client import MistralClient
from src.domain.llm_service_interface import LLMServiceInterface
from src.models.data_contracts import (
    ChatMessage, ChatResponse, ToolDefinition, ToolCall, 
    OrchestrationRequest, OrchestrationResponse
)
from src.infrastructure.secure_api_key_handler import (
    SecureAPIKeyHandler, ProviderType, APIKeyError
)

logger = logging.getLogger(__name__)


class MistralAdapter(LLMServiceInterface):
    """Adaptateur pour l'API Mistral avec sécurisation des clés API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'adaptateur Mistral avec validation sécurisée des clés API
        
        Args:
            api_key: Clé API Mistral (optionnel, peut être définie via MISTRAL_API_KEY)
            
        Raises:
            APIKeyError: Si la clé API est manquante ou invalide
        """
        try:
            # Validation sécurisée de la clé API
            raw_key = api_key or os.getenv("MISTRAL_API_KEY")
            self.secure_handler = SecureAPIKeyHandler()
            self.api_key = self.secure_handler.validate_api_key(raw_key, ProviderType.MISTRAL)
            
            self.client = MistralClient(api_key=self.api_key)
            self.default_model = "mistral-large-latest"
            
            logger.info(f"Mistral adapter initialized with key: {self.secure_handler.mask_api_key(self.api_key)}")
            
        except APIKeyError as e:
            logger.error(f"Failed to initialize Mistral adapter: {e}")
            raise

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_version: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ChatResponse:
        """Génère une réponse via l'API Mistral avec support des outils"""
        if not self.client:
            logger.error(f"Mistral client not initialized - key: {self.secure_handler.mask_api_key(self.api_key) if hasattr(self, 'secure_handler') else 'MISSING'}")
            raise APIKeyError("Mistral API key not configured")

        # Conversion des messages vers le format Mistral
        mistral_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Paramètres de base
        params = {
            "model": model_version,
            "messages": mistral_messages,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature

        # Ajout des outils si fournis
        if tools:
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                params["tools"] = formatted_tools

        try:
            response = self.client.chat(**params)
            
            # Extraction du contenu de la réponse
            content = ""
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content
                else:
                    content = str(choice)
            else:
                content = str(response)
            
            return ChatResponse(
                content=content,
                provider=self.get_provider_name(),
                model=response.model if hasattr(response, 'model') else model_version,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None
                } if hasattr(response, 'usage') else None
            )
        except Exception as e:
            raise Exception(f"Mistral API error: {str(e)}")

    async def format_tools_for_llm(self, tool_definitions: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convertit nos ToolDefinition internes vers le format Mistral
        
        Selon la doc Mistral, le format est identique à OpenAI:
        [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Obtient la météo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }]
        
        Args:
            tool_definitions: Liste des définitions d'outils internes
            
        Returns:
            Liste des outils au format Mistral
        """
        formatted_tools = []
        
        for tool in tool_definitions:
            try:
                # Récupérer le schéma de l'outil (déjà au format OpenAI)
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
        Méthode d'orchestration complète avec support des outils
        
        Args:
            request: Requête d'orchestration avec configuration et outils
            
        Returns:
            Réponse d'orchestration avec éventuels appels d'outils
        """
        if not self.client:
            raise Exception("Mistral API key not configured")

        # Construire les messages avec l'historique
        messages = list(request.conversation_history)
        messages.append(ChatMessage(role="user", content=request.message))

        # Conversion des messages vers le format Mistral
        mistral_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Paramètres de base
        params = {
            "model": request.agent_config.model_version,
            "messages": mistral_messages,
            "max_tokens": request.agent_config.max_tokens,
            "temperature": request.agent_config.temperature,
        }

        # Ajout des outils si activés
        if request.agent_config.tools_enabled and request.agent_config.available_tools:
            # Pour cette démo, on utilise GetCurrentTimeTool
            from src.models.data_contracts import GetCurrentTimeTool
            tools = [GetCurrentTimeTool()]
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                params["tools"] = formatted_tools

        try:
            response = self.client.chat(**params)

            # Extraction du contenu et des tool calls
            content = ""
            tool_calls = []
            requires_tool_execution = False
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    message = choice.message
                    if hasattr(message, 'content'):
                        content = message.content
                    
                    # Vérifier les tool calls (format similaire à OpenAI)
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        requires_tool_execution = True
                        for tool_call in message.tool_calls:
                            tool_calls.append(ToolCall(
                                id=getattr(tool_call, 'id', 'unknown'),
                                tool_name=getattr(tool_call, 'function', {}).get('name', 'unknown'),
                                arguments=getattr(tool_call, 'function', {}).get('arguments', {})
                            ))

            return OrchestrationResponse(
                content=content,
                tool_calls=tool_calls,
                provider=self.get_provider_name(),
                model=request.agent_config.model_version,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else None,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None
                } if hasattr(response, 'usage') else None,
                requires_tool_execution=requires_tool_execution
            )
        except Exception as e:
            raise Exception(f"Mistral API error: {str(e)}")

    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """Génère une réponse simple à partir d'un prompt"""
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, **kwargs)
        return response.content

    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        return "mistral"

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles Mistral disponibles"""
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "codestral-latest"
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le service Mistral est disponible"""
        return self.client is not None and self.api_key is not None

    def get_model_name(self) -> str:
        """Retourne le nom du modèle par défaut"""
        return self.default_model