"""Adaptateur Anthropic - Implémentation de l'interface LLM pour Anthropic Claude avec Function Calling"""

import os
import json
from typing import List, Optional, Dict, Any
import anthropic
from src.domain.llm_service_interface import LLMServiceInterface
from src.models.data_contracts import (
    ChatMessage, ChatResponse, ToolDefinition, ToolCall, 
    OrchestrationRequest, OrchestrationResponse
)


class AnthropicAdapter(LLMServiceInterface):
    """Adaptateur pour l'API Anthropic Claude"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'adaptateur Anthropic
        
        Args:
            api_key: Clé API Anthropic (optionnel, peut être définie via ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.default_model = "claude-sonnet-4-5"

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_version: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ChatResponse:
        """Génère une réponse via l'API Anthropic avec support des outils"""
        if not self.client:
            raise Exception("Anthropic API key not configured")

        # Conversion des messages vers le format Anthropic
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                # Anthropic traite les messages système séparément
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Paramètres de base
        params = {
            "model": model_version,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 1024,  # Obligatoire pour Anthropic
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        if system_message:
            params["system"] = system_message

        # Ajout des outils si fournis
        if tools:
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                params["tools"] = formatted_tools

        try:
            response = self.client.messages.create(**params)
            
            # Extraction du contenu de la réponse
            content = ""
            if response.content and len(response.content) > 0:
                # Anthropic retourne une liste de blocs de contenu
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif hasattr(block, 'type') and block.type == 'text':
                        content += getattr(block, 'text', str(block))
                    else:
                        content += str(block)
            
            return ChatResponse(
                content=content,
                provider=self.get_provider_name(),
                model=response.model if hasattr(response, 'model') else model_version,
                usage={
                    "prompt_tokens": response.usage.input_tokens if hasattr(response, 'usage') else None,
                    "completion_tokens": response.usage.output_tokens if hasattr(response, 'usage') else None,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if hasattr(response, 'usage') else None
                } if hasattr(response, 'usage') else None
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def format_tools_for_llm(self, tool_definitions: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convertit nos ToolDefinition internes vers le format Anthropic
        
        Selon la doc Anthropic, le format est:
        [{
            "name": "get_weather",
            "description": "Obtient la météo actuelle",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Ville et pays"
                    }
                },
                "required": ["location"]
            }
        }]
        
        Args:
            tool_definitions: Liste des définitions d'outils internes
            
        Returns:
            Liste des outils au format Anthropic
        """
        formatted_tools = []
        
        for tool in tool_definitions:
            try:
                # Récupérer le schéma de l'outil
                tool_schema = tool.get_tool_schema()
                
                # Extraire les informations de la fonction
                if "function" in tool_schema:
                    func_info = tool_schema["function"]
                    
                    # Format Anthropic avec input_schema
                    anthropic_tool = {
                        "name": func_info.get("name", tool.name),
                        "description": func_info.get("description", tool.description),
                        "input_schema": func_info.get("parameters", {
                            "type": "object",
                            "properties": {}
                        })
                    }
                    formatted_tools.append(anthropic_tool)
                else:
                    # Fallback si le schéma n'a pas la structure attendue
                    formatted_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": {
                            "type": "object",
                            "properties": {}
                        }
                    })
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
            raise Exception("Anthropic API key not configured")

        # Construire les messages avec l'historique
        messages = list(request.conversation_history)
        messages.append(ChatMessage(role="user", content=request.message))

        # Conversion des messages vers le format Anthropic
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Paramètres de base
        params = {
            "model": request.agent_config.model_version,
            "messages": anthropic_messages,
            "max_tokens": request.agent_config.max_tokens,
            "temperature": request.agent_config.temperature,
        }
        
        if system_message:
            params["system"] = system_message

        # Ajout des outils si activés
        if request.agent_config.tools_enabled and request.agent_config.available_tools:
            # Pour cette démo, on utilise GetCurrentTimeTool
            from src.models.data_contracts import GetCurrentTimeTool
            tools = [GetCurrentTimeTool()]
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                params["tools"] = formatted_tools

        try:
            response = self.client.messages.create(**params)

            # Extraction du contenu et des tool calls
            content = ""
            tool_calls = []
            requires_tool_execution = False
            
            if response.content and len(response.content) > 0:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif hasattr(block, 'type'):
                        if block.type == 'text':
                            content += getattr(block, 'text', str(block))
                        elif block.type == 'tool_use':
                            # Anthropic utilise tool_use pour les appels d'outils
                            requires_tool_execution = True
                            tool_calls.append(ToolCall(
                                id=getattr(block, 'id', 'unknown'),
                                tool_name=getattr(block, 'name', 'unknown'),
                                arguments=getattr(block, 'input', {})
                            ))
                    else:
                        content += str(block)

            return OrchestrationResponse(
                content=content,
                tool_calls=tool_calls,
                provider=self.get_provider_name(),
                model=request.agent_config.model_version,
                usage={
                    "prompt_tokens": response.usage.input_tokens if hasattr(response, 'usage') else None,
                    "completion_tokens": response.usage.output_tokens if hasattr(response, 'usage') else None,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if hasattr(response, 'usage') else None
                } if hasattr(response, 'usage') else None,
                requires_tool_execution=requires_tool_execution
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """Génère une réponse simple à partir d'un prompt"""
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, **kwargs)
        return response.content

    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        return "anthropic"

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles Anthropic disponibles"""
        return [
            "claude-sonnet-4-5",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307"
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le service Anthropic est disponible"""
        return self.client is not None and self.api_key is not None

    def get_model_name(self) -> str:
        """Retourne le nom du modèle par défaut"""
        return self.default_model