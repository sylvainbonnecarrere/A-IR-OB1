# Documentation Technique API - Agents IA

## Vue d'ensemble

Cette documentation technique réunit les fonctionnalités disponibles via API pour différents agents IA, destinée aux développeurs d'applications React/Python. Elle couvre 9 providers principaux avec 8 fonctionnalités clés.

## Tableau de Référence des Fonctionnalités

| LLM | Chat | File Analysis | URL Analysis | Image Generation | Image Modification | Web Search | Function Calling | Output Formatting |
|-----|------|---------------|--------------|------------------|-------------------|------------|------------------|-------------------|
| Gemini | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| OpenAI | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Mistral | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Anthropic | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Grok | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Perplexity | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Qwen | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| DeepSeek | ✅ | ✅ | ❌ | Janus Pro | ❌ | ❌ | ✅ | ✅ |
| Kimi K2 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

## 1. GEMINI API

### 1.1 Chat
```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Votre message ici"
)
print(response.text)
```

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: "YOUR_API_KEY" });
const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: "Votre message ici"
});
console.log(response.text);
```

### 1.2 File Analysis
```python
from google import genai
from google.genai import types
import httpx

client = genai.Client()

# Pour PDF
doc_data = httpx.get("URL_DU_PDF").content
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=doc_data,
            mime_type='application/pdf'
        ),
        "Analysez ce document"
    ]
)
```

### 1.3 URL Analysis
```python
from google import genai
from google.genai.types import Tool, GenerateContentConfig

tools = [{"url_context": {}}]
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Analysez le contenu de https://example.com",
    config=GenerateContentConfig(tools=tools)
)
```

### 1.4 Image Generation
**Modèle:** gemini-2.5-flash-image
```python
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="Générez une image de chat"
)
```

### 1.5 Web Search
```python
# Intégré avec Google Search
tools = [{"google_search": {}}]
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Recherchez les dernières actualités IA",
    config=GenerateContentConfig(tools=tools)
)
```

### 1.6 Function Calling
```python
tools = [{
    "function_declarations": [{
        "name": "get_weather",
        "description": "Obtient la météo",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }]
}]

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Quelle est la météo à Paris?",
    tools=tools
)
```

### 1.7 Output Formatting
```python
# JSON structuré
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Générez une réponse JSON",
    generation_config={"response_mime_type": "application/json"}
)
```

## 2. OPENAI API

### 2.1 Chat
```python
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Votre message"}]
)
print(response.choices[0].message.content)
```

### 2.2 File Analysis
```python
# Upload file first
file = client.files.create(
    file=open("document.pdf", "rb"),
    purpose="assistants"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analysez ce fichier"},
            {"type": "file", "file_id": file.id}
        ]
    }]
)
```

### 2.3 Image Generation
```python
# Via Responses API
response = client.responses.create(
    model="gpt-4o",
    input="Générez une image de chat",
    tools=[{"type": "image_generation"}]
)

# Via DALL-E API direct
image = client.images.generate(
    model="dall-e-3",
    prompt="Chat réaliste",
    size="1024x1024",
    quality="standard",
    n=1
)
```

### 2.4 Image Modification
```python
response = client.images.edit(
    image=open("image.png", "rb"),
    mask=open("mask.png", "rb"),
    prompt="Ajoutez un chapeau au chat",
    n=1,
    size="1024x1024"
)
```

### 2.5 Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Obtient la météo",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Météo à Paris?"}],
    tools=tools,
    tool_choice="auto"
)
```

### 2.6 Output Formatting
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Répondez en JSON"}],
    response_format={"type": "json_object"}
)
```

## 3. MISTRAL API

### 3.1 Chat
```python
from mistralai.client import MistralClient

client = MistralClient(api_key="YOUR_API_KEY")
response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Votre message"}]
)
```

### 3.2 File Analysis
```python
# Via Agents API
agent = client.beta.agents.create(
    model="mistral-large-latest",
    name="Document Analyzer",
    tools=[{"type": "document_library"}]
)

