"""Adaptateur Gemini - Implémentation de l'interface LLM pour Google Gemini avec Function Calling"""

import os
from typing import List, Optional, Dict, Any
from google import genai
from google.genai import types
from src.domain.llm_service_interface import LLMServiceInterface
from src.models.data_contracts import (
    ChatMessage, ChatResponse, ToolDefinition, ToolCall, 
    OrchestrationRequest, OrchestrationResponse
)


class GeminiAdapter(LLMServiceInterface):
    """Adaptateur pour l'API Google Gemini"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'adaptateur Gemini
        
        Args:
            api_key: Clé API Gemini (optionnel, peut être définie via GEMINI_API_KEY)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.default_model = "gemini-2.5-flash"

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_version: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ChatResponse:
        """Génère une réponse via l'API Gemini avec support des outils"""
        if not self.client:
            raise Exception("Gemini API key not configured")

        # Conversion des messages vers le format Gemini
        # Gemini utilise un format de "contents" différent
        gemini_contents = []
        for msg in messages:
            if msg.role == "user":
                gemini_contents.append(msg.content)
            elif msg.role == "assistant":
                # Pour les réponses précédentes, on pourrait les inclure dans l'historique
                # Pour simplifier, on prend juste le dernier message utilisateur
                continue
            elif msg.role == "system":
                # Gemini traite les messages système différemment
                # On pourrait les préfixer au premier message utilisateur
                continue

        # Si plusieurs messages, on prend le dernier utilisateur (simplification)
        content = gemini_contents[-1] if gemini_contents else messages[-1].content

        # Configuration de la génération
        config_params = {}
        if max_tokens:
            config_params["max_output_tokens"] = max_tokens
        if temperature is not None:
            config_params["temperature"] = temperature

        config = types.GenerateContentConfig(**config_params) if config_params else None

        # Ajout des outils si fournis
        tools_config = None
        if tools:
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                tools_config = formatted_tools

        try:
            # Appel à l'API Gemini
            if tools_config:
                response = self.client.models.generate_content(
                    model=model_version,
                    contents=content,
                    config=config,
                    tools=tools_config
                )
            else:
                response = self.client.models.generate_content(
                    model=model_version,
                    contents=content,
                    config=config
                )
            
            return ChatResponse(
                content=response.text if hasattr(response, 'text') else str(response),
                provider=self.get_provider_name(),
                model=model_version,
                usage=None  # Gemini ne retourne pas toujours les détails d'usage
            )
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    async def format_tools_for_llm(self, tool_definitions: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convertit nos ToolDefinition internes vers le format Gemini
        
        Selon la doc Gemini, le format est:
        [{
            "function_declarations": [{
                "name": "get_weather",
                "description": "Obtient la météo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }]
        }]
        
        Args:
            tool_definitions: Liste des définitions d'outils internes
            
        Returns:
            Liste des outils au format Gemini
        """
        if not tool_definitions:
            return []

        function_declarations = []
        
        for tool in tool_definitions:
            try:
                # Récupérer le schéma de l'outil
                tool_schema = tool.get_tool_schema()
                
                # Extraire les informations de la fonction
                if "function" in tool_schema:
                    func_info = tool_schema["function"]
                    function_declarations.append({
                        "name": func_info.get("name", tool.name),
                        "description": func_info.get("description", tool.description),
                        "parameters": func_info.get("parameters", {})
                    })
                else:
                    # Fallback si le schéma n'a pas la structure attendue
                    function_declarations.append({
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    })
            except Exception as e:
                # Log l'erreur mais continue avec les autres outils
                print(f"Erreur lors du formatage de l'outil {tool.name}: {e}")
                continue
                
        # Format final Gemini avec function_declarations
        return [{
            "function_declarations": function_declarations
        }] if function_declarations else []

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
            raise Exception("Gemini API key not configured")

        # Construire les messages avec l'historique
        messages = list(request.conversation_history)
        messages.append(ChatMessage(role="user", content=request.message))

        # Pour Gemini, on simplifie en prenant le dernier message
        content = request.message

        # Configuration de base
        config_params = {
            "max_output_tokens": request.agent_config.max_tokens,
            "temperature": request.agent_config.temperature,
        }
        config = types.GenerateContentConfig(**config_params)

        # Ajout des outils si activés
        tools_config = None
        if request.agent_config.tools_enabled and request.agent_config.available_tools:
            # Pour cette démo, on utilise GetCurrentTimeTool
            from src.models.data_contracts import GetCurrentTimeTool
            tools = [GetCurrentTimeTool()]
            formatted_tools = await self.format_tools_for_llm(tools)
            if formatted_tools:
                tools_config = formatted_tools

        try:
            # Appel à l'API Gemini
            if tools_config:
                response = self.client.models.generate_content(
                    model=request.agent_config.model_version,
                    contents=content,
                    config=config,
                    tools=tools_config
                )
            else:
                response = self.client.models.generate_content(
                    model=request.agent_config.model_version,
                    contents=content,
                    config=config
                )

            # Pour cette implémentation simple, on ne gère pas encore les tool calls
            # TODO: Implémenter la détection et l'extraction des tool calls Gemini
            tool_calls = []
            requires_tool_execution = False

            return OrchestrationResponse(
                content=response.text if hasattr(response, 'text') else str(response),
                tool_calls=tool_calls,
                provider=self.get_provider_name(),
                model=request.agent_config.model_version,
                usage=None,  # Gemini ne retourne pas toujours les détails d'usage
                requires_tool_execution=requires_tool_execution
            )
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """Génère une réponse simple à partir d'un prompt"""
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, **kwargs)
        return response.content

    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        return "gemini"

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles Gemini disponibles"""
        return [
            "gemini-2.5-flash",
            "gemini-2.5-flash-image",
            "gemini-pro",
            "gemini-pro-vision"
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le service Gemini est disponible"""
        return self.client is not None and self.api_key is not None

    def get_model_name(self) -> str:
        """Retourne le nom du modèle par défaut"""
        return self.default_model