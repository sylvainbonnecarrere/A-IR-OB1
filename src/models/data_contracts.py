"""Data Contracts - Pydantic Models for API Validation avec Durcissement Unicode/Sécurité"""

import re
import unicodedata
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from uuid import UUID, uuid4
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


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


class RetryConfig(BaseModel):
    """
    Configuration de résilience pour les appels LLM (JALON 4.2)
    
    Définit les paramètres de retry avec backoff exponentiel pour gérer
    les erreurs temporaires des APIs LLM de façon robuste.
    """
    max_attempts: int = Field(
        default=3, 
        ge=1, 
        le=10,
        description="Nombre maximum de tentatives (1-10)"
    )
    delay_base: float = Field(
        default=1.0, 
        ge=0.1, 
        le=60.0,
        description="Délai initial en secondes pour le backoff exponentiel (0.1-60s)"
    )
    
    @field_validator('max_attempts')
    @classmethod
    def validate_max_attempts(cls, v: int) -> int:
        """Validation du nombre maximum de tentatives"""
        if v < 1 or v > 10:
            raise ValueError("max_attempts doit être entre 1 et 10")
        return v
    
    @field_validator('delay_base')
    @classmethod
    def validate_delay_base(cls, v: float) -> float:
        """Validation du délai de base"""
        if v < 0.1 or v > 60.0:
            raise ValueError("delay_base doit être entre 0.1 et 60.0 secondes")
        return v


class AgentConfig(BaseModel):
    """Configuration pour un agent IA avec outils et validation sécurisée"""
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="Fournisseur LLM")
    model_version: str = Field(default="gpt-4o", description="Version exacte du modèle LLM à utiliser")
    temperature: float = Field(default=0.7, description="Température de génération")
    max_tokens: int = Field(default=1000, description="Nombre maximum de tokens")
    tools_enabled: bool = Field(default=False, description="Activer les outils")
    available_tools: List[str] = Field(default_factory=list, description="Liste des outils disponibles")
    system_prompt: Optional[str] = Field(default=None, description="Prompt système personnalisé")
    
    # JALON 4.2: Configuration de résilience
    retry_config: RetryConfig = Field(
        default_factory=RetryConfig, 
        description="Configuration de retry avec backoff pour les appels LLM"
    )
    
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
    """Réponse d'orchestration avec support des outils et suivi de session"""
    content: Optional[str] = Field(default=None, description="Réponse textuelle de l'IA")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Appels d'outils demandés par l'IA")
    provider: str = Field(..., description="Fournisseur LLM utilisé")
    model: str = Field(..., description="Modèle LLM utilisé")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Informations d'utilisation")
    requires_tool_execution: bool = Field(default=False, description="Indique si des outils doivent être exécutés")
    
    # Jalon 3.5 - Suivi de session
    session_id: Optional[UUID] = Field(default=None, description="ID de la session associée")
    status: Optional[str] = Field(default=None, description="Statut de la session")


# ============================================================================
# JALON 3.4 - ORCHESTRATION MULTI-AGENTS
# ============================================================================

class AgentDefinition(BaseModel):
    """
    Définition d'un agent spécialisé pour l'orchestration multi-agents
    
    Cette classe encapsule la configuration complète d'un agent spécialisé,
    incluant sa mission, sa description pour le routeur, et sa configuration LLM.
    """
    agent_name: str = Field(..., description="Nom unique de l'agent (ex: 'Data_Analyst_Agent')")
    description: str = Field(..., description="Description détaillée de la mission de l'agent pour le routeur LLM")
    default_config: AgentConfig = Field(..., description="Configuration LLM par défaut de cet agent")
    
    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Validation du nom d'agent (format identifier)"""
        cleaned = validate_safe_string(v, "agent_name")
        
        # Validation format identifier (lettres, chiffres, underscore)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', cleaned):
            raise ValueError(f"Nom d'agent invalide: {cleaned}. Format requis: identificateur valide (commence par lettre, puis lettres/chiffres/underscore)")
        
        return cleaned
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validation et normalisation de la description d'agent"""
        return validate_safe_string(v, "agent_description")
    
    @model_validator(mode='after')
    def validate_agent_consistency(self) -> 'AgentDefinition':
        """Validation de la cohérence entre nom d'agent et configuration"""
        # Vérifier que la configuration a un system_prompt si l'agent est spécialisé
        if not self.default_config.system_prompt and self.agent_name != "Default_Agent":
            # Génération automatique d'un system_prompt basique si manquant
            self.default_config.system_prompt = f"Tu es {self.agent_name}. {self.description}"
        
        return self


