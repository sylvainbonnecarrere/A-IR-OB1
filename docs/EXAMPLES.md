# 🎮 Exemples d'Usage Avancés - Orchestrator Agent

Ce guide présente des scenarios d'usage réels démontrant la puissance de la plateforme Orchestrator Agent avec ses **8 fournisseurs LLM**, **sessions persistantes**, et **mémoire automatique**.

## 🚀 Scenarios d'Usage Complets

### 1. 📊 Analyse de Données Multi-Provider

**Objectif :** Analyser un dataset complexe en utilisant les forces spécifiques de chaque LLM.

```python
import requests
import json
import time
from typing import Dict, Any

class DataAnalysisOrchestrator:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session_id = None
    
    def create_analysis_session(self, dataset_info: Dict[str, Any]) -> str:
        """Crée une session dédiée à l'analyse de données"""
        response = requests.post(f"{self.base_url}/sessions", json={
            "user_id": "data_analyst_01",
            "metadata": {
                "project": "Data Analysis",
                "dataset": dataset_info["name"],
                "size": dataset_info["size"],
                "type": dataset_info["type"]
            }
        })
        self.session_id = response.json()["session_id"]
        print(f"✅ Session créée: {self.session_id}")
        return self.session_id
    
    def statistical_analysis_with_claude(self, data_description: str) -> Dict[str, Any]:
        """Utilise Claude pour l'analyse statistique approfondie"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Analysez ces données statistiquement: {data_description}
            
            Fournissez:
            1. Statistiques descriptives détaillées
            2. Identification des variables clés
            3. Tests statistiques recommandés
            4. Détection d'anomalies potentielles
            5. Recommandations pour l'exploration
            """,
            "agent_config": {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 2000
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📈 Analyse statistique Claude: {result['execution_time']:.2f}s")
        return result
    
    def visualization_code_with_deepseek(self, analysis_results: str) -> Dict[str, Any]:
        """Utilise DeepSeek pour générer du code de visualisation"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Basé sur cette analyse statistique: {analysis_results}
            
            Générez du code Python complet pour créer des visualisations:
            1. Graphiques de distribution
            2. Matrices de corrélation
            3. Boxplots pour détecter les outliers
            4. Graphiques temporels si applicable
            5. Visualisations interactives avec Plotly
            
            Code prêt à exécuter avec commentaires détaillés.
            """,
            "agent_config": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "temperature": 0.1,
                "max_tokens": 3000
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"💻 Code visualisation DeepSeek: {result['execution_time']:.2f}s")
        return result
    
    def insights_with_gpt4(self, analysis_context: str) -> Dict[str, Any]:
        """Utilise GPT-4 pour extraire des insights business"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Contexte d'analyse: {analysis_context}
            
            Fournissez des insights business actionnables:
            1. Tendances principales identifiées
            2. Opportunités d'amélioration
            3. Risques potentiels
            4. Recommandations stratégiques
            5. Prochaines étapes suggérées
            
            Format: insights clairs et priorisés.
            """,
            "agent_config": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.5,
                "max_tokens": 2000
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"💡 Insights business GPT-4: {result['execution_time']:.2f}s")
        return result
    
    def run_complete_analysis(self, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une analyse complète multi-provider"""
        print("🚀 Démarrage de l'analyse multi-provider...")
        
        # 1. Créer la session
        self.create_analysis_session(dataset_info)
        
        # 2. Analyse statistique avec Claude
        data_description = f"Dataset: {dataset_info['description']}"
        statistical_analysis = self.statistical_analysis_with_claude(data_description)
        
        # 3. Génération de code avec DeepSeek
        viz_code = self.visualization_code_with_deepseek(
            statistical_analysis['response'][:1000]  # Résumé pour le contexte
        )
        
        # 4. Insights business avec GPT-4
        business_insights = self.insights_with_gpt4(
            f"Analyse: {statistical_analysis['response'][:500]}"
        )
        
        # 5. Récupérer les métriques de session
        metrics_response = requests.get(f"{self.base_url}/sessions/{self.session_id}/metrics")
        session_metrics = metrics_response.json()
        
        return {
            "session_id": self.session_id,
            "statistical_analysis": statistical_analysis,
            "visualization_code": viz_code,
            "business_insights": business_insights,
            "session_metrics": session_metrics,
            "providers_used": ["anthropic", "deepseek", "openai"],
            "total_execution_time": (
                statistical_analysis['execution_time'] + 
                viz_code['execution_time'] + 
                business_insights['execution_time']
            )
        }

# Exemple d'utilisation
if __name__ == "__main__":
    orchestrator = DataAnalysisOrchestrator()
    
    dataset_info = {
        "name": "Customer Behavior Analysis",
        "size": "50,000 records",
        "type": "Time series + Demographics",
        "description": """
        Dataset contenant 50,000 enregistrements de comportement client avec:
        - Données démographiques (âge, localisation, revenus)
        - Historique d'achats (montants, fréquence, catégories)
        - Données temporelles (5 années)
        - Métriques d'engagement (clicks, temps sur site, conversions)
        """
    }
    
    results = orchestrator.run_complete_analysis(dataset_info)
    
    print("\n📊 RÉSULTATS DE L'ANALYSE MULTI-PROVIDER")
    print("=" * 50)
    print(f"Session ID: {results['session_id']}")
    print(f"Providers utilisés: {', '.join(results['providers_used'])}")
    print(f"Temps total: {results['total_execution_time']:.2f}s")
    print(f"Messages échangés: {results['session_metrics']['message_count']}")
    print(f"Coût estimé: ${results['session_metrics']['total_cost']:.4f}")
```