conversation = client.beta.conversations.start(
    agent_id=agent.id,
    inputs="Analysez ce document",
    files=["document.pdf"]
)
```

### 3.3 Web Search
```python
# Via Agents API
agent = client.beta.agents.create(
    model="mistral-large-latest",
    name="Web Search Agent",
    tools=[{"type": "web_search"}]
)

conversation = client.beta.conversations.start(
    agent_id=agent.id,
    inputs="Recherchez les actualités IA"
)
```

### 3.4 Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Obtient la météo",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}]

response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Météo à Paris?"}],
    tools=tools
)
```

### 3.5 Output Formatting
```python
response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Répondez en JSON"}],
    response_format={"type": "json_object"}
)
```

## 4. ANTHROPIC CLAUDE API

### 4.1 Chat
```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY")
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Votre message"}]
)
print(response.content[0].text)
```

### 4.2 File Analysis
```python
# Via Files API
file = client.files.create(
    file=open("document.pdf", "rb")
)

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analysez ce document"},
            {
                "type": "document",
                "source": {
                    "type": "file",
                    "file_id": file.id
                }
            }
        ]
    }]
)
```

### 4.3 Function Calling
```python
tools = [{
    "name": "get_weather",
    "description": "Obtient la météo actuelle",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Ville et pays"
            }
        },
        "required": ["location"]
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Météo à Paris?"}]
)
```

### 4.4 Output Formatting
```python
# JSON via tool use
tools = [{
    "name": "format_response",
    "description": "Formate la réponse en JSON",
    "input_schema": {
        "type": "object",
        "properties": {
            "response": {"type": "object"}
        }
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "format_response"},
    messages=[{"role": "user", "content": "Répondez en JSON"}]
)
```

## 5. GROK (xAI) API

### 5.1 Chat
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_XAI_API_KEY",
    base_url="https://api.x.ai/v1"
)

response = client.chat.completions.create(
    model="grok-3-latest",
    messages=[{"role": "user", "content": "Votre message"}]
)
```

### 5.2 File Analysis
```python
# Support des images et documents
response = client.chat.completions.create(
    model="grok-vision-latest",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analysez cette image"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,{base64_image}"}
            }
        ]
    }]
)
```

### 5.3 Image Generation
```python
response = client.images.generate(
    model="grok-2-image",
    prompt="Chat réaliste",
    size="1024x768",
    n=1
)
```

### 5.4 Web Search
```python
# Via Live Search
response = client.chat.completions.create(
    model="grok-3-latest",
    messages=[{"role": "user", "content": "Dernières actualités IA"}],
    extra_body={
        "search_parameters": {
            "mode": "on",
            "return_citations": True,
            "sources": [{"type": "web"}]
        }
    }
)
```

## 6. PERPLEXITY API

### 6.1 Chat
```python
from perplexity import Perplexity

client = Perplexity(api_key="YOUR_API_KEY")
response = client.chat.completions.create(
    model="llama-3.1-sonar-small-128k-online",
    messages=[{"role": "user", "content": "Votre question"}]
)
```

### 6.2 Web Search
```python
# Search API
search_response = client.search.create(
    query="actualités intelligence artificielle",
    max_results=10,
    max_tokens_per_page=1024
)

# Sonar models avec recherche intégrée
response = client.chat.completions.create(
    model="llama-3.1-sonar-large-128k-online",
    messages=[{"role": "user", "content": "Dernières actualités IA"}]
)
```

## 7. QWEN API

### 7.1 Chat
```python
from openai import OpenAI

# Via DashScope ou providers compatibles
client = OpenAI(
    api_key="YOUR_QWEN_API_KEY",
    base_url="https://dashscope.aliyuncs.com/v1"
)

