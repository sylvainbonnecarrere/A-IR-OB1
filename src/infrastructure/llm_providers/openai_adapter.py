"""Adaptateur OpenAI - Implémentation de l'interface LLM pour OpenAI"""

import os
from typing import List, Optional
from openai import AsyncOpenAI
from src.domain.llm_service_interface import LLMServiceInterface
from src.models.data_contracts import ChatMessage, ChatResponse


class OpenAIAdapter(LLMServiceInterface):
    """Adaptateur pour l'API OpenAI"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'adaptateur OpenAI
        
        Args:
            api_key: Clé API OpenAI (optionnel, peut être définie via OPENAI_API_KEY)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.default_model = "gpt-3.5-turbo"

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> ChatResponse:
        """Génère une réponse via l'API OpenAI Chat Completion"""
        if not self.client:
            raise Exception("OpenAI API key not configured")

        # Conversion des messages Pydantic vers le format OpenAI
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Paramètres de la requête
        params = {
            "model": model or self.default_model,
            "messages": openai_messages,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature

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
            raise Exception(f"OpenAI API error: {str(e)}")

    async def simple_completion(self, prompt: str, **kwargs) -> str:
        """Génère une réponse simple à partir d'un prompt"""
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.chat_completion(messages, **kwargs)
        return response.content

    def get_provider_name(self) -> str:
        """Retourne le nom du fournisseur"""
        return "openai"

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles OpenAI disponibles"""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le service OpenAI est disponible"""
        return self.client is not None and self.api_key is not None