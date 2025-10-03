# 📊 Guide de Métriques et Monitoring - Orchestrator Agent

Ce guide détaille le système complet de surveillance, métriques et monitoring de la plateforme Orchestrator Agent avec ses 8 fournisseurs LLM.

## 🎯 Vue d'ensemble du Monitoring

### Architecture de Surveillance

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Health Checks │    │   Métriques API  │    │  Session Stats  │
│                 │    │                  │    │                 │
│ • Provider UP   │    │ • Latence        │    │ • Messages      │
│ • API Keys OK   │    │ • Throughput     │    │ • Coûts         │
│ • Connectivité  │    │ • Erreurs        │    │ • Durée         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │   Dashboard Central     │
                    │                         │
                    │ • Alertes temps réel    │
                    │ • Rapports automatiques │
                    │ • Analytics prédictives │
                    └─────────────────────────┘
```

## 🏥 Health Checks Avancés

### Endpoint Health Global

```http
GET /api/health
```

**Réponse détaillée :**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "uptime": "5d 12h 34m 22s",
  "providers_status": {
    "openai": {
      "healthy": true,
      "last_check": "2024-01-01T11:59:55Z",
      "response_time": 1.23,
      "api_key_configured": true,
      "models_available": ["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
      "rate_limit_remaining": 4850,
      "error_rate_24h": 0.02
    },
    "anthropic": {
      "healthy": true,
      "last_check": "2024-01-01T11:59:57Z",
      "response_time": 1.87,
      "api_key_configured": true,
      "models_available": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
      "rate_limit_remaining": 4200,
      "error_rate_24h": 0.01
    },
    "gemini": {
      "healthy": false,
      "last_check": "2024-01-01T11:59:45Z",
      "response_time": null,
      "api_key_configured": true,
      "error": "Connection timeout",
      "last_success": "2024-01-01T10:30:12Z",
      "error_rate_24h": 0.15
    }
  },
  "system_metrics": {
    "cpu_usage": 23.5,
    "memory_usage": 67.2,
    "disk_usage": 45.8,
    "active_sessions": 142,
    "requests_per_minute": 87
  }
}
```

### Health Check par Provider

```python
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ProviderHealthMonitor:
    """Moniteur de santé avancé pour chaque provider"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.health_history = {}
        self.alert_thresholds = {
            'response_time': 5.0,  # secondes
            'error_rate': 0.05,    # 5%
            'uptime': 0.99         # 99%
        }
    
    async def check_provider_health(self, provider: str) -> Dict[str, Any]:
        """Effectue un health check complet d'un provider"""
        start_time = time.time()
        
        try:
            # Test basique de connectivité
            response = await self._test_provider_connectivity(provider)
            response_time = time.time() - start_time
            
            # Test de fonctionnalité
            functionality_test = await self._test_provider_functionality(provider)
            
            # Calcul des métriques
            health_data = {
                "provider": provider,
                "timestamp": datetime.now().isoformat(),
                "healthy": response and functionality_test,
                "response_time": response_time,
                "connectivity": response,
                "functionality": functionality_test,
                "api_key_status": self._check_api_key_status(provider),
                "rate_limits": await self._check_rate_limits(provider),
                "error_rate": self._calculate_error_rate(provider),
                "uptime_24h": self._calculate_uptime(provider)
            }
            
            # Stocker l'historique
            self._store_health_history(provider, health_data)
            
            # Vérifier les alertes
            self._check_alert_conditions(provider, health_data)
            
            return health_data
            
        except Exception as e:
            return {
                "provider": provider,
                "timestamp": datetime.now().isoformat(),
                "healthy": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    async def _test_provider_connectivity(self, provider: str) -> bool:
        """Test de connectivité basique"""
        try:
            # Simuler un test de connectivité
            response = requests.get(f"{self.base_url}/providers")
            return response.status_code == 200
        except:
            return False
    
    async def _test_provider_functionality(self, provider: str) -> bool:
        """Test de fonctionnalité avec requête simple"""
        try:
            response = requests.post(f"{self.base_url}/orchestrate", json={
                "message": "Test de santé",
                "agent_config": {"provider": provider, "max_tokens": 10}
            })
            return response.status_code == 200
        except:
            return False
    
    def _check_api_key_status(self, provider: str) -> Dict[str, Any]:
        """Vérifie le statut de la clé API"""
        env_var = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(env_var)
        
        return {
            "configured": api_key is not None,
            "valid_format": self._validate_api_key_format(provider, api_key),
            "expires_soon": self._check_key_expiration(provider, api_key)
        }
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Génère un rapport de santé complet"""
        providers = ["openai", "anthropic", "gemini", "mistral", "grok", "qwen", "deepseek", "kimi_k2"]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "providers": {},
            "summary": {
                "total_providers": len(providers),
                "healthy_providers": 0,
                "degraded_providers": 0,
                "unhealthy_providers": 0
            },
            "alerts": []
        }
        
        for provider in providers:
            health_data = asyncio.run(self.check_provider_health(provider))
            report["providers"][provider] = health_data
            
            if health_data.get("healthy", False):
                report["summary"]["healthy_providers"] += 1
            elif health_data.get("response_time", 0) > self.alert_thresholds["response_time"]:
                report["summary"]["degraded_providers"] += 1
            else:
                report["summary"]["unhealthy_providers"] += 1
        
        # Déterminer le statut global
        if report["summary"]["unhealthy_providers"] > 0:
            report["overall_status"] = "unhealthy"
        elif report["summary"]["degraded_providers"] > 0:
            report["overall_status"] = "degraded"
        
        return report

# Instance globale
health_monitor = ProviderHealthMonitor()
```