# ============================================================================
# JALON 4.1-B - CONTRATS DE TRAÇABILITÉ (TRACING)
# ============================================================================

class TraceStep(BaseModel):
    """
    Modèle pour une étape unique de traçage dans le cycle d'orchestration
    
    Chaque TraceStep représente un événement atomique dans le flux d'exécution,
    permettant une observabilité complète du système pour le débogage.
    """
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage précis de l'étape")
    component: str = Field(..., description="Composant responsable (Router/Orchestrator/LLM/HistorySummarizer)")
    event: str = Field(..., description="Type d'événement (start/decision/call/response/error)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Détails spécifiques de l'étape")
    
    @field_validator('component')
    @classmethod
    def validate_component(cls, v: str) -> str:
        """Validation du nom de composant"""
        allowed_components = {
            'Router', 'Orchestrator', 'LLM', 'HistorySummarizer', 
            'AgentRouter', 'AgentOrchestrator', 'ToolExecutor', 'SessionManager'
        }
        if v not in allowed_components:
            # Permettre d'autres composants mais normaliser
            return validate_safe_string(v, "trace_component")
        return v
    
    @field_validator('event')
    @classmethod
    def validate_event(cls, v: str) -> str:
        """Validation du type d'événement"""
        return validate_safe_string(v, "trace_event")

# Type Alias pour une trace complète (liste d'étapes)
Trace = List[TraceStep]


# ============================================================================
# JALON 3.5 - PERSISTANCE ET MÉMOIRE À LONG TERME
# ============================================================================

class HistoryConfig(BaseModel):
    """
    Configuration pour la gestion de la mémoire à long terme et la synthèse d'historique
    
    Cette classe définit les seuils et paramètres pour déclencher la synthèse automatique
    de l'historique de conversation afin de maintenir des performances optimales.
    """
    enabled: bool = Field(default=True, description="Active ou désactive la synthèse automatique")
    
    # Seuils de déclenchement
    message_threshold: int = Field(default=10, description="Nombre max de messages avant synthèse")
    token_threshold: int = Field(default=8000, description="Nombre max de tokens approximatifs avant synthèse")
    word_threshold: int = Field(default=2000, description="Nombre max de mots avant synthèse")
    char_threshold: int = Field(default=15000, description="Nombre max de caractères avant synthèse")
    
    # Configuration du LLM de synthèse
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="Fournisseur LLM pour la synthèse")
    model_version: str = Field(default="gpt-3.5-turbo", description="Modèle rapide pour la synthèse")
    system_prompt: str = Field(
        default="""Tu es un assistant spécialisé dans la synthèse d'historiques de conversation.

Ta mission : créer un résumé concis et informatif qui préserve :
1. Le contexte principal de la conversation
2. Les informations clés échangées
3. L'état actuel de la discussion
4. Les décisions ou conclusions importantes

Format de sortie :
- Résumé en 2-3 paragraphes maximum
- Style narratif fluide
- Préservation du contexte pour la suite de la conversation
- Focus sur les éléments utiles pour les prochains échanges

Évite les détails superflus et concentre-toi sur l'essentiel.""",
        description="Prompt système pour le LLM de synthèse"
    )
    
    @field_validator('message_threshold', 'token_threshold', 'word_threshold', 'char_threshold')
    @classmethod
    def validate_positive_thresholds(cls, v: int) -> int:
        """Validation que les seuils sont positifs"""
        if v <= 0:
            raise ValueError("Les seuils doivent être des nombres positifs")
        return v