### 2. 🎓 Tuteur IA Adaptatif Multi-Niveau

**Objectif :** Créer un système de tutorat qui s'adapte au niveau de l'utilisateur en utilisant différents LLMs.

```python
class AdaptiveTutorOrchestrator:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session_id = None
        self.student_level = "beginner"  # beginner, intermediate, advanced
        self.subject = None
    
    def start_tutoring_session(self, student_info: Dict[str, Any]) -> str:
        """Démarre une session de tutorat personnalisée"""
        response = requests.post(f"{self.base_url}/sessions", json={
            "user_id": f"student_{student_info['id']}",
            "metadata": {
                "type": "tutoring",
                "subject": student_info["subject"],
                "level": student_info["level"],
                "learning_style": student_info.get("learning_style", "visual"),
                "goals": student_info.get("goals", [])
            }
        })
        
        self.session_id = response.json()["session_id"]
        self.student_level = student_info["level"]
        self.subject = student_info["subject"]
        
        print(f"🎓 Session de tutorat créée: {self.session_id}")
        return self.session_id
    
    def assess_student_level(self, question: str) -> Dict[str, Any]:
        """Utilise Gemini pour évaluer le niveau de l'étudiant"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Question de l'étudiant: "{question}"
            Sujet: {self.subject}
            
            Analysez cette question pour déterminer:
            1. Niveau de compréhension apparent (débutant/intermédiaire/avancé)
            2. Concepts sous-jacents nécessaires
            3. Lacunes potentielles identifiées
            4. Approche pédagogique recommandée
            5. Prérequis manquants éventuels
            
            Format JSON avec évaluation détaillée.
            """,
            "agent_config": {
                "provider": "gemini",
                "model": "gemini-1.5-pro",
                "temperature": 0.4,
                "max_tokens": 1500
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📊 Évaluation niveau Gemini: {result['execution_time']:.2f}s")
        return result
    
    def provide_explanation(self, question: str, level_assessment: str) -> Dict[str, Any]:
        """Utilise Claude pour fournir une explication adaptée au niveau"""
        provider_by_level = {
            "beginner": ("anthropic", "claude-3-5-haiku-20241022"),
            "intermediate": ("anthropic", "claude-3-5-sonnet-20241022"),
            "advanced": ("openai", "gpt-4")
        }
        
        provider, model = provider_by_level.get(self.student_level, ("anthropic", "claude-3-5-sonnet-20241022"))
        
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Question de l'étudiant: "{question}"
            Évaluation du niveau: {level_assessment}
            Niveau étudiant: {self.student_level}
            Sujet: {self.subject}
            
            Fournissez une explication adaptée au niveau {self.student_level}:
            
            Pour niveau débutant:
            - Langage simple et accessible
            - Analogies du quotidien
            - Étapes très détaillées
            - Exemples concrets
            
            Pour niveau intermédiaire:
            - Terminologie appropriée
            - Liens avec concepts connexes
            - Exemples pratiques
            - Questions de réflexion
            
            Pour niveau avancé:
            - Analyse approfondie
            - Nuances et cas particuliers
            - Références théoriques
            - Défis intellectuels
            
            Incluez toujours des exercices pratiques adaptés.
            """,
            "agent_config": {
                "provider": provider,
                "model": model,
                "temperature": 0.6,
                "max_tokens": 2500
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📚 Explication {provider}: {result['execution_time']:.2f}s")
        return result
    
    def generate_practice_exercises(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Utilise Mistral pour générer des exercices pratiques"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Sujet: {topic}
            Niveau de difficulté: {difficulty}
            Niveau étudiant: {self.student_level}
            
            Générez 5 exercices pratiques progressifs:
            
            1. Exercice de compréhension (QCM)
            2. Exercice d'application directe
            3. Exercice de résolution de problème
            4. Exercice créatif/synthèse
            5. Exercice de transfert de compétences
            
            Pour chaque exercice:
            - Énoncé clair
            - Solution détaillée
            - Critères d'évaluation
            - Conseils si difficulté
            - Temps estimé
            
            Format structuré pour faciliter la pratique.
            """,
            "agent_config": {
                "provider": "mistral",
                "model": "mistral-large-latest",
                "temperature": 0.7,
                "max_tokens": 3000
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📝 Exercices Mistral: {result['execution_time']:.2f}s")
        return result
    
    def provide_feedback(self, student_answer: str, correct_answer: str) -> Dict[str, Any]:
        """Utilise Qwen pour fournir un feedback constructif"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Réponse de l'étudiant: "{student_answer}"
            Réponse correcte: "{correct_answer}"
            Niveau étudiant: {self.student_level}
            
            Fournissez un feedback constructif et encourageant:
            
            1. Points positifs identifiés
            2. Erreurs spécifiques avec explications
            3. Suggestions d'amélioration concrètes
            4. Ressources complémentaires recommandées
            5. Encouragements personnalisés
            6. Prochaines étapes suggérées
            
            Ton bienveillant et motivant, adapté au niveau.
            """,
            "agent_config": {
                "provider": "qwen",
                "model": "qwen-turbo",
                "temperature": 0.5,
                "max_tokens": 1500
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"💬 Feedback Qwen: {result['execution_time']:.2f}s")
        return result
    
    def run_tutoring_session(self, student_info: Dict[str, Any], 
                           question: str, student_answer: str = None) -> Dict[str, Any]:
        """Exécute une session complète de tutorat adaptatif"""
        print("🎓 Démarrage du tutorat adaptatif...")
        
        # 1. Créer la session
        self.start_tutoring_session(student_info)
        
        # 2. Évaluer le niveau
        level_assessment = self.assess_student_level(question)
        
        # 3. Fournir l'explication adaptée
        explanation = self.provide_explanation(question, level_assessment['response'][:500])
        
        # 4. Générer des exercices
        exercises = self.generate_practice_exercises(
            topic=self.subject,
            difficulty=self.student_level
        )
        
        # 5. Feedback si réponse fournie
        feedback = None
        if student_answer:
            feedback = self.provide_feedback(
                student_answer, 
                "Réponse modèle basée sur l'explication fournie"
            )
        
        # 6. Métriques de session
        metrics_response = requests.get(f"{self.base_url}/sessions/{self.session_id}/metrics")
        session_metrics = metrics_response.json()
        
        return {
            "session_id": self.session_id,
            "level_assessment": level_assessment,
            "explanation": explanation,
            "exercises": exercises,
            "feedback": feedback,
            "session_metrics": session_metrics,
            "providers_used": ["gemini", "anthropic", "mistral", "qwen"] if feedback else ["gemini", "anthropic", "mistral"],
            "adaptation_effective": True
        }

# Exemple d'utilisation
if __name__ == "__main__":
    tutor = AdaptiveTutorOrchestrator()
    
    student_info = {
        "id": "12345",
        "name": "Alice Martin",
        "subject": "Programmation Python",
        "level": "intermediate",
        "learning_style": "hands-on",
        "goals": ["Maîtriser les classes", "Comprendre les décorateurs", "Projet web"]
    }
    
    question = "Comment fonctionnent les décorateurs en Python et à quoi servent-ils ?"
    student_answer = "Les décorateurs permettent de modifier une fonction sans changer son code directement"
    
    results = tutor.run_tutoring_session(student_info, question, student_answer)
    
    print("\n🎓 RÉSULTATS DU TUTORAT ADAPTATIF")
    print("=" * 50)
    print(f"Session ID: {results['session_id']}")
    print(f"Niveau détecté: {tutor.student_level}")
    print(f"Providers utilisés: {', '.join(results['providers_used'])}")
    print(f"Messages échangés: {results['session_metrics']['message_count']}")
    print(f"Adaptation réussie: {results['adaptation_effective']}")
```

