# 🔐 Guide de Sécurité - Configuration des API Keys

## Vue d'ensemble de la Sécurité

Ce guide détaille la configuration sécurisée des 8 fournisseurs LLM supportés par l'Orchestrator Agent, avec les meilleures pratiques de sécurité pour la gestion des clés API.

## 🔑 Configuration des Variables d'Environnement

### Variables Requises

| Provider | Variable d'Environnement | Format Attendu | Exemple |
|----------|-------------------------|----------------|---------|
| **OpenAI** | `OPENAI_API_KEY` | `sk-[a-zA-Z0-9]{48}` | `sk-proj-abc123...` |
| **Anthropic** | `ANTHROPIC_API_KEY` | `sk-ant-api03-[a-zA-Z0-9-_]{95}` | `sk-ant-api03-xyz789...` |
| **Google Gemini** | `GEMINI_API_KEY` | `AIzaSy[a-zA-Z0-9_-]{33}` | `AIzaSyABC123...` |
| **Mistral** | `MISTRAL_API_KEY` | `[a-zA-Z0-9]{32}` | `abcd1234efgh5678...` |
| **Grok (xAI)** | `GROK_API_KEY` | `xai-[a-zA-Z0-9]{40}` | `xai-abc123def456...` |
| **Qwen** | `QWEN_API_KEY` | `sk-[a-zA-Z0-9]{48}` | `sk-abc123def456...` |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `sk-[a-zA-Z0-9]{48}` | `sk-abc123def456...` |
| **Kimi K2** | `KIMI_K2_API_KEY` | `sk-[a-zA-Z0-9]{48}` | `sk-abc123def456...` |

### Fichier .env Sécurisé

```env
# ===================================================
# 🔐 ORCHESTRATOR AGENT - CONFIGURATION SÉCURISÉE
# ===================================================

# 🤖 OpenAI Configuration
# Utilisé pour: GPT-3.5-turbo, GPT-4, GPT-4o, O1-preview
OPENAI_API_KEY=sk-proj-your_openai_key_here
OPENAI_ORG_ID=org-your_org_id_here  # Optionnel

# 🧠 Anthropic Configuration  
# Utilisé pour: Claude 3.5 Sonnet, Claude 3.5 Haiku
ANTHROPIC_API_KEY=sk-ant-api03-your_anthropic_key_here

# 🔍 Google Gemini Configuration
# Utilisé pour: Gemini 1.5 Pro, Gemini 1.5 Flash
GEMINI_API_KEY=AIzaSyYour_gemini_key_here

# 🎯 Mistral Configuration
# Utilisé pour: Mistral Large, Mistral Small
MISTRAL_API_KEY=your_mistral_key_here

# 🚀 Grok (xAI) Configuration
# Utilisé pour: Grok-beta
GROK_API_KEY=xai-your_grok_key_here

# 🏮 Qwen Configuration
# Utilisé pour: Qwen-turbo, Qwen-plus
QWEN_API_KEY=sk-your_qwen_key_here

# 🔬 DeepSeek Configuration
# Utilisé pour: DeepSeek V3
DEEPSEEK_API_KEY=sk-your_deepseek_key_here

# 🌙 Kimi K2 Configuration
# Utilisé pour: Moonshot V1
KIMI_K2_API_KEY=sk-your_kimi_k2_key_here

# ===================================================
# 🛡️ CONFIGURATION DE SÉCURITÉ AVANCÉE
# ===================================================

# Limitation de rate (optionnel)
MAX_REQUESTS_PER_MINUTE=100
SESSION_TIMEOUT_MINUTES=30

# Monitoring et alertes
ENABLE_API_MONITORING=true
ALERT_EMAIL=admin@yourcompany.com

# Environnement
ENVIRONMENT=production  # development, staging, production
DEBUG_MODE=false
```

## 🛡️ Sécurité par Niveau d'Environnement

### 🔧 Développement Local

