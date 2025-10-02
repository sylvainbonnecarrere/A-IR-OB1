"""
Module utilitaire pour la validation et la gestion sécurisée des clés API.

Ce module fournit des fonctions pour :
- Valider le format des clés API
- Masquer les clés dans les logs et exceptions
- Gérer les erreurs de configuration de manière sécurisée
"""

import re
import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)


class APIKeyError(Exception):
    """Exception levée lors de problèmes de validation des clés API"""
    pass


class ProviderType(Enum):
    """Types de fournisseurs LLM supportés"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    GROK = "grok"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    KIMI_K2 = "kimi_k2"


class APIKeyValidator:
    """Validateur de clés API avec patterns de format spécifiques"""
    
    # Patterns de validation pour chaque fournisseur (relaxés pour compatibilité)
    VALIDATION_PATTERNS = {
        ProviderType.OPENAI: r'^sk-[a-zA-Z0-9]{40,}$',
        ProviderType.ANTHROPIC: r'^sk-ant-api03-[a-zA-Z0-9\-_]{95}$',
        ProviderType.GEMINI: r'^AIza[a-zA-Z0-9_\-]{33,}$',  # Support AIza et AIzaSy
        ProviderType.MISTRAL: r'^[a-zA-Z0-9]{32}$',
        ProviderType.GROK: r'^xai-[a-zA-Z0-9]{40}$',
        ProviderType.QWEN: r'^sk-[a-zA-Z0-9]{40,}$',
        ProviderType.DEEPSEEK: r'^sk-[a-zA-Z0-9]{40,}$',
        ProviderType.KIMI_K2: r'^sk-[a-zA-Z0-9]{40,}$'
    }
    
    # Longueurs minimales attendues
    MIN_LENGTHS = {
        ProviderType.OPENAI: 45,
        ProviderType.ANTHROPIC: 100,
        ProviderType.GEMINI: 35,
        ProviderType.MISTRAL: 32,
        ProviderType.GROK: 45,
        ProviderType.QWEN: 45,
        ProviderType.DEEPSEEK: 45,
        ProviderType.KIMI_K2: 45
    }
    
    @classmethod
    def validate_api_key(cls, provider: ProviderType, api_key: Optional[str]) -> bool:
        """
        Valide le format d'une clé API pour un fournisseur donné.
        
        Args:
            provider: Type de fournisseur
            api_key: Clé API à valider
            
        Returns:
            bool: True si la clé est valide, False sinon
        """
        if not api_key:
            return False
            
        # Vérification de la longueur minimale
        min_length = cls.MIN_LENGTHS.get(provider, 20)
        if len(api_key) < min_length:
            return False
            
        # Vérification du pattern spécifique
        pattern = cls.VALIDATION_PATTERNS.get(provider)
        if pattern and not re.match(pattern, api_key):
            return False
            
        return True
    
    @classmethod
    def get_env_var_name(cls, provider: ProviderType) -> str:
        """
        Retourne le nom de la variable d'environnement pour un fournisseur.
        
        Args:
            provider: Type de fournisseur
            
        Returns:
            str: Nom de la variable d'environnement
        """
        return f"{provider.value.upper()}_API_KEY"


class SecureAPIKeyHandler:
    """Gestionnaire sécurisé des clés API avec masquage et validation"""
    
    @staticmethod
    def mask_api_key(api_key: Optional[str]) -> str:
        """
        Masque une clé API pour l'affichage dans les logs.
        
        Args:
            api_key: Clé API à masquer
            
        Returns:
            str: Clé masquée pour affichage sécurisé
        """
        if not api_key:
            return "[NO_KEY]"
            
        if len(api_key) < 8:
            return "[INVALID_KEY]"
            
        # Affiche les 4 premiers et 4 derniers caractères avec masquage au milieu
        return f"{api_key[:4]}****{api_key[-4:]}"
    
    @staticmethod
    def load_and_validate_api_key(provider: ProviderType, api_key: Optional[str] = None) -> str:
        """
        Charge et valide une clé API depuis l'environnement ou le paramètre.
        
        Args:
            provider: Type de fournisseur
            api_key: Clé API optionnelle (sinon chargée depuis l'environnement)
            
        Returns:
            str: Clé API validée
            
        Raises:
            APIKeyError: Si la clé est manquante ou invalide
        """
        # Charger depuis l'environnement si non fournie
        if not api_key:
            env_var = APIKeyValidator.get_env_var_name(provider)
            api_key = os.getenv(env_var)
        
        # Vérifier la présence
        if not api_key:
            env_var = APIKeyValidator.get_env_var_name(provider)
            raise APIKeyError(
                f"Clé API manquante pour {provider.value}. "
                f"Veuillez configurer la variable d'environnement {env_var}"
            )
        
        # Valider le format
        if not APIKeyValidator.validate_api_key(provider, api_key):
            masked_key = SecureAPIKeyHandler.mask_api_key(api_key)
            min_length = APIKeyValidator.MIN_LENGTHS.get(provider, 20)
            raise APIKeyError(
                f"Clé API invalide pour {provider.value} (clé: {masked_key}). "
                f"Format attendu: pattern spécifique au fournisseur, "
                f"longueur minimale: {min_length} caractères"
            )
        
        # Logger la configuration réussie (avec masquage)
        masked_key = SecureAPIKeyHandler.mask_api_key(api_key)
        logger.info(f"Clé API {provider.value} configurée avec succès (clé: {masked_key})")
        
        return api_key
    
    @staticmethod
    def get_secure_config_info(provider: ProviderType, api_key: str) -> Dict[str, Any]:
        """
        Retourne des informations sécurisées sur la configuration d'une clé API.
        
        Args:
            provider: Type de fournisseur
            api_key: Clé API configurée
            
        Returns:
            Dict: Informations de configuration masquées
        """
        return {
            "provider": provider.value,
            "key_configured": True,
            "key_masked": SecureAPIKeyHandler.mask_api_key(api_key),
            "key_length": len(api_key),
            "key_valid": APIKeyValidator.validate_api_key(provider, api_key),
            "env_var": APIKeyValidator.get_env_var_name(provider)
        }


def create_secure_client_info(provider: ProviderType, client_status: str, 
                            additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Crée des informations sécurisées sur l'état d'un client LLM.
    
    Args:
        provider: Type de fournisseur
        client_status: Statut du client ("initialized", "failed", etc.)
        additional_info: Informations supplémentaires (optionnel)
        
    Returns:
        Dict: Informations de statut sécurisées
    """
    info = {
        "provider": provider.value,
        "status": client_status,
        "timestamp": None  # Sera rempli par le client
    }
    
    if additional_info:
        # S'assurer qu'aucune information sensible n'est incluse
        safe_info = {k: v for k, v in additional_info.items() 
                    if k not in ['api_key', 'secret', 'token', 'password']}
        info.update(safe_info)
    
    return info


# Configuration du logging sécurisé pour ce module
def configure_secure_logging():
    """Configure le logging pour masquer automatiquement les clés API"""
    
    class SecureFormatter(logging.Formatter):
        """Formatter qui masque automatiquement les clés API dans les logs"""
        
        def format(self, record):
            msg = super().format(record)
            
            # Patterns pour détecter et masquer les clés API
            patterns = [
                (r'sk-[a-zA-Z0-9]{40,}', lambda m: f"sk-****{m.group()[-4:]}"),
                (r'sk-ant-api03-[a-zA-Z0-9\-_]{95}', lambda m: f"sk-ant-****{m.group()[-4:]}"),
                (r'AIzaSy[a-zA-Z0-9_\-]{33}', lambda m: f"AIzaSy****{m.group()[-4:]}"),
                (r'xai-[a-zA-Z0-9]{40}', lambda m: f"xai-****{m.group()[-4:]}")
            ]
            
            for pattern, replacement in patterns:
                msg = re.sub(pattern, replacement, msg)
            
            return msg
    
    # Appliquer le formatter sécurisé au logger principal
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(SecureFormatter())


# Auto-configuration du logging sécurisé à l'import
configure_secure_logging()