### 3. 🏢 Assistant de Veille Technologique

**Objectif :** Système de veille automatisée combinant plusieurs LLMs pour analyser les tendances tech.

```python
class TechWatchOrchestrator:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session_id = None
        self.tech_domains = []
    
    def start_tech_watch_session(self, watch_config: Dict[str, Any]) -> str:
        """Démarre une session de veille technologique"""
        response = requests.post(f"{self.base_url}/sessions", json={
            "user_id": f"tech_analyst_{watch_config['analyst_id']}",
            "metadata": {
                "type": "tech_watch",
                "domains": watch_config["domains"],
                "frequency": watch_config.get("frequency", "daily"),
                "focus": watch_config.get("focus", "emerging_technologies"),
                "company": watch_config.get("company", "default")
            }
        })
        
        self.session_id = response.json()["session_id"]
        self.tech_domains = watch_config["domains"]
        
        print(f"🔍 Session de veille créée: {self.session_id}")
        return self.session_id
    
    def analyze_trends_with_gpt4(self, tech_data: str) -> Dict[str, Any]:
        """Utilise GPT-4 pour l'analyse de tendances"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Données technologiques récentes: {tech_data}
            Domaines surveillés: {', '.join(self.tech_domains)}
            
            Analysez les tendances technologiques émergentes:
            
            1. TENDANCES PRINCIPALES:
               - Technologies en croissance rapide
               - Nouveaux frameworks/outils populaires
               - Évolutions des standards de l'industrie
            
            2. ANALYSE COMPARATIVE:
               - Comparaison avec les trimestres précédents
               - Positionnement vs concurrents
               - Adoption market vs hype
            
            3. IMPACT BUSINESS:
               - Opportunités d'innovation
               - Risques de disruption
               - ROI potentiel d'adoption
            
            4. PRÉDICTIONS:
               - Évolution à 6-12 mois
               - Technologies à surveiller
               - Obsolescence probable
            
            Format: rapport exécutif structuré avec données quantifiées.
            """,
            "agent_config": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.4,
                "max_tokens": 3000
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📈 Analyse tendances GPT-4: {result['execution_time']:.2f}s")
        return result
    
    def competitive_analysis_with_claude(self, trends_summary: str) -> Dict[str, Any]:
        """Utilise Claude pour l'analyse concurrentielle approfondie"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Résumé des tendances identifiées: {trends_summary}
            
            Effectuez une analyse concurrentielle stratégique:
            
            1. POSITIONNEMENT CONCURRENTIEL:
               - Leaders technologiques identifiés
               - Stratégies d'adoption par secteur
               - Avantages/inconvénients par solution
            
            2. ANALYSE DES GAPS:
               - Opportunités non exploitées
               - Niches technologiques émergentes
               - Besoins clients non satisfaits
            
            3. RECOMMANDATIONS STRATÉGIQUES:
               - Technologies à adopter en priorité
               - Partenariats stratégiques suggérés
               - Investissements R&D recommandés
            
            4. PLAN D'ACTION:
               - Timeline d'implémentation
               - Ressources nécessaires
               - Métriques de succès
            
            Approche analytique rigoureuse avec preuves à l'appui.
            """,
            "agent_config": {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 2500
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"🎯 Analyse concurrentielle Claude: {result['execution_time']:.2f}s")
        return result
    
    def technical_deep_dive_with_deepseek(self, tech_focus: str) -> Dict[str, Any]:
        """Utilise DeepSeek pour l'analyse technique approfondie"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Focus technique: {tech_focus}
            
            Effectuez une analyse technique approfondie:
            
            1. ARCHITECTURE TECHNIQUE:
               - Composants et modules principaux
               - Patterns d'architecture utilisés
               - Intégrations et APIs disponibles
            
            2. IMPLÉMENTATION:
               - Code samples et exemples pratiques
               - Bonnes pratiques d'implémentation
               - Pièges à éviter et solutions
            
            3. PERFORMANCE ET SCALABILITÉ:
               - Benchmarks et métriques
               - Limites techniques identifiées
               - Optimisations possibles
            
            4. ÉCOSYSTÈME ET TOOLING:
               - Outils de développement
               - Bibliothèques et extensions
               - Communauté et support
            
            5. MIGRATION ET ADOPTION:
               - Stratégies de migration
               - Coexistence avec l'existant
               - Formation équipes nécessaire
            
            Analyse technique détaillée avec exemples de code.
            """,
            "agent_config": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "temperature": 0.2,
                "max_tokens": 3500
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"🔧 Analyse technique DeepSeek: {result['execution_time']:.2f}s")
        return result
    
    def market_intelligence_with_gemini(self, analysis_context: str) -> Dict[str, Any]:
        """Utilise Gemini pour l'intelligence marché"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Contexte d'analyse: {analysis_context}
            
            Fournissez une intelligence marché complète:
            
            1. SIZING ET VALORISATION:
               - Taille de marché actuelle et projetée
               - Segments de croissance principaux
               - Valorisations et investissements récents
            
            2. ACTEURS CLÉS:
               - Leaders établis et challengers
               - Startups prometteuses à surveiller
               - Consolidations et acquisitions récentes
            
            3. DYNAMIQUES MARCHÉ:
               - Facteurs de croissance identifiés
               - Barrières à l'entrée
               - Cycles d'adoption par industrie
            
            4. SIGNAUX FAIBLES:
               - Innovations de rupture potentielles
               - Changements réglementaires impact
               - Shifts comportementaux utilisateurs
            
            5. RECOMMANDATIONS INVESTISSEMENT:
               - Priorités d'allocation budget
               - Horizons temporels par technologie
               - Stratégies hedging recommandées
            
            Intelligence actionnable avec données marché récentes.
            """,
            "agent_config": {
                "provider": "gemini",
                "model": "gemini-1.5-pro",
                "temperature": 0.5,
                "max_tokens": 2800
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📊 Intelligence marché Gemini: {result['execution_time']:.2f}s")
        return result
    
    def synthesize_insights_with_mistral(self, all_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Utilise Mistral pour synthétiser tous les insights"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": f"""
            Analyses réalisées:
            - Tendances: {all_analyses['trends']['response'][:300]}...
            - Concurrence: {all_analyses['competitive']['response'][:300]}...
            - Technique: {all_analyses['technical']['response'][:300]}...
            - Marché: {all_analyses['market']['response'][:300]}...
            
            Synthétisez en rapport exécutif final:
            
            ## EXECUTIVE SUMMARY
            - 3 insights clés prioritaires
            - Impact business estimé
            - Actions immédiates recommandées
            
            ## STRATEGIC ROADMAP
            - Phase 1 (0-3 mois): Actions critiques
            - Phase 2 (3-6 mois): Développements stratégiques
            - Phase 3 (6-12 mois): Innovations long terme
            
            ## RISK ASSESSMENT
            - Risques technologiques identifiés
            - Risques concurrentiels
            - Stratégies de mitigation
            
            ## KPIs DE SUIVI
            - Métriques d'adoption
            - Indicateurs de performance
            - Seuils d'alerte
            
            Format: rapport exécutif prêt pour présentation C-level.
            """,
            "agent_config": {
                "provider": "mistral",
                "model": "mistral-large-latest",
                "temperature": 0.4,
                "max_tokens": 2500
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        print(f"📋 Synthèse finale Mistral: {result['execution_time']:.2f}s")
        return result
    
    def run_complete_tech_watch(self, watch_config: Dict[str, Any], 
                              tech_data: str) -> Dict[str, Any]:
        """Exécute une veille technologique complète"""
        print("🔍 Démarrage de la veille technologique complète...")
        
        # 1. Créer la session
        self.start_tech_watch_session(watch_config)
        
        # 2. Analyse des tendances avec GPT-4
        trends_analysis = self.analyze_trends_with_gpt4(tech_data)
        
        # 3. Analyse concurrentielle avec Claude
        competitive_analysis = self.competitive_analysis_with_claude(
            trends_analysis['response'][:800]
        )
        
        # 4. Deep dive technique avec DeepSeek
        technical_analysis = self.technical_deep_dive_with_deepseek(
            watch_config['domains'][0]  # Focus sur le premier domaine
        )
        
        # 5. Intelligence marché avec Gemini
        market_intelligence = self.market_intelligence_with_gemini(
            f"Trends: {trends_analysis['response'][:400]}... Competitive: {competitive_analysis['response'][:400]}..."
        )
        
        # 6. Synthèse finale avec Mistral
        all_analyses = {
            'trends': trends_analysis,
            'competitive': competitive_analysis,
            'technical': technical_analysis,
            'market': market_intelligence
        }
        
        final_synthesis = self.synthesize_insights_with_mistral(all_analyses)
        
        # 7. Métriques de session
        metrics_response = requests.get(f"{self.base_url}/sessions/{self.session_id}/metrics")
        session_metrics = metrics_response.json()
        
        return {
            "session_id": self.session_id,
            "trends_analysis": trends_analysis,
            "competitive_analysis": competitive_analysis,
            "technical_analysis": technical_analysis,
            "market_intelligence": market_intelligence,
            "final_synthesis": final_synthesis,
            "session_metrics": session_metrics,
            "providers_used": ["openai", "anthropic", "deepseek", "gemini", "mistral"],
            "total_execution_time": sum([
                trends_analysis['execution_time'],
                competitive_analysis['execution_time'],
                technical_analysis['execution_time'],
                market_intelligence['execution_time'],
                final_synthesis['execution_time']
            ]),
            "domains_analyzed": self.tech_domains
        }

# Exemple d'utilisation
if __name__ == "__main__":
    tech_watch = TechWatchOrchestrator()
    
    watch_config = {
        "analyst_id": "TW_001",
        "domains": ["AI/ML", "Cloud Computing", "Cybersecurity", "DevOps"],
        "frequency": "weekly",
        "focus": "enterprise_adoption",
        "company": "TechCorp Inc."
    }
    
    tech_data = """
    Données récentes Q4 2024:
    - Adoption massive de l'IA générative en entreprise (+340%)
    - Croissance des solutions edge computing (+125%)
    - Nouvelles régulations cybersécurité EU/US
    - Kubernetes devient standard de facto (87% adoption)
    - Émergence des LLMs spécialisés par domaine
    - Consolidation marché cloud providers
    - Zero-trust architecture mainstream
    - Quantum computing: premiers cas d'usage pratiques
    """
    
    results = tech_watch.run_complete_tech_watch(watch_config, tech_data)
    
    print("\n🔍 RÉSULTATS DE LA VEILLE TECHNOLOGIQUE")
    print("=" * 60)
    print(f"Session ID: {results['session_id']}")
    print(f"Domaines analysés: {', '.join(results['domains_analyzed'])}")
    print(f"Providers utilisés: {', '.join(results['providers_used'])}")
    print(f"Temps total d'analyse: {results['total_execution_time']:.2f}s")
    print(f"Messages échangés: {results['session_metrics']['message_count']}")
    print(f"Coût total: ${results['session_metrics']['total_cost']:.4f}")
    print(f"Providers sollicités: {len(results['session_metrics']['providers_used'])}")
```

