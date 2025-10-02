"""Adaptateur Kimi K2 - Implémentation de l'interface LLM pour Kimi K2/Moonshot (OpenAI-compatible)"""

import os
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from src.domain.llm_service_interface import LLMServiceInterface
from src.models.data_contracts import (
    ChatMessage, ChatResponse, ToolDefinition, ToolCall, 
    OrchestrationRequest, OrchestrationResponse
)


class KimiK2Adapter(LLMServiceInterface):
    """Adaptateur pour l'API Kimi K2/Moonshot (compatible OpenAI)"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'adaptateur Kimi K2
        
        Args:
            api_key: Clé API Kimi K2 (optionnel, peut être définie via KIMI_K2_API_KEY)
        """
        self.api_key = api_key or os.getenv("KIMI_K2_API_KEY")
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        ) if self.api_key else None
        self.default_model = "moonshot-v1-128k"

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_version: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ChatResponse:
        """Génère une réponse via l'API Kimi K2 avec support des outils"""
        if not self.client:
            raise Exception("Kimi K2 API key not configured")

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
            
        # Ajout des outils si fournis (format OpenAI)
        if tools:
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                params["tools"] = formatted_tools
                params["tool_choice"] = "auto"

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
            raise Exception(f"Kimi K2 API error: {str(e)}")

    async def format_tools_for_llm(self, tool_definitions: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convertit nos ToolDefinition internes vers le format OpenAI (Kimi K2 compatible)
        
        Args:
            tool_definitions: Liste des définitions d'outils internes
            
        Returns:
            Liste des outils au format OpenAI
        """
        formatted_tools = []
        
        for tool in tool_definitions:
            try:
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
            raise Exception("Kimi K2 API key not configured")

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

        # Ajout des outils si activés
        if request.agent_config.tools_enabled and request.agent_config.available_tools:
            # Pour cette démo, on utilise GetCurrentTimeTool
            from src.models.data_contracts import GetCurrentTimeTool
            tools = [GetCurrentTimeTool()]
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                params["tools"] = formatted_tools
                params["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**params)
            message = response.choices[0].message

            # Vérifier si l'IA veut appeler des outils
            tool_calls = []
            requires_tool_execution = False
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                requires_tool_execution = True
                for tool_call in message.tool_calls:
                    tool_calls.append(ToolCall(
                        id=tool_call.id,
                        tool_name=tool_call.function.name,
                        arguments=eval(tool_call.function.arguments) if tool_call.function.arguments else {}
                    ))

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
            raise Exception(f"Kimi K2 API error: {str(e)}")

    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """Génère une réponse simple à partir d'un prompt"""
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, **kwargs)
        return response.content

    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        return "kimi_k2"

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles Kimi K2 disponibles"""
        return [
            "moonshot-v1-128k",
            "moonshot-v1-32k",
            "moonshot-v1-8k"
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le service Kimi K2 est disponible"""
        return self.client is not None and self.api_key is not None

    def get_model_name(self) -> str:
        """Retourne le nom du modèle par défaut"""
        return self.default_model