class Session(BaseModel):
    """
    Modèle pour une session de conversation persistante avec mémoire à long terme
    
    Une session encapsule une conversation complète avec un agent spécialisé,
    incluant l'historique, la configuration de synthèse et l'état d'exécution.
    """
    session_id: UUID = Field(default_factory=uuid4, description="Identifiant unique de la session")
    agent_name: str = Field(..., description="Nom de l'agent assigné à cette session")
    history: List[ChatMessage] = Field(default_factory=list, description="Historique complet de la conversation")
    status: str = Field(default="ACTIVE", description="Statut de la session (ACTIVE, PROCESSING, COMPLETED, ERROR)")
    history_config: HistoryConfig = Field(default_factory=HistoryConfig, description="Configuration de la mémoire à long terme")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp de création")
    last_message_at: datetime = Field(default_factory=datetime.now, description="Timestamp du dernier message")
    
    # JALON 4.1-B: Traçabilité pour observabilité
    trace: Trace = Field(default_factory=list, description="Historique complet des étapes d'exécution pour le débogage")
    
    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Validation du nom d'agent"""
        return validate_safe_string(v, "session_agent_name")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validation du statut de session"""
        allowed_statuses = {'ACTIVE', 'PROCESSING', 'COMPLETED', 'ERROR', 'PAUSED'}
        if v not in allowed_statuses:
            raise ValueError(f"Statut invalide: {v}. Statuts autorisés: {allowed_statuses}")
        return v
    
    def get_history_metrics(self) -> Dict[str, int]:
        """
        Calcule les métriques de l'historique pour les seuils de synthèse
        
        Returns:
            Dict contenant messages, chars, words, estimated_tokens
        """
        if not self.history:
            return {"messages": 0, "chars": 0, "words": 0, "estimated_tokens": 0}
        
        total_chars = 0
        total_words = 0
        
        for message in self.history:
            content = message.content or ""
            total_chars += len(content)
            # Approximation simple du comptage de mots
            words = len(content.split())
            total_words += words
        
        # Estimation approximative des tokens (1 token ≈ 4 caractères en moyenne)
        estimated_tokens = total_chars // 4
        
        return {
            "messages": len(self.history),
            "chars": total_chars,
            "words": total_words,
            "estimated_tokens": estimated_tokens
        }
    
    def should_trigger_summarization(self) -> bool:
        """
        Vérifie si la synthèse doit être déclenchée selon les seuils configurés
        
        Returns:
            bool: True si au moins un seuil est dépassé
        """
        if not self.history_config.enabled:
            return False
        
        metrics = self.get_history_metrics()
        
        return (
            metrics["messages"] >= self.history_config.message_threshold or
            metrics["chars"] >= self.history_config.char_threshold or
            metrics["words"] >= self.history_config.word_threshold or
            metrics["estimated_tokens"] >= self.history_config.token_threshold
        )


class SessionManager(ABC):
    """
    Interface abstraite pour la gestion des sessions persistantes
    
    Cette interface définit le contrat pour les implémentations de stockage
    de sessions (en mémoire, base de données, cache Redis, etc.)
    """
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Récupère une session par son ID
        
        Args:
            session_id: Identifiant unique de la session (string)
            
        Returns:
            Session si trouvée, None sinon
        """
        pass
    
    @abstractmethod
    async def save_session(self, session: Session) -> None:
        """
        Sauvegarde ou met à jour une session
        
        Args:
            session: Session à sauvegarder
        """
        pass
    
    @abstractmethod
    async def create_new_session(
        self, 
        agent_name: str, 
        history_config: Optional[HistoryConfig] = None
    ) -> Session:
        """
        Crée une nouvelle session
        
        Args:
            agent_name: Nom de l'agent assigné
            history_config: Configuration optionnelle de l'historique
            
        Returns:
            Nouvelle session créée
        """
        pass
    
    @abstractmethod
    async def list_sessions(self, limit: int = 100) -> List[Session]:
        """
        Liste les sessions existantes
        
        Args:
            limit: Nombre maximum de sessions à retourner
            
        Returns:
            Liste des sessions
        """
        pass


# === Modèles de requête/réponse pour les endpoints de session (Jalon 3.5) ===

@dataclass
class SessionCreateRequest:
    """Requête de création de session"""
    agent_name: str
    history_config: Optional[HistoryConfig] = None
    
    def __post_init__(self):
        self.agent_name = validate_user_input_security(self.agent_name, "agent_name")


@dataclass 
class SessionResponse:
    """Réponse avec informations de session"""
    session_id: str
    agent_name: str
    total_messages: int
    created_at: datetime
    last_message_at: datetime
    status: str
    
    # Métriques optionnelles
    total_characters: Optional[int] = None
    total_words: Optional[int] = None
    estimated_tokens: Optional[int] = None
    
    # JALON 4.1-B: Trace d'observabilité
    trace: Optional[Trace] = None


# ============================================================================
# EXCEPTIONS PERSONNALISÉES (JALON 4.2)
# ============================================================================

class AgentExecutionError(Exception):
    """
    Exception levée lors d'échecs définitifs d'exécution d'agent (JALON 4.2)
    
    Cette exception encapsule les erreurs finales après épuisement des 
    tentatives de retry, tout en préservant la sécurité (pas de fuite d'infos).
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None, attempts: int = 1):
        self.message = message
        self.original_error = original_error
        self.attempts = attempts
        super().__init__(self.message)
        
    def __str__(self) -> str:
        return f"Agent execution failed after {self.attempts} attempts: {self.message}"