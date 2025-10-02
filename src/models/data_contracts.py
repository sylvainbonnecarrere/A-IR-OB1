"""Data Contracts - Pydantic Models for API Validation avec Durcissement Unicode/Sécurité"""

import re
import unicodedata
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# ============================================================================
# JALON 2.6 - FONCTIONS DE SÉCURITÉ ET NORMALISATION
# ============================================================================

def normalize_and_sanitize_text(text: str) -> str:
    """
    Normalise et nettoie une chaîne de caractères pour la sécurité
    
    Args:
        text: Chaîne à normaliser
        
    Returns:
        str: Chaîne normalisée et sécurisée
        
    Sécurité:
        - Normalisation Unicode (NFC) pour éviter les attaques par caractères composés
        - Suppression des caractères de contrôle dangereux
        - Encodage strict UTF-8
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Normalisation Unicode (NFC - Canonical Decomposition, followed by Canonical Composition)
    normalized = unicodedata.normalize('NFC', text)
    
    # Suppression des caractères de contrôle dangereux (sauf \n, \r, \t)
    # Garde les caractères imprimables + whitespace basique
    control_chars_pattern = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]'
    cleaned = re.sub(control_chars_pattern, '', normalized)
    
    # Protection supplémentaire: limiter la longueur pour éviter DoS
    max_length = 50000  # 50KB de texte max
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "... [TRONQUÉ]"
    
    # Validation finale: s'assurer que c'est du UTF-8 valide
    try:
        cleaned.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback: remplacer les caractères problématiques
        cleaned = cleaned.encode('utf-8', errors='replace').decode('utf-8')
    
    return cleaned


def validate_safe_string(text: str, field_name: str = "field") -> str:
    """
    Validation stricte d'une chaîne pour les champs critiques
    
    Args:
        text: Chaîne à valider
        field_name: Nom du champ pour les messages d'erreur
        
    Returns:
        str: Chaîne validée et normalisée
        
    Raises:
        ValueError: Si la chaîne contient des éléments suspects
    """
    # Normalisation d'abord
    normalized = normalize_and_sanitize_text(text)
    
    # Détection de patterns suspects pour injection
    suspicious_patterns = [
        r'<script[^>]*>',  # Scripts HTML
        r'javascript:',    # JavaScript URLs
        r'on\w+\s*=',      # Event handlers HTML
        r'eval\s*\(',      # eval() calls
        r'exec\s*\(',      # exec() calls
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            raise ValueError(f"Contenu suspect détecté dans {field_name}: pattern '{pattern}' trouvé")
    
    return normalized


# ============================================================================
# MODÈLES PYDANTIC AVEC VALIDATION SÉCURISÉE
# ============================================================================


class LLMProvider(str, Enum):
    """Enumeration des fournisseurs LLM supportés"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    GROK = "grok"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    KIMI_K2 = "kimi_k2"


class ChatMessage(BaseModel):
    """Modèle pour un message de chat avec validation sécurisée"""
    role: str = Field(..., description="Rôle du message: 'user', 'assistant', 'system'")
    content: str = Field(..., description="Contenu du message")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validation et normalisation du contenu du message"""
        return validate_safe_string(v, "content")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validation du rôle (liste blanche)"""
        allowed_roles = {'user', 'assistant', 'system', 'tool'}
        if v not in allowed_roles:
            raise ValueError(f"Rôle non autorisé: {v}. Rôles autorisés: {allowed_roles}")
        return v


class ChatRequest(BaseModel):
    """Modèle pour une requête de chat avec validation sécurisée"""
    message: str = Field(..., description="Message de l'utilisateur")
    provider: Optional[LLMProvider] = Field(default=LLMProvider.OPENAI, description="Fournisseur LLM à utiliser")
    model: Optional[str] = Field(default=None, description="Modèle spécifique à utiliser")
    max_tokens: Optional[int] = Field(default=1000, description="Nombre maximum de tokens")
    temperature: Optional[float] = Field(default=0.7, description="Température pour la génération")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validation et normalisation du message utilisateur"""
        return validate_safe_string(v, "message")
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Validation du nom de modèle"""
        if v is not None:
            return normalize_and_sanitize_text(v)
        return v


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


# ============================================================================
# JALON 2.3 - MODELS POUR FUNCTION CALLING & TOOLS
# ============================================================================

class ToolCall(BaseModel):
    """Modèle pour un appel d'outil par l'IA"""
    id: str = Field(..., description="Identifiant unique de l'appel d'outil")
    tool_name: str = Field(..., description="Nom de l'outil appelé")
    arguments: Dict[str, Any] = Field(..., description="Arguments passés à l'outil")


