"""
In-Memory Session Manager - Gestionnaire de sessions en mémoire

Ce module implémente un gestionnaire de sessions simple stockant les données
en mémoire pour le développement et les tests. En production, ceci serait
remplacé par une implémentation avec base de données ou cache distribué.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from uuid import UUID
from src.models.data_contracts import Session, HistoryConfig, SessionManager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InMemorySessionManager(SessionManager):
    """
    Gestionnaire de sessions en mémoire
    
    Cette implémentation stocke les sessions dans un dictionnaire en mémoire.
    Les sessions sont perdues au redémarrage de l'application.
    
    Note: En production, utiliser une base de données (PostgreSQL, MongoDB)
    ou un cache distribué (Redis) pour la persistance réelle.
    """
    
    def __init__(self):
        """Initialise le gestionnaire avec un stockage vide"""
        self._sessions: Dict[str, Session] = {}
        logger.info("InMemorySessionManager initialisé")
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Récupère une session par son ID
        
        Args:
            session_id: Identifiant unique de la session (string)
            
        Returns:
            Session si trouvée, None sinon
        """
        session = self._sessions.get(session_id)
        if session:
            logger.debug(f"Session récupérée: {session_id}")
        else:
            logger.warning(f"Session non trouvée: {session_id}")
        return session
    
    async def save_session(self, session: Session) -> None:
        """
        Sauvegarde ou met à jour une session
        
        Args:
            session: Session à sauvegarder
        """
        # Mise à jour du timestamp
        session.last_message_at = datetime.now()
        
        # Sauvegarde en mémoire
        self._sessions[str(session.session_id)] = session
        logger.info(f"💾 Session {session.session_id} sauvegardée")
    
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
        # Configuration par défaut si non fournie
        if history_config is None:
            history_config = HistoryConfig()
        
        # Création de la session
        session = Session(
            agent_name=agent_name,
            history_config=history_config,
            status="ACTIVE"
        )
        
        # Sauvegarde initiale
        await self.save_session(session)
        
        logger.info(f"Session créée: {session.session_id} pour agent {agent_name}")
        return session
    
    async def update_session(self, session: Session) -> bool:
        """
        Met à jour une session existante
        
        Args:
            session: Session à mettre à jour
            
        Returns:
            True si mise à jour réussie, False sinon
        """
        try:
            await self.save_session(session)
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour session {session.session_id}: {e}")
            return False
    
    async def list_sessions(self, limit: int = 100) -> List[Session]:
        """
        Liste les sessions existantes
        
        Args:
            limit: Nombre maximum de sessions à retourner
            
        Returns:
            Liste des sessions (triées par date de création décroissante)
        """
        sessions = list(self._sessions.values())
        
        # Tri par date de création (plus récentes en premier)
        sessions.sort(
            key=lambda s: s.created_at or "1970-01-01T00:00:00", 
            reverse=True
        )
        
        # Limitation du nombre de résultats
        limited_sessions = sessions[:limit]
        
        logger.debug(f"Liste de {len(limited_sessions)} sessions retournée")
        return limited_sessions
    
    async def delete_session(self, session_id: UUID) -> bool:
        """
        Supprime une session
        
        Args:
            session_id: ID de la session à supprimer
            
        Returns:
            bool: True si supprimée, False si non trouvée
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session supprimée: {session_id}")
            return True
        else:
            logger.warning(f"Tentative de suppression d'une session inexistante: {session_id}")
            return False
    
    async def update_session_status(self, session_id: UUID, status: str) -> bool:
        """
        Met à jour le statut d'une session
        
        Args:
            session_id: ID de la session
            status: Nouveau statut
            
        Returns:
            bool: True si mise à jour réussie
        """
        session = await self.get_session(session_id)
        if session:
            session.status = status
            await self.save_session(session)
            logger.info(f"Statut session {session_id} mis à jour: {status}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, any]:
        """
        Retourne des statistiques sur le gestionnaire de sessions
        
        Returns:
            Dict: Statistiques diverses
        """
        sessions = list(self._sessions.values())
        
        # Comptage par statut
        status_counts = {}
        agent_counts = {}
        total_messages = 0
        
        for session in sessions:
            # Statuts
            status_counts[session.status] = status_counts.get(session.status, 0) + 1
            
            # Agents
            agent_counts[session.agent_name] = agent_counts.get(session.agent_name, 0) + 1
            
            # Messages
            total_messages += len(session.history)
        
        return {
            "total_sessions": len(sessions),
            "status_distribution": status_counts,
            "agent_distribution": agent_counts,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / len(sessions) if sessions else 0,
            "storage_type": "in_memory"
        }