```bash
# Fichier .env.development
OPENAI_API_KEY=sk-dev-your_dev_key
ANTHROPIC_API_KEY=sk-ant-dev-your_dev_key
# ... autres clés de développement

# Variables de debug activées
DEBUG_MODE=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### 🧪 Environnement de Test

```bash
# Fichier .env.testing
# Utilisation de clés API limitées pour les tests
OPENAI_API_KEY=sk-test-limited_key
ANTHROPIC_API_KEY=sk-ant-test-limited_key

# Limitations strictes pour les tests
MAX_TOKENS_PER_REQUEST=100
RATE_LIMIT_TEST=10
```

### 🚀 Production

```bash
# Configuration via gestionnaire de secrets cloud
# AWS Secrets Manager, Azure Key Vault, Google Secret Manager

# Variables d'environnement injectées par l'orchestrateur
# Kubernetes secrets, Docker secrets, etc.

# Aucune clé en clair dans les fichiers !
```

## 🏢 Gestionnaires de Secrets Cloud

### AWS Secrets Manager

```python
import boto3
import json

def get_llm_secrets():
    """Récupère les clés API depuis AWS Secrets Manager"""
    secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        response = secrets_client.get_secret_value(SecretId='orchestrator-agent/llm-keys')
        secrets = json.loads(response['SecretString'])
        
        return {
            'OPENAI_API_KEY': secrets.get('openai_key'),
            'ANTHROPIC_API_KEY': secrets.get('anthropic_key'),
            'GEMINI_API_KEY': secrets.get('gemini_key'),
            # ... autres clés
        }
    except Exception as e:
        print(f"Erreur récupération secrets: {e}")
        return {}

# Configuration dans main.py
if os.getenv('ENVIRONMENT') == 'production':
    secrets = get_llm_secrets()
    for key, value in secrets.items():
        os.environ[key] = value
```

### Azure Key Vault

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_azure_secrets():
    """Récupère les clés depuis Azure Key Vault"""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url="https://orchestrator-kv.vault.azure.net/", credential=credential)
    
    secrets = {}
    secret_names = [
        'openai-api-key', 'anthropic-api-key', 'gemini-api-key',
        'mistral-api-key', 'grok-api-key', 'qwen-api-key',
        'deepseek-api-key', 'kimi-k2-api-key'
    ]
    
    for secret_name in secret_names:
        try:
            secret = client.get_secret(secret_name)
            env_name = secret_name.upper().replace('-', '_')
            secrets[env_name] = secret.value
        except Exception as e:
            print(f"Erreur récupération {secret_name}: {e}")
    
    return secrets
```

### Google Secret Manager

```python
from google.cloud import secretmanager

def get_google_secrets():
    """Récupère les clés depuis Google Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    project_id = "your-project-id"
    
    secrets = {}
    secret_names = [
        'openai-api-key', 'anthropic-api-key', 'gemini-api-key',
        'mistral-api-key', 'grok-api-key', 'qwen-api-key',
        'deepseek-api-key', 'kimi-k2-api-key'
    ]
    
    for secret_name in secret_names:
        try:
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            env_name = secret_name.upper().replace('-', '_')
            secrets[env_name] = secret_value
        except Exception as e:
            print(f"Erreur récupération {secret_name}: {e}")
    
    return secrets
```

## 🔍 Validation et Monitoring des Clés

### Validation Automatique