### 4. 📱 Assistant de Session Longue avec Auto-Summarization

**Objectif :** Démontrer la gestion automatique de la mémoire et du résumé en session longue.

```python
class LongSessionOrchestrator:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session_id = None
        self.message_count = 0
    
    def start_long_session(self, context: str) -> str:
        """Démarre une session longue avec contexte"""
        response = requests.post(f"{self.base_url}/sessions", json={
            "user_id": "long_session_user",
            "metadata": {
                "type": "long_conversation",
                "context": context,
                "auto_summarization": True,
                "summarization_threshold": 10  # Résumé tous les 10 messages pour la démo
            }
        })
        
        self.session_id = response.json()["session_id"]
        print(f"🚀 Session longue créée: {self.session_id}")
        return self.session_id
    
    def send_message(self, message: str, provider: str = "openai") -> Dict[str, Any]:
        """Envoie un message dans la session"""
        response = requests.post(f"{self.base_url}/orchestrate", json={
            "message": message,
            "agent_config": {
                "provider": provider,
                "model": "gpt-3.5-turbo" if provider == "openai" else "claude-3-5-haiku-20241022",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "session_id": self.session_id
        })
        
        result = response.json()
        self.message_count += 1
        
        # Vérifier si un résumé a été déclenché
        was_summarized = result.get('metadata', {}).get('was_summarized', False)
        if was_summarized:
            print(f"🧠 Résumé automatique déclenché au message {self.message_count}")
        
        print(f"💬 Message {self.message_count} ({provider}): {result['execution_time']:.2f}s")
        return result
    
    def demonstrate_auto_summarization(self) -> Dict[str, Any]:
        """Démontre le mécanisme de résumé automatique"""
        print("📚 Démonstration de la summarization automatique...")
        
        # 1. Créer une session longue
        self.start_long_session("Projet de développement d'application mobile")
        
        # Série de messages qui vont déclencher la summarization
        messages = [
            ("Bonjour, je travaille sur une app mobile de fitness", "openai"),
            ("Quelles sont les meilleures pratiques UX pour ce type d'app?", "anthropic"),
            ("Comment gérer l'authentification des utilisateurs?", "openai"),
            ("Quel backend recommandez-vous pour une app fitness?", "gemini"),
            ("Comment implémenter le tracking GPS pour les courses?", "deepseek"),
            ("Quelles APIs utiliser pour les données nutritionnelles?", "mistral"),
            ("Comment optimiser les performances de l'app?", "anthropic"),
            ("Quelle stratégie de monétisation adopter?", "openai"),
            ("Comment gérer les notifications push efficacement?", "qwen"),
            ("Quels tests automatisés mettre en place?", "openai"),
            # Le 11ème message devrait déclencher la summarization
            ("Comment déployer l'app sur les stores?", "anthropic"),
            ("Après le résumé, continuons avec les métriques d'usage", "gemini"),
            ("Comment analyser le comportement des utilisateurs?", "openai"),
        ]
        
        responses = []
        summarization_triggered = False
        
        for i, (message, provider) in enumerate(messages, 1):
            print(f"\n--- Message {i} ---")
            response = self.send_message(message, provider)
            responses.append(response)
            
            # Détecter si la summarization a été déclenchée
            if response.get('metadata', {}).get('was_summarized', False):
                summarization_triggered = True
                print(f"✅ Résumé automatique confirmé au message {i}")
                
                # Récupérer l'historique pour voir le résumé
                history_response = requests.get(
                    f"{self.base_url}/sessions/{self.session_id}/history?limit=50"
                )
                history = history_response.json()
                
                print(f"📝 Résumé généré: {history.get('summary', 'Aucun résumé')[:200]}...")
        
        # Métriques finales
        metrics_response = requests.get(f"{self.base_url}/sessions/{self.session_id}/metrics")
        session_metrics = metrics_response.json()
        
        return {
            "session_id": self.session_id,
            "total_messages": len(responses),
            "summarization_triggered": summarization_triggered,
            "providers_used": list(set(msg[1] for msg in messages)),
            "session_metrics": session_metrics,
            "responses": responses
        }

# Exemple d'utilisation
if __name__ == "__main__":
    long_session = LongSessionOrchestrator()
    
    results = long_session.demonstrate_auto_summarization()
    
    print("\n📚 RÉSULTATS DÉMONSTRATION AUTO-SUMMARIZATION")
    print("=" * 60)
    print(f"Session ID: {results['session_id']}")
    print(f"Messages envoyés: {results['total_messages']}")
    print(f"Résumé déclenché: {'✅ Oui' if results['summarization_triggered'] else '❌ Non'}")
    print(f"Providers utilisés: {', '.join(results['providers_used'])}")
    print(f"Message count final: {results['session_metrics']['message_count']}")
    print(f"Coût total: ${results['session_metrics']['total_cost']:.4f}")
    
    if results['summarization_triggered']:
        print("🎉 Démonstration réussie de la mémoire automatique!")
    else:
        print("⚠️ Le seuil de summarization n'a pas été atteint dans cette démo")
```

