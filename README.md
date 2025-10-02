# 🤖 A-IR-OB1 - AI Agent Orchestrator

**Système d'orchestration d'agents IA simple et autonome**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-black.svg)](https://openai.com)

## 🚀 Installation Rapide (1 commande)

### Windows
```bash
setup.bat
```

### Linux/macOS
```bash
chmod +x setup.sh && ./setup.sh
```

## ▶️ Démarrage Simple

### Windows
```bash
run.bat
```

### Linux/macOS
```bash
./run.sh
```

➡️ **Application disponible sur** : http://localhost:8000  
📚 **Documentation API** : http://localhost:8000/docs

## 🎯 Description

**A-IR-OB1** est un orchestrateur d'agents d'intelligence artificielle moderne, conçu pour être **simple à installer et utiliser**. Installation automatique, démarrage en une commande, et interface Web intuitive.

### ✨ Fonctionnalités

- 🏗️ **Architecture Hexagonale** - Code propre et modulaire
- ⚡ **FastAPI Asynchrone** - Performance optimale
- 🔧 **Factory Pattern** - Gestion intelligente des services LLM
- 💉 **Dependency Injection** - Architecture découplée
- 🛡️ **Validation Pydantic** - Typage strict automatique
- 🔌 **Multi-LLM** - OpenAI (+ Anthropic/Gemini à venir)
- 📱 **Interface Web** - Documentation API interactive

## 📁 Structure Simplifiée

```
A-IR-OB1/
├── setup.bat / setup.sh       # 🎯 Installation automatique
├── run.bat / run.sh           # ▶️ Démarrage simple
├── main.py                    # 🚀 Point d'entrée
├── requirements.txt           # 📦 Dépendances
├── src/                       # � Code source
│   ├── api/                   # �️ Endpoints FastAPI
│   ├── domain/               # 🧠 Logique métier
│   ├── infrastructure/       # 🔌 Adaptateurs LLM
│   └── models/               # 📝 Modèles de données
└── tests/                    # 🧪 Tests automatisés
```

## � Configuration (Optionnel)

### Clé API OpenAI
Créez un fichier `.env` dans le dossier du projet :
```env
OPENAI_API_KEY=votre_clé_api_ici
```

Ou définissez la variable d'environnement :
```bash
# Windows
set OPENAI_API_KEY=votre_clé_api_ici

# Linux/macOS
export OPENAI_API_KEY=votre_clé_api_ici
```

## 📋 Endpoints Disponibles

| Endpoint | Description | Méthode |
|----------|-------------|---------|
| `/` | Page d'accueil | GET |
| `/health` | Status de l'application | GET |
| `/providers` | Fournisseurs LLM disponibles | GET |
| `/test-service` | Test du service LLM | POST |
| `/chat` | Chat avec l'IA | POST |
| `/docs` | Documentation interactive | GET |

### Exemple d'utilisation
```bash
# Test de santé
curl http://localhost:8000/health

# Chat avec l'IA
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Bonjour ! Comment ça va ?"}'
```

## 🧪 Tests

```bash
# Activer l'environnement
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/macOS

# Lancer les tests
pytest
pytest -v                # Mode verbose
pytest --cov=src        # Avec coverage
```

## 🆘 Dépannage

### Problèmes courants

**Python non trouvé** :
- Installez Python 3.8+ depuis [python.org](https://python.org)
- Ajoutez Python au PATH système

**Erreur d'installation** :
- Vérifiez votre connexion internet
- Exécutez en tant qu'administrateur si nécessaire

**Serveur ne démarre pas** :
- Vérifiez que le port 8000 est libre
- Consultez les logs dans le terminal

## 📈 Roadmap

### ✅ Complété
- ✅ Architecture FastAPI + hexagonale
- ✅ Intégration OpenAI
- ✅ Factory pattern et DI
- ✅ Installation autonome

### 🚧 Prochaines étapes
- 🔄 Function Calling (Tools)
- 🤖 Support Anthropic Claude
- 🎯 Logique ReAct (Reasoning + Acting)
- 🕸️ Orchestration multi-agents

## 🤝 Contribution

1. Fork le repository
2. Créer une branche : `git checkout -b feature/ma-fonctionnalite`
3. Commit : `git commit -am 'Ajout de ma fonctionnalité'`
4. Push : `git push origin feature/ma-fonctionnalite`
5. Créer une Pull Request

## 📝 Licence

MIT License - Voir le fichier `LICENSE`

## 👨‍💻 Auteur

**Sylvain Bonnecarrère** - Architecture IA & Développement

---

*🎯 Installation en 1 commande, démarrage en 1 clic !*