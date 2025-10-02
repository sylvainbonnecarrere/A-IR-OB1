"""
Agent Router - Moteur de Décision pour l'Orchestration Multi-Agents

Ce module implémente le routeur intelligent qui précède l'AgentOrchestrator.
Il utilise le Function Calling d'un LLM pour analyser l'intention utilisateur
et sélectionner l'agent spécialisé le plus approprié.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from src.domain.llm_service_interface import LLMServiceInterface
from src.domain.tracer import Tracer  # JALON 4.1-B: Intégration du traçage
from src.models.data_contracts import (
    ChatMessage, 
    AgentDefinition,
    ToolDefinition,
    OrchestrationRequest,
    OrchestrationResponse
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentSelectionTool(ToolDefinition):
    """
    Outil spécialisé pour la sélection d'agent par le routeur LLM
    
    Cet outil sera généré dynamiquement en fonction des agents disponibles
    et utilisé par le LLM de routage pour choisir l'agent approprié.
    """
    name: str = "select_agent"
    description: str = "Sélectionne l'agent le plus approprié pour traiter la requête utilisateur"
    agent_name: str = ""  # Paramètre qui sera rempli par le LLM
    
    @classmethod
    def create_for_agents(cls, available_agents: List[AgentDefinition]) -> Dict[str, Any]:
        """
        Crée le schéma d'outil dynamique basé sur les agents disponibles
        
        Args:
            available_agents: Liste des agents disponibles pour la sélection
            
        Returns:
            Dict: Schéma d'outil compatible Function Calling
        """
        # Construction de l'enum des agents disponibles
        agent_enum = [agent.agent_name for agent in available_agents]
        agent_descriptions = "\n".join([
            f"- {agent.agent_name}: {agent.description}"
            for agent in available_agents
        ])
        
        return {
            "type": "function",
            "function": {
                "name": "select_agent",
                "description": f"Sélectionne l'agent le plus approprié parmi les agents disponibles. Agents disponibles:\n{agent_descriptions}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "enum": agent_enum,
                            "description": "Nom de l'agent sélectionné pour traiter la requête"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explication du choix de l'agent (pour debug et transparence)"
                        }
                    },
                    "required": ["agent_name", "reasoning"]
                }
            }
        }


class AgentRouter:
    """
    Routeur intelligent pour l'orchestration multi-agents
    
    Cette classe implémente le moteur de décision qui analyse l'intention
    de l'utilisateur et sélectionne l'agent spécialisé le plus approprié
    via Function Calling avec un LLM rapide.
    """
    
    def __init__(self, llm_service: LLMServiceInterface):
        """
        Initialise le routeur avec un service LLM pour la prise de décision
        
        Args:
            llm_service: Service LLM configuré pour la décision de routage
                        (recommandé: modèle rapide comme gpt-3.5-turbo ou gemini-flash)
        """
        self.llm_service = llm_service
        self.router_system_prompt = """Tu es un routeur intelligent spécialisé dans la sélection d'agents.

Ta mission : analyser la requête utilisateur et choisir l'agent le plus approprié.

Consignes:
1. Lis attentivement la requête utilisateur
2. Analyse les capacités de chaque agent disponible
3. Sélectionne l'agent dont les compétences correspondent le mieux à la demande
4. Utilise OBLIGATOIREMENT la fonction select_agent pour ton choix
5. Justifie ton raisonnement de manière claire et concise

