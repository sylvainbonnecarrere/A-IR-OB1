"""
Exemple d'utilisation de l'OpenAIAdapter - Jalon 2.1

Ce script démontre comment utiliser l'OpenAIAdapter dans un contexte réel.
Il montre l'instanciation, la configuration et un appel de base.

ATTENTION : Ce script nécessite une clé API OpenAI valide !
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire source au PYTHONPATH
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from infrastructure.llm_providers.openai_adapter import OpenAIAdapter
from models.data_contracts import AgentConfig, ChatMessage


async def example_simple_chat():
    """
    Exemple basique d'utilisation de l'OpenAIAdapter.
    """
    print("🤖 Exemple d'utilisation de l'OpenAIAdapter")
    print("=" * 50)
    
    # Vérification de la clé API
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Clé API OpenAI manquante.")
        print("   Définissez la variable d'environnement OPENAI_API_KEY")
        print("   ou modifiez le script pour passer la clé directement.")
        return
    
    try:
        # 1. Instanciation de l'adaptateur
        print("📍 1. Instanciation de l'OpenAIAdapter")
        adapter = OpenAIAdapter(model="gpt-3.5-turbo")
        print(f"   ✅ Adaptateur créé avec le modèle : {await adapter.get_model_name()}")
        
        # 2. Configuration de l'agent
        print("\n📍 2. Configuration de l'agent")
        config = AgentConfig(
            agent_id="demo-assistant",
            provider="openai",
            model="gpt-3.5-turbo",
            system_prompt="Tu es un assistant Python qui explique le code de manière concise et claire.",
            tools=[],
            temperature=0.3,  # Réponses plus déterministes
            max_tokens=150    # Réponses courtes
        )
        print(f"   ✅ Agent configuré : {config.agent_id}")
        
        # 3. Préparation de l'historique
        print("\n📍 3. Préparation de l'historique de conversation")
        history = [
            ChatMessage(
                role="user", 
                content="Explique-moi en 2 phrases ce qu'est un adaptateur en architecture logicielle."
            )
        ]
        print(f"   ✅ Historique préparé avec {len(history)} message(s)")
        
        # 4. Appel à l'adaptateur
        print("\n📍 4. Appel à l'OpenAI API")
        print("   🚀 Envoi de la requête...")
        
        response = await adapter.chat_completion(config, history)
        
        # 5. Affichage des résultats
        print("\n📍 5. Réponse reçue")
        print(f"   ✅ Rôle : {response.response_message.role}")
        print(f"   💬 Contenu : {response.response_message.content}")
        
        print(f"\n📊 Métadonnées d'exécution :")
        for key, value in response.execution_metadata.items():
            print(f"   📈 {key} : {value}")
        
        print(f"\n📜 Historique mis à jour : {len(response.updated_history)} messages")
        
        print("\n" + "=" * 50)
        print("🎉 Exemple terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exemple : {e}")
        print("   Vérifiez votre clé API et votre connexion internet.")


async def example_multi_turn_conversation():
    """
    Exemple de conversation multi-tours.
    """
    print("\n\n🔄 Exemple de conversation multi-tours")
    print("=" * 50)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Clé API manquante - exemple ignoré")
        return
    
    try:
        adapter = OpenAIAdapter(model="gpt-3.5-turbo")
        
        config = AgentConfig(
            agent_id="multi-turn-assistant",
            provider="openai",
            model="gpt-3.5-turbo",
            system_prompt="Tu es un assistant qui se souvient du contexte et répond brièvement.",
            temperature=0.5,
            max_tokens=100
        )
        
        # Simulation d'une conversation
        conversation_history = []
        
        messages = [
            "Bonjour ! Comment t'appelles-tu ?",
            "Peux-tu me rappeler ce que tu fais ?",
            "Merci pour les explications !"
        ]
        
        for i, user_message in enumerate(messages, 1):
            print(f"\n💬 Tour {i} - Utilisateur : {user_message}")
            
            # Ajout du message utilisateur
            conversation_history.append(ChatMessage(role="user", content=user_message))
            
            # Appel à l'adaptateur
            response = await adapter.chat_completion(config, conversation_history)
            
            # Mise à jour de l'historique
            conversation_history = response.updated_history
            
            print(f"🤖 Assistant : {response.response_message.content}")
        
        print(f"\n📊 Conversation terminée avec {len(conversation_history)} messages au total")
        
    except Exception as e:
        print(f"❌ Erreur dans la conversation : {e}")


if __name__ == "__main__":
    print("🚀 Exemples d'utilisation de l'OpenAIAdapter - Jalon 2.1")
    print("Ces exemples nécessitent une clé API OpenAI valide.")
    print("Définissez OPENAI_API_KEY ou modifiez le code pour inclure votre clé.\n")
    
    asyncio.run(example_simple_chat())
    
    # Exemple de conversation multi-tours (commenté pour éviter les coûts)
    # asyncio.run(example_multi_turn_conversation())