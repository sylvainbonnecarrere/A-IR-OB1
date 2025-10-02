"""
Collecteur de Métriques Prometheus pour l'Observabilité de Production (JALON 4.3)

Ce module implémente la collecte et l'exposition des métriques clés de l'orchestration
au format Prometheus/OpenMetrics pour le monitoring de production et l'intégration 
avec des outils comme Grafana.
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Info, Gauge, CollectorRegistry, generate_latest

logger = logging.getLogger(__name__)

# Variables globales pour le pattern singleton
_metrics_collector: Optional['MetricsCollector'] = None
_registry_in_use: Optional[CollectorRegistry] = None


class MetricsCollector:
    """
    Collecteur centralisé de métriques Prometheus pour l'observabilité de production
    
    Collecte et expose les métriques clés de performance, fiabilité et utilisation
    de la plateforme d'orchestration multi-agent selon les standards OpenMetrics.
    
    Métriques collectées:
    - Appels LLM (count, latency, tokens)
    - Exécutions d'outils (count, latency)  
    - Erreurs d'orchestrateur (count par type)
    - Sessions (count, durée, messages)
    - Tentatives de retry (count par composant)
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialise le collecteur avec toutes les métriques Prometheus
        
        Args:
            registry: Registry Prometheus personnalisé (optionnel)
        """
        self.registry = registry or CollectorRegistry()
        logger.info("✅ MetricsCollector initialisé avec toutes les métriques Prometheus")
        
        # =============================================================================
        # MÉTRIQUES LLM (Large Language Model)
        # =============================================================================
        
        # Compteur d'appels LLM avec labels détaillés
        self.llm_call_count = Counter(
            name='llm_call_count',
            documentation='Total number of LLM API calls',
            labelnames=['provider', 'model', 'status'],
            registry=self.registry
        )
        
        # Latence des appels LLM (histogramme pour percentiles)
        self.llm_latency_seconds = Histogram(
            name='llm_latency_seconds',
            documentation='Latency of LLM API calls in seconds',
            labelnames=['provider', 'model'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        # Tokens consommés par appel LLM
        self.llm_tokens_consumed = Counter(
            name='llm_tokens_consumed',
            documentation='Total tokens consumed by LLM calls',
            labelnames=['provider', 'model', 'token_type'],
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRIQUES D'ERREURS ET RÉSILIENCE
        # =============================================================================
        
        # Erreurs de l'orchestrateur par type et composant
        self.orchestrator_errors_count = Counter(
            name='orchestrator_errors_count',
            documentation='Total number of orchestrator errors',
            labelnames=['error_type', 'component'],
            registry=self.registry
        )
        
        # Tentatives de retry par composant
        self.retry_attempts_count = Counter(
            name='retry_attempts_count',
            documentation='Total number of retry attempts',
            labelnames=['component', 'operation'],
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRIQUES D'OUTILS (Tools)
        # =============================================================================
        
        # Compteur d'exécutions d'outils
        self.tool_execution_count = Counter(
            name='tool_execution_count',
            documentation='Total number of tool executions',
            labelnames=['tool_name', 'status'],
            registry=self.registry
        )
        
        # Latence d'exécution des outils
        self.tool_execution_latency = Histogram(
            name='tool_execution_latency_seconds',
            documentation='Tool execution latency in seconds',
            labelnames=['tool_name'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRIQUES DE SESSIONS
        # =============================================================================
        
        # Compteur de sessions créées
        self.session_count = Counter(
            name='session_count',
            documentation='Total number of sessions created',
            labelnames=['agent_name'],
            registry=self.registry
        )
        
        # Durée des sessions (histogramme)
        self.session_duration_seconds = Histogram(
            name='session_duration_seconds',
            documentation='Session duration in seconds',
            labelnames=['agent_name'],
            buckets=[1, 10, 60, 300, 600, 1800, 3600],
            registry=self.registry
        )
        
        # Nombre de messages par session
        self.session_messages_count = Histogram(
            name='session_messages_count',
            documentation='Number of messages per session',
            labelnames=['agent_name'],
            buckets=[1, 5, 10, 20, 50, 100, 200],
            registry=self.registry
        )
        
        # Sessions actives (gauge)
        self.active_sessions_gauge = Gauge(
            name='active_sessions_current',
            documentation='Current number of active sessions',
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRIQUES D'APPLICATION
        # =============================================================================
        
        # Informations sur l'application
        self.application_info = Info(
            name='application_info',
            documentation='Application information',
            registry=self.registry
        )
        
        # Initialiser les informations d'application
        self.application_info.info({
            'version': '1.0.0',
            'jalon': '4.3',
            'component': 'orchestrator_agent',
            'observability': 'prometheus_metrics'
        })
    
    # =============================================================================
    # MÉTHODES D'ENREGISTREMENT LLM
    # =============================================================================
    
    def record_llm_call(self, provider: str, model: str, duration_seconds: float, 
                       status: str, tokens_used: Optional[Dict[str, int]] = None):
        """
        Enregistre un appel LLM avec ses métriques associées
        
        Args:
            provider: Fournisseur LLM (openai, anthropic, etc.)
            model: Modèle utilisé (gpt-4, claude-3, etc.)
            duration_seconds: Durée en secondes
            status: Statut (success, error, timeout)
            tokens_used: Dictionnaire des tokens utilisés par type
        """
        # Compteur d'appels
        self.llm_call_count.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        # Latence
        self.llm_latency_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration_seconds)
        
        # Tokens consommés
        if tokens_used:
            for token_type, count in tokens_used.items():
                self.llm_tokens_consumed.labels(
                    provider=provider,
                    model=model,
                    token_type=token_type
                ).inc(count)
    
    # =============================================================================
    # MÉTHODES D'ENREGISTREMENT OUTILS
    # =============================================================================
    
    def record_tool_execution(self, tool_name: str, duration_seconds: float, status: str):
        """
        Enregistre l'exécution d'un outil
        
        Args:
            tool_name: Nom de l'outil exécuté
            duration_seconds: Durée d'exécution
            status: Statut (success, error, timeout)
        """
        self.tool_execution_count.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        self.tool_execution_latency.labels(
            tool_name=tool_name
        ).observe(duration_seconds)
    
    # =============================================================================
    # MÉTHODES D'ENREGISTREMENT ERREURS
    # =============================================================================
    
    def record_orchestrator_error(self, error_type: str, component: str):
        """
        Enregistre une erreur de l'orchestrateur
        
        Args:
            error_type: Type d'erreur (RESILIENT_LLM_FAILURE, VALIDATION_ERROR, etc.)
            component: Composant source (AgentOrchestrator, ResilientLLMService, etc.)
        """
        self.orchestrator_errors_count.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def record_retry_attempt(self, component: str, operation: str):
        """
        Enregistre une tentative de retry
        
        Args:
            component: Composant qui retry
            operation: Opération tentée
        """
        self.retry_attempts_count.labels(
            component=component,
            operation=operation
        ).inc()
    
    # =============================================================================
    # MÉTHODES D'ENREGISTREMENT SESSIONS
    # =============================================================================
    
    def record_session_created(self, agent_name: str):
        """
        Enregistre la création d'une session
        
        Args:
            agent_name: Nom de l'agent
        """
        self.session_count.labels(agent_name=agent_name).inc()
    
    def record_session_completed(self, agent_name: str, duration_seconds: float, 
                                message_count: int):
        """
        Enregistre la fin d'une session avec ses métriques
        
        Args:
            agent_name: Nom de l'agent
            duration_seconds: Durée totale de la session
            message_count: Nombre de messages échangés
        """
        self.session_duration_seconds.labels(agent_name=agent_name).observe(duration_seconds)
        self.session_messages_count.labels(agent_name=agent_name).observe(message_count)
    
    def update_active_sessions_count(self, count: int):
        """
        Met à jour le nombre de sessions actives
        
        Args:
            count: Nombre actuel de sessions actives
        """
        self.active_sessions_gauge.set(count)
    
    # =============================================================================
    # EXPOSITION DES MÉTRIQUES
    # =============================================================================
    
    def get_metrics(self) -> str:
        """
        Génère et retourne les métriques au format OpenMetrics
        
        Returns:
            Chaîne contenant toutes les métriques au format Prometheus/OpenMetrics
        """
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur génération métriques: {e}")
            # Retour de métriques de fallback en cas d'erreur
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self) -> str:
        """
        Génère des métriques de fallback en cas d'erreur
        
        Returns:
            Métriques minimales de fallback
        """
        fallback = [
            "# HELP application_info Application information",
            "# TYPE application_info info",
            'application_info{version="1.0.0",status="error"} 1',
            "",
            "# HELP metrics_generation_errors_total Metrics generation errors",
            "# TYPE metrics_generation_errors_total counter", 
            "metrics_generation_errors_total 1"
        ]
        return "\n".join(fallback)


# =============================================================================
# FONCTIONS GLOBALES DE GESTION
# =============================================================================

def initialize_metrics_collector(registry: Optional[CollectorRegistry] = None) -> MetricsCollector:
    """
    Initialise le collecteur de métriques global avec le registry fourni
    
    Args:
        registry: Registry Prometheus personnalisé
        
    Returns:
        Instance initialisée du MetricsCollector
    """
    global _metrics_collector, _registry_in_use
    
    # Si on utilise déjà ce registry, retourner l'instance existante
    if _metrics_collector is not None and _registry_in_use is registry:
        return _metrics_collector
    
    # Reset l'instance globale si on change de registry
    _metrics_collector = None
    _registry_in_use = None
    
    # Créer nouvelle instance
    _metrics_collector = MetricsCollector(registry=registry)
    _registry_in_use = registry
    return _metrics_collector


def reset_metrics_collector():
    """
    Reset le collecteur de métriques global - utilisé principalement pour les tests
    """
    global _metrics_collector, _registry_in_use
    _metrics_collector = None
    _registry_in_use = None


def get_metrics_collector() -> MetricsCollector:
    """
    Retourne l'instance globale du collecteur de métriques
    
    Returns:
        Instance du MetricsCollector (crée une nouvelle si nécessaire)
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector