"""Data Contracts - Pydantic Models for API Validation"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    """Enumeration des fournisseurs LLM supportés"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ChatMessage(BaseModel):
    """Modèle pour un message de chat"""
    role: str = Field(..., description="Rôle du message: 'user', 'assistant', 'system'")
    content: str = Field(..., description="Contenu du message")


class ChatRequest(BaseModel):
    """Modèle pour une requête de chat"""
    message: str = Field(..., description="Message de l'utilisateur")
    provider: Optional[LLMProvider] = Field(default=LLMProvider.OPENAI, description="Fournisseur LLM à utiliser")
    model: Optional[str] = Field(default=None, description="Modèle spécifique à utiliser")
    max_tokens: Optional[int] = Field(default=1000, description="Nombre maximum de tokens")
    temperature: Optional[float] = Field(default=0.7, description="Température pour la génération")


class ChatResponse(BaseModel):
    """Modèle pour une réponse de chat"""
    content: str = Field(..., description="Contenu de la réponse")
    provider: str = Field(..., description="Fournisseur utilisé")
    model: str = Field(..., description="Modèle utilisé")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Informations d'utilisation")


class HealthResponse(BaseModel):
    """Modèle pour la réponse de santé de l'API"""
    status: str = Field(..., description="Statut de l'application")
    version: str = Field(..., description="Version de l'application")
    timestamp: str = Field(..., description="Timestamp de la vérification")


class ErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur"""
    error: str = Field(..., description="Description de l'erreur")
    details: Optional[str] = Field(default=None, description="Détails supplémentaires")
    code: Optional[int] = Field(default=None, description="Code d'erreur")


class ServiceTestRequest(BaseModel):
    """Modèle pour tester un service LLM"""
    message: str = Field(default="Hello, AI!", description="Message de test")
    provider: Optional[LLMProvider] = Field(default=LLMProvider.OPENAI, description="Fournisseur à tester")


class ServiceTestResponse(BaseModel):
    """Modèle pour la réponse de test de service"""
    success: bool = Field(..., description="Indique si le test a réussi")
    response: Optional[str] = Field(default=None, description="Réponse du service LLM")
    provider: str = Field(..., description="Fournisseur testé")
    error: Optional[str] = Field(default=None, description="Erreur éventuelle")


class ProvidersResponse(BaseModel):
    """Modèle pour la liste des fournisseurs disponibles"""
    providers: List[str] = Field(..., description="Liste des fournisseurs LLM disponibles")
    default: str = Field(..., description="Fournisseur par défaut")
    count: int = Field(..., description="Nombre de fournisseurs disponibles")