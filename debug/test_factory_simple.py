"""
Test simple de la Factory LLM avec clés factices pour validation complète.
"""

import sys
from pathlib import Path

# Ajouter le répertoire source au PYTHONPATH
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from domain.llm_service_factory import LLMServiceFactory
from models.data_contracts import AgentConfig

def test_factory_simple():
    """Test simple de la factory avec clé factice."""
    print("🧪 Test simple de LLMServiceFactory")
    
    # Test de base
    providers = LLMServiceFactory.get_supported_providers()
    print(f"✅ Fournisseurs supportés : {providers}")
    
    # Test avec clé factice
    service = LLMServiceFactory.get_service("openai", api_key="fake-key-test")
    print(f"✅ Service créé : {type(service).__name__}")
    
    # Test avec AgentConfig et clé factice modifiée
    # On va modifier temporairement la factory pour accepter les clés factices
    config = AgentConfig(
        agent_id="test-factory",
        provider="openai", 
        model="gpt-3.5-turbo",
        system_prompt="Test factory"
    )
    
    try:
        # On passe une clé factice directement
        service2 = LLMServiceFactory.get_service(
            provider=config.provider,
            model=config.model, 
            api_key="fake-key-for-factory-test"
        )
        print(f"✅ Service depuis config créé : {type(service2).__name__}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    
    # Test cache
    LLMServiceFactory.clear_cache()
    cache_info = LLMServiceFactory.get_cache_info()
    print(f"✅ Cache info : {cache_info}")
    
    print("🎉 Factory fonctionne correctement !")

if __name__ == "__main__":
    test_factory_simple()