```python
import re
from typing import Optional, Dict, Any

class APIKeyValidator:
    """Validateur de format des clés API"""
    
    PATTERNS = {
        'openai': r'^sk-[a-zA-Z0-9]{48}$',
        'anthropic': r'^sk-ant-api03-[a-zA-Z0-9\-_]{95}$',
        'gemini': r'^AIzaSy[a-zA-Z0-9_\-]{33}$',
        'mistral': r'^[a-zA-Z0-9]{32}$',
        'grok': r'^xai-[a-zA-Z0-9]{40}$',
        'qwen': r'^sk-[a-zA-Z0-9]{48}$',
        'deepseek': r'^sk-[a-zA-Z0-9]{48}$',
        'kimi_k2': r'^sk-[a-zA-Z0-9]{48}$'
    }
    
    @classmethod
    def validate_key(cls, provider: str, api_key: str) -> bool:
        """Valide le format d'une clé API"""
        if not api_key or provider not in cls.PATTERNS:
            return False
        
        pattern = cls.PATTERNS[provider]
        return bool(re.match(pattern, api_key))
    
    @classmethod
    def validate_all_keys(cls) -> Dict[str, Any]:
        """Valide toutes les clés configurées"""
        results = {}
        
        for provider, pattern in cls.PATTERNS.items():
            env_var = f"{provider.upper()}_API_KEY"
            api_key = os.getenv(env_var)
            
            results[provider] = {
                'configured': api_key is not None,
                'valid_format': cls.validate_key(provider, api_key) if api_key else False,
                'length': len(api_key) if api_key else 0
            }
        
        return results

# Utilisation au démarrage
def startup_security_check():
    """Vérifications de sécurité au démarrage"""
    validation_results = APIKeyValidator.validate_all_keys()
    
    invalid_keys = []
    for provider, result in validation_results.items():
        if result['configured'] and not result['valid_format']:
            invalid_keys.append(provider)
    
    if invalid_keys:
        raise ValueError(f"Clés API invalides détectées: {invalid_keys}")
    
    print("✅ Validation des clés API réussie")
    return validation_results
```

### Monitoring des Usages

```python
import time
from collections import defaultdict
from datetime import datetime, timedelta

class APIUsageMonitor:
    """Moniteur d'usage des APIs"""
    
    def __init__(self):
        self.usage_stats = defaultdict(lambda: {
            'requests_count': 0,
            'tokens_used': 0,
            'errors_count': 0,
            'last_request': None,
            'cost_estimate': 0.0
        })
    
    def record_request(self, provider: str, tokens_used: int = 0, 
                      cost: float = 0.0, error: bool = False):
        """Enregistre une utilisation d'API"""
        stats = self.usage_stats[provider]
        stats['requests_count'] += 1
        stats['tokens_used'] += tokens_used
        stats['cost_estimate'] += cost
        stats['last_request'] = datetime.now()
        
        if error:
            stats['errors_count'] += 1
    
    def get_daily_report(self) -> Dict[str, Any]:
        """Génère un rapport quotidien d'usage"""
        return {
            'timestamp': datetime.now().isoformat(),
            'providers': dict(self.usage_stats),
            'total_requests': sum(stats['requests_count'] for stats in self.usage_stats.values()),
            'total_cost': sum(stats['cost_estimate'] for stats in self.usage_stats.values()),
            'total_errors': sum(stats['errors_count'] for stats in self.usage_stats.values())
        }
    
    def check_rate_limits(self, provider: str, max_requests_per_hour: int = 100) -> bool:
        """Vérifie les limites de taux"""
        stats = self.usage_stats[provider]
        if not stats['last_request']:
            return True
        
        hour_ago = datetime.now() - timedelta(hours=1)
        # Logique simplifiée - en production, utiliser une vraie fenêtre glissante
        return stats['requests_count'] < max_requests_per_hour

# Instance globale
usage_monitor = APIUsageMonitor()
```

## 🚨 Alertes de Sécurité

### Configuration des Alertes

```python
import smtplib
from email.mime.text import MIMEText
from typing import List

class SecurityAlerter:
    """Système d'alertes de sécurité"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        
        # Seuils d'alerte
        self.thresholds = {
            'error_rate': 0.05,  # 5% d'erreurs
            'requests_per_minute': 100,
            'unusual_cost_spike': 10.0,  # $10/heure
            'failed_auth_attempts': 5
        }
    
    def send_alert(self, subject: str, message: str, recipients: List[str]):
        """Envoie une alerte par email"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"🚨 ORCHESTRATOR SECURITY ALERT: {subject}"
            msg['From'] = self.email
            msg['To'] = ', '.join(recipients)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
                
            print(f"✅ Alerte envoyée: {subject}")
        except Exception as e:
            print(f"❌ Erreur envoi alerte: {e}")
    
    def check_security_metrics(self, metrics: Dict[str, Any]):
        """Vérifie les métriques de sécurité"""
        alerts = []
        
        # Vérification du taux d'erreur
        total_requests = metrics.get('total_requests', 0)
        total_errors = metrics.get('total_errors', 0)
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > self.thresholds['error_rate']:
                alerts.append(f"Taux d'erreur élevé: {error_rate:.2%}")
        
        # Vérification des coûts
        total_cost = metrics.get('total_cost', 0)
        if total_cost > self.thresholds['unusual_cost_spike']:
            alerts.append(f"Pic de coût inhabituel: ${total_cost:.2f}")
        
        # Envoyer les alertes
        if alerts:
            message = "Anomalies détectées:\n" + "\n".join(f"- {alert}" for alert in alerts)
            self.send_alert("Anomalies Détectées", message, ["admin@company.com"])

# Configuration
security_alerter = SecurityAlerter(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    email=os.getenv("ALERT_EMAIL"),
    password=os.getenv("ALERT_EMAIL_PASSWORD")
)
```