## 🎯 Exécution des Exemples

### Prérequis

```bash
# 1. Démarrer le serveur Orchestrator Agent
python main.py

# 2. Installer les dépendances pour les exemples
pip install requests

# 3. Configurer les clés API dans .env
# (Voir ./SECURITY.md pour la configuration complète)
```

### Lancement des Scénarios

```python
# Exécuter tous les exemples
if __name__ == "__main__":
    import asyncio
    
    async def run_all_scenarios():
        """Exécute tous les scénarios d'usage avancés"""
        
        print("🚀 LANCEMENT DES SCÉNARIOS AVANCÉS")
        print("=" * 50)
        
        # Scénario 1: Analyse de données
        print("\n1️⃣ Analyse de Données Multi-Provider")
        data_orchestrator = DataAnalysisOrchestrator()
        # ... (code du scénario)
        
        # Scénario 2: Tutorat adaptatif
        print("\n2️⃣ Tutorat IA Adaptatif")
        tutor = AdaptiveTutorOrchestrator()
        # ... (code du scénario)
        
        # Scénario 3: Veille technologique
        print("\n3️⃣ Veille Technologique")
        tech_watch = TechWatchOrchestrator()
        # ... (code du scénario)
        
        # Scénario 4: Session longue
        print("\n4️⃣ Auto-Summarization")
        long_session = LongSessionOrchestrator()
        # ... (code du scénario)
        
        print("\n✅ TOUS LES SCÉNARIOS TERMINÉS")
    
    # Lancer les scénarios
    asyncio.run(run_all_scenarios())
```

---

## 📊 Métriques et Performance

Chaque scénario génère des métriques détaillées :

- **Temps d'exécution** par provider
- **Coût estimé** par requête
- **Nombre de tokens** utilisés
- **Taux de succès** des requêtes
- **Performance comparative** entre providers

## 🎯 Personnalisation

Ces exemples sont entièrement personnalisables :

1. **Modifiez les providers** selon vos besoins
2. **Ajustez les paramètres** (temperature, max_tokens)
3. **Adaptez les prompts** à votre domaine
4. **Configurez les seuils** de summarization
5. **Personnalisez les métriques** collectées

---

> 🎮 **Ces exemples démontrent la puissance réelle de l'Orchestrator Agent** avec ses sessions persistantes, sa mémoire automatique, et son orchestration intelligente de 8 fournisseurs LLM différents.