## 📈 Métriques de Performance

### Endpoint Métriques Détaillées

```http
GET /api/metrics
```

**Réponse complète :**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "period": "last_24h",
  "system_metrics": {
    "uptime": "5d 12h 34m",
    "total_requests": 15420,
    "successful_requests": 15112,
    "failed_requests": 308,
    "success_rate": 0.98,
    "average_response_time": 1.85,
    "requests_per_minute": 87.3,
    "peak_rps": 23.7,
    "memory_usage": {
      "current": "512MB",
      "peak": "743MB",
      "average": "487MB"
    },
    "cpu_usage": {
      "current": 23.5,
      "peak": 78.2,
      "average": 34.7
    }
  },
  "provider_metrics": {
    "openai": {
      "requests": 5420,
      "success_rate": 0.992,
      "average_latency": 1.23,
      "p50_latency": 1.15,
      "p95_latency": 2.47,
      "p99_latency": 4.12,
      "total_tokens": 234567,
      "total_cost": 12.34,
      "models_used": {
        "gpt-3.5-turbo": 3200,
        "gpt-4": 1850,
        "gpt-4o": 370
      },
      "error_breakdown": {
        "rate_limit": 15,
        "timeout": 8,
        "api_error": 12,
        "other": 7
      }
    },
    "anthropic": {
      "requests": 4100,
      "success_rate": 0.985,
      "average_latency": 1.87,
      "p50_latency": 1.65,
      "p95_latency": 3.21,
      "p99_latency": 5.89,
      "total_tokens": 187432,
      "total_cost": 23.45,
      "models_used": {
        "claude-3-5-sonnet-20241022": 2800,
        "claude-3-5-haiku-20241022": 1300
      }
    }
  },
  "session_metrics": {
    "total_sessions": 1520,
    "active_sessions": 142,
    "completed_sessions": 1378,
    "average_session_duration": "00:23:45",
    "average_messages_per_session": 8.7,
    "sessions_with_summarization": 234,
    "summarization_rate": 0.154
  },
  "cost_analytics": {
    "total_cost_24h": 156.78,
    "cost_by_provider": {
      "openai": 45.23,
      "anthropic": 67.89,
      "gemini": 23.45,
      "mistral": 12.34,
      "others": 7.87
    },
    "cost_trend": "increasing",
    "projected_monthly_cost": 4703.40
  }
}
```

### Métriques de Session Détaillées

```http
GET /api/sessions/{session_id}/metrics
```

```python
class SessionMetricsCollector:
    """Collecteur de métriques avancées pour les sessions"""
    
    def __init__(self):
        self.session_data = {}
    
    def collect_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Collecte des métriques complètes pour une session"""
        
        # Récupérer les données de base
        session_response = requests.get(f"{base_url}/sessions/{session_id}/metrics")
        base_metrics = session_response.json()
        
        # Récupérer l'historique complet
        history_response = requests.get(f"{base_url}/sessions/{session_id}/history?limit=1000")
        history = history_response.json()
        
        # Calculer les métriques avancées
        advanced_metrics = self._calculate_advanced_metrics(history)
        
        return {
            **base_metrics,
            "advanced_analytics": advanced_metrics,
            "quality_metrics": self._calculate_quality_metrics(history),
            "efficiency_metrics": self._calculate_efficiency_metrics(history),
            "user_satisfaction": self._estimate_satisfaction(history)
        }
    
    def _calculate_advanced_metrics(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule des métriques avancées"""
        messages = history.get("messages", [])
        
        if not messages:
            return {}
        
        # Analyser les patterns de conversation
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        
        # Métriques temporelles
        session_duration = self._calculate_session_duration(messages)
        response_times = self._extract_response_times(messages)
        
        # Métriques de contenu
        avg_user_message_length = np.mean([len(msg.get("content", "")) for msg in user_messages])
        avg_assistant_message_length = np.mean([len(msg.get("content", "")) for msg in assistant_messages])
        
        # Patterns d'utilisation
        provider_switches = self._count_provider_switches(assistant_messages)
        peak_activity_time = self._identify_peak_activity(messages)
        
        return {
            "session_duration_minutes": session_duration / 60,
            "average_response_time": np.mean(response_times),
            "response_time_variance": np.var(response_times),
            "message_frequency": len(messages) / (session_duration / 60),  # messages/minute
            "avg_user_message_length": avg_user_message_length,
            "avg_assistant_message_length": avg_assistant_message_length,
            "provider_switches": provider_switches,
            "peak_activity_time": peak_activity_time,
            "conversation_complexity": self._assess_complexity(messages)
        }
    
    def _calculate_quality_metrics(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue la qualité des réponses"""
        messages = history.get("messages", [])
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        
        quality_scores = []
        for msg in assistant_messages:
            content = msg.get("content", "")
            provider = msg.get("provider", "unknown")
            
            # Métriques de qualité heuristiques
            completeness = min(len(content) / 500, 1.0)  # Normaliser sur 500 chars
            structure = self._assess_structure_quality(content)
            relevance = self._assess_relevance(content)
            
            quality_scores.append({
                "provider": provider,
                "completeness": completeness,
                "structure": structure,
                "relevance": relevance,
                "overall": (completeness + structure + relevance) / 3
            })
        
        if not quality_scores:
            return {}
        
        avg_quality = np.mean([score["overall"] for score in quality_scores])
        
        return {
            "average_quality_score": avg_quality,
            "quality_by_provider": self._group_quality_by_provider(quality_scores),
            "quality_trend": self._calculate_quality_trend(quality_scores),
            "best_performing_provider": max(quality_scores, key=lambda x: x["overall"])["provider"]
        }

# Instance de collecteur
metrics_collector = SessionMetricsCollector()
```

## 🚨 Système d'Alertes Avancé

### Configuration des Alertes

```python
class AlertManager:
    """Gestionnaire d'alertes intelligent"""
    
    def __init__(self):
        self.alert_rules = {
            "provider_down": {
                "condition": lambda metrics: not metrics.get("healthy", True),
                "severity": "critical",
                "cooldown": 300,  # 5 minutes
                "message": "Provider {provider} is down"
            },
            "high_latency": {
                "condition": lambda metrics: metrics.get("response_time", 0) > 5.0,
                "severity": "warning",
                "cooldown": 600,  # 10 minutes
                "message": "High latency detected for {provider}: {response_time}s"
            },
            "error_rate_spike": {
                "condition": lambda metrics: metrics.get("error_rate", 0) > 0.1,
                "severity": "warning",
                "cooldown": 900,  # 15 minutes
                "message": "Error rate spike for {provider}: {error_rate:.2%}"
            },
            "cost_anomaly": {
                "condition": lambda metrics: metrics.get("cost_hourly", 0) > 50.0,
                "severity": "info",
                "cooldown": 3600,  # 1 hour
                "message": "Cost anomaly detected: ${cost_hourly}/hour"
            },
            "session_overload": {
                "condition": lambda metrics: metrics.get("active_sessions", 0) > 1000,
                "severity": "warning",
                "cooldown": 300,
                "message": "High session load: {active_sessions} active sessions"
            }
        }
        
        self.alert_history = {}
        self.notification_channels = {
            "email": EmailNotifier(),
            "slack": SlackNotifier(),
            "webhook": WebhookNotifier()
        }
    
    def check_alerts(self, metrics: Dict[str, Any]):
        """Vérifie toutes les conditions d'alerte"""
        current_time = time.time()
        
        for rule_name, rule in self.alert_rules.items():
            try:
                if rule["condition"](metrics):
                    # Vérifier le cooldown
                    last_alert = self.alert_history.get(rule_name, 0)
                    if current_time - last_alert > rule["cooldown"]:
                        self._trigger_alert(rule_name, rule, metrics)
                        self.alert_history[rule_name] = current_time
            except Exception as e:
                print(f"Erreur évaluation règle {rule_name}: {e}")
    
    def _trigger_alert(self, rule_name: str, rule: Dict[str, Any], metrics: Dict[str, Any]):
        """Déclenche une alerte"""
        alert = {
            "rule": rule_name,
            "severity": rule["severity"],
            "message": rule["message"].format(**metrics),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        
        # Envoyer via tous les canaux configurés
        for channel_name, notifier in self.notification_channels.items():
            try:
                notifier.send_alert(alert)
            except Exception as e:
                print(f"Erreur envoi alerte via {channel_name}: {e}")
        
        print(f"🚨 ALERTE [{rule['severity'].upper()}]: {alert['message']}")

class EmailNotifier:
    """Notificateur email"""
    def send_alert(self, alert: Dict[str, Any]):
        # Implémentation email
        pass

class SlackNotifier:
    """Notificateur Slack"""
    def send_alert(self, alert: Dict[str, Any]):
        # Implémentation Slack webhook
        pass

class WebhookNotifier:
    """Notificateur webhook générique"""
    def send_alert(self, alert: Dict[str, Any]):
        # Implémentation webhook
        pass

# Instance globale
alert_manager = AlertManager()
```

## 📊 Dashboard de Monitoring

### Métriques Temps Réel

```python
class MonitoringDashboard:
    """Dashboard de monitoring en temps réel"""
    
    def __init__(self):
        self.refresh_interval = 30  # secondes
        self.historical_data = []
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Génère les données pour le dashboard"""
        
        # Récupérer les métriques actuelles
        current_metrics = self._collect_current_metrics()
        
        # Calculer les tendances
        trends = self._calculate_trends()
        
        # Préparer les graphiques
        charts_data = self._prepare_charts_data()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "refresh_interval": self.refresh_interval,
            "current_metrics": current_metrics,
            "trends": trends,
            "charts": charts_data,
            "alerts": self._get_active_alerts(),
            "health_summary": self._get_health_summary()
        }
    
    def _collect_current_metrics(self) -> Dict[str, Any]:
        """Collecte les métriques actuelles"""
        try:
            response = requests.get(f"{base_url}/metrics")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calcule les tendances sur les dernières heures"""
        if len(self.historical_data) < 2:
            return {}
        
        current = self.historical_data[-1]
        previous = self.historical_data[-2]
        
        return {
            "requests_trend": self._calculate_percentage_change(
                current.get("total_requests", 0),
                previous.get("total_requests", 0)
            ),
            "error_rate_trend": self._calculate_difference(
                current.get("error_rate", 0),
                previous.get("error_rate", 0)
            ),
            "response_time_trend": self._calculate_percentage_change(
                current.get("average_response_time", 0),
                previous.get("average_response_time", 0)
            ),
            "cost_trend": self._calculate_percentage_change(
                current.get("total_cost", 0),
                previous.get("total_cost", 0)
            )
        }
    
    def _prepare_charts_data(self) -> Dict[str, Any]:
        """Prépare les données pour les graphiques"""
        return {
            "response_time_chart": self._prepare_response_time_chart(),
            "provider_usage_chart": self._prepare_provider_usage_chart(),
            "cost_evolution_chart": self._prepare_cost_chart(),
            "session_activity_chart": self._prepare_session_activity_chart()
        }
    
    def start_monitoring(self):
        """Démarre le monitoring continu"""
        while True:
            try:
                dashboard_data = self.generate_dashboard_data()
                
                # Stocker dans l'historique
                self.historical_data.append(dashboard_data["current_metrics"])
                
                # Limiter l'historique à 24h (avec refresh toutes les 30s = 2880 points)
                if len(self.historical_data) > 2880:
                    self.historical_data = self.historical_data[-2880:]
                
                # Vérifier les alertes
                alert_manager.check_alerts(dashboard_data["current_metrics"])
                
                # Attendre l'intervalle suivant
                time.sleep(self.refresh_interval)
                
            except Exception as e:
                print(f"Erreur monitoring: {e}")
                time.sleep(60)  # Attendre 1 minute en cas d'erreur

# Instance du dashboard
monitoring_dashboard = MonitoringDashboard()
```

## 📱 Monitoring Mobile/Web

### API pour Applications de Monitoring

```http
# Métriques simplifiées pour mobile
GET /api/metrics/mobile
```

```json
{
  "status": "healthy",
  "active_sessions": 142,
  "requests_per_minute": 87,
  "error_rate": 0.02,
  "top_provider": "openai",
  "cost_today": 156.78,
  "alerts_count": 2
}
```

### WebSocket pour Métriques Temps Réel

```javascript
// Client WebSocket pour monitoring temps réel
const ws = new WebSocket('ws://localhost:8000/ws/metrics');

ws.onmessage = function(event) {
    const metrics = JSON.parse(event.data);
    updateDashboard(metrics);
};

function updateDashboard(metrics) {
    document.getElementById('active-sessions').textContent = metrics.active_sessions;
    document.getElementById('requests-per-minute').textContent = metrics.requests_per_minute;
    document.getElementById('error-rate').textContent = (metrics.error_rate * 100).toFixed(2) + '%';
    
    // Mettre à jour les graphiques
    updateCharts(metrics.charts);
}
```

## 🔧 Configuration du Monitoring

### Variables d'Environnement

```env
# Configuration monitoring
MONITORING_ENABLED=true
METRICS_RETENTION_DAYS=30
ALERT_EMAIL=admin@company.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Seuils d'alerte
ALERT_RESPONSE_TIME_THRESHOLD=5.0
ALERT_ERROR_RATE_THRESHOLD=0.05
ALERT_COST_HOURLY_THRESHOLD=50.0

# Dashboard
DASHBOARD_REFRESH_INTERVAL=30
DASHBOARD_PORT=8001
```

### Script de Déploiement Monitoring

```bash
#!/bin/bash
# deploy_monitoring.sh

echo "🚀 Déploiement du système de monitoring..."

# 1. Créer les répertoires
mkdir -p monitoring/{logs,config,data}

# 2. Copier les configurations
cp monitoring_config.json monitoring/config/

# 3. Démarrer les services
python -m monitoring.dashboard &
python -m monitoring.alerter &
python -m monitoring.collector &

echo "✅ Monitoring déployé avec succès"
echo "📊 Dashboard: http://localhost:8001"
echo "🚨 Alertes: configurées via email/slack"
```

## 📋 Checklist de Monitoring

### ✅ Configuration de Base

- [ ] Health checks activés pour tous les providers
- [ ] Métriques collectées et stockées
- [ ] Dashboard accessible et fonctionnel
- [ ] Alertes configurées et testées
- [ ] Logs centralisés et analysables

### ✅ Monitoring Avancé

- [ ] Tendances et prédictions activées
- [ ] Métriques business configurées
- [ ] Monitoring des coûts en temps réel
- [ ] SLA tracking implémenté
- [ ] Rapports automatiques planifiés

### ✅ Alertes et Incidents

- [ ] Canaux de notification configurés
- [ ] Escalade automatique en place
- [ ] Playbooks d'incident définis
- [ ] Post-mortem automatisé
- [ ] Métriques de récupération trackées

---

## 📞 Support Monitoring

**Monitoring Support :** monitoring@yourcompany.com  
**Dashboard Issues :** https://status.orchestrator-agent.com  
**Documentation :** https://docs.orchestrator-agent.com/monitoring  

---

> 📊 **Un monitoring efficace est essentiel pour maintenir la performance et la fiabilité de votre plateforme Orchestrator Agent.** Ce système de métriques vous donne une visibilité complète sur tous les aspects de votre infrastructure IA.