## 🔄 Rotation des Clés

### Script de Rotation Automatisée

```python
import schedule
import time
from datetime import datetime, timedelta

class KeyRotationManager:
    """Gestionnaire de rotation des clés"""
    
    def __init__(self):
        self.rotation_schedule = {
            'openai': timedelta(days=30),
            'anthropic': timedelta(days=30),
            'gemini': timedelta(days=30),
            'mistral': timedelta(days=30),
            'grok': timedelta(days=30),
            'qwen': timedelta(days=30),
            'deepseek': timedelta(days=30),
            'kimi_k2': timedelta(days=30)
        }
        
        self.last_rotation = {}
    
    def should_rotate_key(self, provider: str) -> bool:
        """Détermine si une clé doit être renouvelée"""
        if provider not in self.last_rotation:
            return True
        
        last_rotation = self.last_rotation[provider]
        rotation_interval = self.rotation_schedule[provider]
        
        return datetime.now() - last_rotation > rotation_interval
    
    def rotate_key(self, provider: str):
        """Effectue la rotation d'une clé"""
        print(f"🔄 Rotation de la clé {provider}...")
        
        # 1. Générer nouvelle clé via API du provider
        # 2. Mettre à jour le gestionnaire de secrets
        # 3. Tester la nouvelle clé
        # 4. Désactiver l'ancienne clé
        # 5. Notifier les équipes
        
        self.last_rotation[provider] = datetime.now()
        print(f"✅ Clé {provider} renouvelée avec succès")
    
    def check_all_keys(self):
        """Vérifie et renouvelle toutes les clés nécessaires"""
        for provider in self.rotation_schedule:
            if self.should_rotate_key(provider):
                self.rotate_key(provider)

# Planification automatique
rotation_manager = KeyRotationManager()
schedule.every().week.do(rotation_manager.check_all_keys)

def run_rotation_scheduler():
    """Lance le planificateur de rotation"""
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Vérification chaque heure
```

## 🔒 Checklist de Sécurité

### ✅ Configuration Initiale

- [ ] Toutes les 8 clés API configurées
- [ ] Validation des formats de clés
- [ ] Fichier .env ajouté à .gitignore
- [ ] Gestionnaire de secrets configuré (prod)
- [ ] Permissions d'accès restreintes

### ✅ Monitoring

- [ ] Système d'alertes configuré
- [ ] Métriques d'usage activées
- [ ] Logs sécurisés (pas de clés en clair)
- [ ] Monitoring des taux d'erreur
- [ ] Surveillance des coûts

### ✅ Sécurité Opérationnelle

- [ ] Rotation automatique des clés
- [ ] Backup des configurations
- [ ] Tests de basculement
- [ ] Documentation à jour
- [ ] Formation équipes

### ✅ Conformité

- [ ] Audit de sécurité régulier
- [ ] Respect RGPD/CCPA
- [ ] Logs d'audit complets
- [ ] Certification sécurité
- [ ] Politique de rétention des données

---

## 📞 Support Sécurité

**Contact Sécurité :** security@yourcompany.com  
**Urgences 24/7 :** +1-XXX-XXX-XXXX  
**Documentation :** https://docs.orchestrator-agent.com/security  

---

> 🛡️ **La sécurité n'est pas une option, c'est une nécessité.** Ce guide assure une configuration sécurisée de votre plateforme Orchestrator Agent.