response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Votre message"}]
)
```

### 7.2 File Analysis
```python
# Analyse de documents via multimodal
response = client.chat.completions.create(
    model="qwen-vl-max",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analysez ce document"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,{base64_doc}"}
            }
        ]
    }]
)
```

### 7.3 Function Calling
```python
# Via Qwen-Agent
from qwen_agent.llm import get_chat_model

llm = get_chat_model({
    "model": "qwen-max",
    "api_key": "YOUR_API_KEY"
})

functions = [{
    "name": "get_weather",
    "description": "Obtient la météo",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        }
    }
}]

for responses in llm.chat(
    messages=[{"role": "user", "content": "Météo à Paris?"}],
    functions=functions
):
    pass
```

### 7.4 Output Formatting
```python
response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Répondez en JSON"}],
    response_format={"type": "json_object"}
)
```

## 8. DEEPSEEK API

### 8.1 Chat
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Votre message"}]
)
```

### 8.2 File Analysis
```python
# Analyse d'images avec vision model
import base64

with open("document.jpg", "rb") as img_file:
    base64_img = base64.b64encode(img_file.read()).decode('utf-8')

response = client.chat.completions.create(
    model="deepseek-vl-7b-chat",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analysez ce document"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
            }
        ]
    }]
)
```

### 8.3 Image Generation (Janus Pro)
```python
# Utilisation du modèle Janus Pro pour génération d'images
# API séparée pour Janus Pro
response = client.images.generate(
    model="janus-pro-7b",
    prompt="Chat réaliste dans un jardin",
    size="1024x1024"
)
```

### 8.4 Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Obtient la météo",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Météo à Paris?"}],
    tools=tools
)
```

### 8.5 Output Formatting
```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "Répondez en JSON"}],
    response_format={"type": "json_object"}
)
```

## 9. KIMI K2 API

### 9.1 Chat
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_KIMI_API_KEY",
    base_url="https://api.moonshot.cn/v1"
)

response = client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[{"role": "user", "content": "Votre message"}]
)
```

### 9.2 File Analysis
```python
# Analyse de longs documents (256K context)
with open("long_document.txt", "r") as f:
    content = f.read()

response = client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[{
        "role": "user",
        "content": f"Analysez ce document: {content}"
    }]
)
```

### 9.3 Function Calling
```python
# Kimi K2 avec capacités agentic
tools = [{
    "type": "function",
    "function": {
        "name": "analyze_data",
        "description": "Analyse des données",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string"}
            }
        }
    }
}]

response = client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[{"role": "user", "content": "Analysez ces données"}],
    tools=tools,
    tool_choice="auto"
)
```

### 9.4 Output Formatting
```python
response = client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[{
        "role": "system",
        "content": "Répondez toujours en JSON valide"
    }, {
        "role": "user",
        "content": "Analysez cette situation"
    }]
)
```

## Notes Techniques Importantes

### Authentification
- **Gemini**: Clé API Google AI
- **OpenAI**: Clé API OpenAI
- **Mistral**: Clé API Mistral
- **Anthropic**: Clé API Anthropic
- **Grok**: Clé API xAI
- **Perplexity**: Clé API Perplexity
- **Qwen**: DashScope API key
- **DeepSeek**: Clé API DeepSeek
- **Kimi K2**: Clé API Moonshot

### Limites et Considérations
- **Rate Limits**: Chaque provider a ses propres limites
- **Token Limits**: Variables selon les modèles
- **Pricing**: Coûts différents par provider et fonctionnalité
- **Latence**: Performance variable selon la complexité

### Recommandations d'Implémentation
1. Utilisez des wrappers pour standardiser les interfaces
2. Implémentez un système de fallback entre providers
3. Gérez les erreurs spécifiques à chaque API
4. Monitorer les coûts et performances
5. Respectez les bonnes pratiques de sécurité pour les clés API

Cette documentation doit être mise à jour régulièrement car les APIs évoluent rapidement.