Si la requête est ambiguë, choisis l'agent le plus généraliste ou demande des clarifications."""

    async def dispatch(
        self, 
        user_message: ChatMessage, 
        available_agents: List[AgentDefinition],
        tracer: Optional[Tracer] = None  # JALON 4.1-B: Traçage optionnel
    ) -> AgentDefinition:
        """
        Sélectionne l'agent approprié pour traiter la requête utilisateur
        
        Args:
            user_message: Message de l'utilisateur à analyser
            available_agents: Liste des agents disponibles pour la sélection
            tracer: Tracer optionnel pour l'observabilité (JALON 4.1-B)
            
        Returns:
            AgentDefinition: L'agent sélectionné pour traiter la requête
            
        Raises:
            Exception: Si aucun agent ne peut être sélectionné ou si l'appel LLM échoue
        """
        if not available_agents:
            raise ValueError("Aucun agent disponible pour le routage")
        
        # JALON 4.1-B: Traçage du début du routage
        if tracer:
            await tracer.log_router_start(
                request_summary=user_message.content[:100] + ("..." if len(user_message.content) > 100 else "")
            )
        
        # Si un seul agent, pas besoin de routage
        if len(available_agents) == 1:
            selected_agent = available_agents[0]
            logger.info(f"Un seul agent disponible, sélection automatique: {selected_agent.agent_name}")
            
            # JALON 4.1-B: Traçage de la décision automatique
            if tracer:
                await tracer.log_router_decision(selected_agent.agent_name, confidence=1.0)
            
            return selected_agent
        
        logger.info(f"Routage en cours pour: '{user_message.content}' parmi {len(available_agents)} agents")
        
        try:
            # Création de l'outil de sélection dynamique
            selection_tool_schema = AgentSelectionTool.create_for_agents(available_agents)
            
            # Messages pour le LLM de routage
            routing_messages = [
                ChatMessage(role="system", content=self.router_system_prompt),
                ChatMessage(role="user", content=f"Requête à analyser: {user_message.content}")
            ]
            
            # Appel du LLM de routage avec Function Calling
            routing_request = OrchestrationRequest(
                message="",  # Le message est déjà dans l'historique
                agent_config=None,  # Utilise la config par défaut du routeur
                conversation_history=routing_messages
            )
            
            # Appel via orchestration_completion avec les outils
            response = await self._call_router_llm_with_tools(
                routing_messages, 
                [selection_tool_schema]
            )
            
            # Parser la réponse et extraire l'agent sélectionné
            selected_agent = self._extract_selected_agent(response, available_agents)
            
            # JALON 4.1-B: Traçage de la décision finale
            if tracer:
                await tracer.log_router_decision(selected_agent.agent_name)
            
            logger.info(f"Agent sélectionné: {selected_agent.agent_name}")
            return selected_agent
            
        except Exception as e:
            logger.error(f"Erreur lors du routage: {str(e)}")
            
            # JALON 4.1-B: Traçage de l'erreur
            if tracer:
                await tracer.log_error("AgentRouter", "routing_error", str(e))
            
            # Fallback : retourner le premier agent disponible
            fallback_agent = available_agents[0]
            logger.warning(f"Fallback vers le premier agent: {fallback_agent.agent_name}")
            
            # JALON 4.1-B: Traçage du fallback
            if tracer:
                await tracer.log_router_decision(fallback_agent.agent_name, confidence=0.0)
            
            return fallback_agent

    async def _call_router_llm_with_tools(
        self, 
        messages: List[ChatMessage], 
        tools: List[Dict[str, Any]]
    ) -> OrchestrationResponse:
        """
        Appelle le LLM de routage avec les outils de sélection
        
        Args:
            messages: Messages de conversation pour le routage
            tools: Outils de sélection d'agent
            
        Returns:
            OrchestrationResponse: Réponse du LLM avec appels d'outils
        """
        # Construction de la requête d'orchestration pour le routeur
        from src.models.data_contracts import AgentConfig, LLMProvider
        
        # Configuration légère pour le routeur (modèle rapide)
        router_config = AgentConfig(
            provider=LLMProvider.OPENAI,  # Utilise OpenAI par défaut
            model_version="gpt-3.5-turbo",  # Modèle rapide pour le routage
            temperature=0.1,  # Température basse pour cohérence
            max_tokens=200,  # Réponse courte suffisante
            tools_enabled=True,
            system_prompt=self.router_system_prompt
        )
        
        routing_request = OrchestrationRequest(
            message="",  # Message vide, tout est dans l'historique
            agent_config=router_config,
            conversation_history=messages
        )
        
        # Note: Pour une implémentation complète, on pourrait passer les tools
        # Ici on simule l'appel - dans la vraie implémentation, il faudrait
        # modifier orchestration_completion pour accepter des tools custom
        return await self.llm_service.orchestration_completion(routing_request)

    def _extract_selected_agent(
        self, 
        response: OrchestrationResponse, 
        available_agents: List[AgentDefinition]
    ) -> AgentDefinition:
        """
        Extrait l'agent sélectionné depuis la réponse du LLM de routage
        
        Args:
            response: Réponse du LLM contenant potentiellement des tool calls
            available_agents: Liste des agents disponibles
            
        Returns:
            AgentDefinition: Agent sélectionné
            
        Raises:
            Exception: Si aucun agent valide n'est trouvé dans la réponse
        """
        # Recherche d'un appel à select_agent dans les tool_calls
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.tool_name == "select_agent":
                    selected_name = tool_call.arguments.get("agent_name")
                    reasoning = tool_call.arguments.get("reasoning", "Non spécifié")
                    
                    # Recherche de l'agent correspondant
                    for agent in available_agents:
                        if agent.agent_name == selected_name:
                            logger.info(f"Agent sélectionné via tool call: {selected_name}")
                            logger.info(f"Raisonnement: {reasoning}")
                            return agent
                    
                    logger.warning(f"Agent demandé non trouvé: {selected_name}")
        
        # Fallback: analyse du contenu textuel pour extraire un nom d'agent
        if response.content:
            content_lower = response.content.lower()
            for agent in available_agents:
                if agent.agent_name.lower() in content_lower:
                    logger.info(f"Agent détecté dans le contenu: {agent.agent_name}")
                    return agent
        
        # Dernier fallback: premier agent disponible
        logger.warning("Aucune sélection claire, utilisation du premier agent disponible")
        return available_agents[0]

    def get_available_agents_summary(self, agents: List[AgentDefinition]) -> str:
        """
        Génère un résumé des agents disponibles pour debug/logging
        
        Args:
            agents: Liste des agents à résumer
            
        Returns:
            str: Résumé formaté des agents
        """
        if not agents:
            return "Aucun agent disponible"
        
        summary = "Agents disponibles:\n"
        for i, agent in enumerate(agents, 1):
            summary += f"{i}. {agent.agent_name}: {agent.description}\n"
            summary += f"   Provider: {agent.default_config.provider.value}, "
            summary += f"Model: {agent.default_config.model_version}\n"
        
        return summary