class ToolResult(BaseModel):
    """Modèle pour le résultat d'exécution d'un outil"""
    tool_call_id: str = Field(..., description="ID de l'appel d'outil correspondant")
    success: bool = Field(..., description="Indique si l'exécution a réussi")
    result: Any = Field(..., description="Résultat de l'exécution de l'outil")
    error: Optional[str] = Field(default=None, description="Message d'erreur si échec")


class ToolDefinition(BaseModel):
    """Classe de base pour la définition d'un outil"""
    name: str = Field(..., description="Nom unique de l'outil")
    description: str = Field(..., description="Description de ce que fait l'outil")
    
    @classmethod
    def get_tool_schema(cls) -> Dict[str, Any]:
        """Retourne le schéma JSON de l'outil pour les APIs LLM"""
        schema = cls.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": schema.get("title", cls.__name__),
                "description": schema.get("description", ""),
                "parameters": schema.get("properties", {})
            }
        }


class GetCurrentTimeTool(ToolDefinition):
    """Outil de démonstration pour obtenir l'heure actuelle"""
    name: str = Field(default="get_current_time", description="Nom de l'outil")
    description: str = Field(
        default="Obtient l'heure et la date actuelles du système",
        description="Description de l'outil"
    )
    timezone: Optional[str] = Field(
        default="UTC", 
        description="Fuseau horaire pour l'heure (par défaut UTC)"
    )
    
    @classmethod
    def get_tool_schema(cls) -> Dict[str, Any]:
        """Schéma spécifique pour l'outil GetCurrentTime"""
        return {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Obtient l'heure et la date actuelles du système",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Fuseau horaire pour l'heure (UTC, Europe/Paris, etc.)",
                            "default": "UTC"
                        }
                    },
                    "required": []
                }
            }
        }


class AgentConfig(BaseModel):
    """Configuration pour un agent IA avec outils et validation sécurisée"""
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="Fournisseur LLM")
    model_version: str = Field(default="gpt-4o", description="Version exacte du modèle LLM à utiliser")
    temperature: float = Field(default=0.7, description="Température de génération")
    max_tokens: int = Field(default=1000, description="Nombre maximum de tokens")
    tools_enabled: bool = Field(default=False, description="Activer les outils")
    available_tools: List[str] = Field(default_factory=list, description="Liste des outils disponibles")
    system_prompt: Optional[str] = Field(default=None, description="Prompt système personnalisé")
    
    @field_validator('model_version')
    @classmethod
    def validate_model_version(cls, v: str) -> str:
        """Validation du nom de version de modèle"""
        return normalize_and_sanitize_text(v)
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt(cls, v: Optional[str]) -> Optional[str]:
        """Validation critique du system prompt"""
        if v is not None:
            return validate_safe_string(v, "system_prompt")
        return v
    
    @field_validator('available_tools')
    @classmethod
    def validate_available_tools(cls, v: List[str]) -> List[str]:
        """Validation de la liste des outils (liste blanche)"""
        allowed_tools = {
            'get_current_time', 
            'complex_api_call', 
            'calculate_expression', 
            'get_system_info'
        }
        
        validated_tools = []
        for tool in v:
            clean_tool = normalize_and_sanitize_text(tool)
            if clean_tool not in allowed_tools:
                raise ValueError(f"Outil non autorisé: {clean_tool}. Outils autorisés: {allowed_tools}")
            validated_tools.append(clean_tool)
        
        return validated_tools


class OrchestrationRequest(BaseModel):
    """Requête d'orchestration avec support des outils et validation sécurisée"""
    message: str = Field(..., description="Message de l'utilisateur")
    agent_config: Optional[AgentConfig] = Field(default_factory=AgentConfig, description="Configuration de l'agent")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Historique de conversation")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validation et normalisation du message d'orchestration"""
        return validate_safe_string(v, "orchestration_message")


class OrchestrationResponse(BaseModel):
    """Réponse d'orchestration avec support des outils"""
    content: Optional[str] = Field(default=None, description="Réponse textuelle de l'IA")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Appels d'outils demandés par l'IA")
    provider: str = Field(..., description="Fournisseur LLM utilisé")
    model: str = Field(..., description="Modèle LLM utilisé")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Informations d'utilisation")
    requires_tool_execution: bool = Field(default=False, description="Indique si des outils doivent être exécutés")