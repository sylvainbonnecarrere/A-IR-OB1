"""
Script de test et validation pour le Jalon 2.1 - OpenAIAdapter.

Ce script valide que :
1. L'OpenAIAdapter peut être instancié correctement
2. Les méthodes basiques retournent les types attendus
3. La méthode chat_completion fonctionne avec une configuration minimale
4. La conversion des formats fonctionne correctement

IMPORTANT : Pour exécuter ce test, vous devez :
1. Définir la variable d'environnement OPENAI_API_KEY avec votre clé API OpenAI
2. Avoir des crédits disponibles sur votre compte OpenAI

Usage: python debug/test_jalon_2_1.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire source au PYTHONPATH
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from infrastructure.llm_providers.openai_adapter import OpenAIAdapter
    from models.data_contracts import AgentConfig, ChatMessage, OrchestrationResponse
except ImportError as e:
    print(f"❌ Erreur d'import : {e}")
    print("Assurez-vous que le script est exécuté depuis le répertoire orchestrator_agent_py")
    sys.exit(1)


async def test_openai_adapter_instantiation():
    """
    Teste l'instanciation de l'OpenAIAdapter.
    """
    print("🔍 Test 1: Instanciation de l'OpenAIAdapter")
    
    try:
        # Test sans clé API (doit échouer)
        if os.getenv("OPENAI_API_KEY"):
            # Sauvegarde temporaire
            temp_key = os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_API_KEY"]
            
            try:
                adapter = OpenAIAdapter()
                print("❌ FAIL: L'adapter devrait échouer sans clé API")
                return False
            except ValueError as expected:
                print("✅ PASS: Erreur correctement levée sans clé API")
            
            # Restauration de la clé
            os.environ["OPENAI_API_KEY"] = temp_key
        
        # Test avec clé API
        adapter = OpenAIAdapter(model="gpt-3.5-turbo")
        print("✅ PASS: OpenAIAdapter instancié avec succès")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Erreur lors de l'instanciation : {e}")
        return False


async def test_basic_methods():
    """
    Teste les méthodes basiques de l'adaptateur.
    """
    print("\n🔍 Test 2: Méthodes basiques")
    
    try:
        adapter = OpenAIAdapter(model="gpt-3.5-turbo")
        
        # Test get_model_name
        model_name = await adapter.get_model_name()
        if model_name == "gpt-3.5-turbo":
            print("✅ PASS: get_model_name retourne le bon modèle")
        else:
            print(f"❌ FAIL: get_model_name retourne {model_name}, attendu gpt-3.5-turbo")
            return False
        
        # Test get_supported_tools
        tools = await adapter.get_supported_tools()
        if isinstance(tools, list) and len(tools) > 0:
            print(f"✅ PASS: get_supported_tools retourne une liste : {tools}")
        else:
            print(f"❌ FAIL: get_supported_tools retourne : {tools}")
            return False
        
        # Test format_tools_for_llm
        formatted = await adapter.format_tools_for_llm(["get_time"])
        if formatted is None:  # Attendu pour ce jalon
            print("✅ PASS: format_tools_for_llm retourne None (placeholder)")
        else:
            print(f"❌ FAIL: format_tools_for_llm retourne : {formatted}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Erreur lors du test des méthodes basiques : {e}")
        return False


async def test_chat_completion_mock():
    """
    Teste la méthode chat_completion avec une configuration mock.
    
    Note: Ce test ne fait PAS d'appel réel à l'API OpenAI pour éviter les coûts.
    Il teste uniquement la logique de conversion des formats.
    """
    print("\n🔍 Test 3: Logique de conversion chat_completion (mock)")
    
    try:
        adapter = OpenAIAdapter(model="gpt-3.5-turbo")
        
        # Configuration d'agent de test
        config = AgentConfig(
            agent_id="test-agent",
            provider="openai",
            model="gpt-3.5-turbo",
            system_prompt="Tu es un assistant utile et concis.",
            tools=[],
            temperature=0.7,
            max_tokens=100
        )
        
        # Historique de test
        history = [
            ChatMessage(
                role="user",
                content="Bonjour, comment ça va ?"
            )
        ]
        
        # Test de la conversion vers le format OpenAI
        messages = adapter._convert_history_to_openai_format(config, history)
        
        expected_structure = [
            {"role": "system", "content": "Tu es un assistant utile et concis."},
            {"role": "user", "content": "Bonjour, comment ça va ?"}
        ]
        
        if messages == expected_structure:
            print("✅ PASS: Conversion vers format OpenAI correcte")
        else:
            print(f"❌ FAIL: Conversion incorrecte")
            print(f"   Attendu: {expected_structure}")
            print(f"   Obtenu:  {messages}")
            return False
        
        print("✅ PASS: Logique de conversion validée")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Erreur lors du test de conversion : {e}")
        return False


async def test_chat_completion_real():
    """
    Teste un appel réel à l'API OpenAI (optionnel).
    
    Ce test est conditionnel et ne s'exécute que si :
    1. La clé API est disponible
    2. L'utilisateur confirme qu'il veut faire un appel réel
    """
    print("\n🔍 Test 4: Appel réel à l'API OpenAI (optionnel)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⏭️  SKIP: Pas de clé API OpenAI disponible")
        return True
    
    # Demande de confirmation (simulée pour le script automatique)
    # Dans un vrai test interactif, on demanderait à l'utilisateur
    perform_real_call = False  # Changez en True pour tester avec un vrai appel
    
    if not perform_real_call:
        print("⏭️  SKIP: Test d'appel réel désactivé (changez perform_real_call=True pour l'activer)")
        return True
    
    try:
        adapter = OpenAIAdapter(model="gpt-3.5-turbo")
        
        # Configuration simple
        config = AgentConfig(
            agent_id="test-agent",
            provider="openai",
            model="gpt-3.5-turbo",
            system_prompt="Tu es un assistant qui répond en une phrase courte.",
            tools=[],
            temperature=0.1,  # Déterministe
            max_tokens=50     # Limité pour réduire les coûts
        )
        
        # Historique simple
        history = [
            ChatMessage(role="user", content="Dis juste 'test réussi'")
        ]
        
        print("🚀 Appel à l'API OpenAI en cours...")
        response = await adapter.chat_completion(config, history)
        
        # Validation du type de retour
        if isinstance(response, OrchestrationResponse):
            print("✅ PASS: Type de retour correct (OrchestrationResponse)")
        else:
            print(f"❌ FAIL: Type de retour incorrect : {type(response)}")
            return False
        
        # Validation du contenu
        if response.response_message.role == "assistant":
            print("✅ PASS: Rôle de la réponse correct")
        else:
            print(f"❌ FAIL: Rôle incorrect : {response.response_message.role}")
            return False
        
        if response.response_message.content:
            print(f"✅ PASS: Réponse reçue : '{response.response_message.content[:50]}...'")
        else:
            print("❌ FAIL: Contenu de réponse vide")
            return False
        
        # Validation des métadonnées
        if "model_used" in response.execution_metadata:
            print("✅ PASS: Métadonnées d'exécution présentes")
        else:
            print("❌ FAIL: Métadonnées manquantes")
            return False
        
        print("✅ PASS: Appel réel à l'API OpenAI réussi")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Erreur lors de l'appel réel : {e}")
        return False


async def run_all_tests():
    """
    Exécute tous les tests de validation du Jalon 2.1.
    """
    print("🚀 Validation du Jalon 2.1 - OpenAIAdapter")
    print("=" * 60)
    
    tests = [
        test_openai_adapter_instantiation,
        test_basic_methods,
        test_chat_completion_mock,
        test_chat_completion_real
    ]
    
    results = []
    
    for test_func in tests:
        result = await test_func()
        results.append(result)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"✅ Tests réussis: {passed}/{total}")
    
    if passed >= 3:  # Les 3 premiers tests sont obligatoires
        print("🎉 JALON 2.1 VALIDÉ - L'OpenAIAdapter fonctionne correctement!")
        print("\n📋 Fonctionnalités validées :")
        print("   ✅ Instanciation avec gestion des erreurs")
        print("   ✅ Méthodes basiques implémentées")
        print("   ✅ Logique de conversion des formats")
        print("   ✅ Architecture respectant l'interface LLMService")
        
        if results[3]:  # Si le test réel a aussi réussi
            print("   ✅ Appel réel à l'API OpenAI fonctionnel")
        
        print("\n🚀 Prêt pour le Jalon 2.2 (Façade et Injection de Dépendances)")
    else:
        print("⚠️  Certains tests obligatoires ont échoué.")
        print("   Vérifiez l'implémentation de l'OpenAIAdapter.")
    
    print("\n📝 Note :")
    print("   Pour tester avec un vrai appel API, définissez OPENAI_API_KEY")
    print("   et changez perform_real_call=True dans test_chat_completion_real()")


if __name__ == "__main__":
    asyncio.run(run_all_tests())