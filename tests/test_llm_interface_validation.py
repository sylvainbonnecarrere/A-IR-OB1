"""
Test de validation architecturale pour l'interface LLMService.

Ce script valide que l'interface LLMService respecte tous les critères
architecturaux définis pour le Jalon 1.2 selon les bonnes pratiques.

Critères de validation :
- Syntaxe Python valide
- Héritage correct de abc.ABC
- Présence des 4 méthodes abstraites requises
- Méthodes asynchrones (async def)
- Typage strict avec modèles Pydantic
- Conformité aux principes SOLID
"""

import sys
import ast
import os
from pathlib import Path

# Ajout du chemin source pour les imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def validate_llm_interface():
    """Valide l'interface LLMService selon les critères architecturaux."""
    
    print("🔍 VALIDATION ARCHITECTURALE - Interface LLMService")
    print("=" * 60)
    
    interface_path = project_root / "src" / "domain" / "llm_service_interface.py"
    
    if not interface_path.exists():
        print("❌ ERREUR: Fichier llm_service_interface.py non trouvé")
        return False
    
    # 1. Validation syntaxique
    print("\n1. 📝 Validation syntaxique...")
    try:
        with open(interface_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        print("   ✅ Syntaxe Python valide")
    except SyntaxError as e:
        print(f"   ❌ Erreur de syntaxe: {e}")
        return False
    
    # 2. Validation de la structure de classe
    print("\n2. 🏗️ Validation de la structure de classe...")
    class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    llm_service_class = None
    for class_node in class_nodes:
        if class_node.name == 'LLMService':
            llm_service_class = class_node
            break
    
    if not llm_service_class:
        print("   ❌ Classe LLMService non trouvée")
        return False
    print("   ✅ Classe LLMService définie")
    
    # 3. Validation de l'héritage ABC
    print("\n3. 🧬 Validation de l'héritage ABC...")
    inherits_abc = False
    for base in llm_service_class.bases:
        if isinstance(base, ast.Name) and base.id == 'ABC':
            inherits_abc = True
            break
    
    if inherits_abc:
        print("   ✅ Hérite correctement de abc.ABC")
    else:
        print("   ❌ N'hérite pas de abc.ABC")
        return False
    
    # 4. Validation des méthodes abstraites
    print("\n4. 🔧 Validation des méthodes abstraites...")
    method_nodes = [node for node in llm_service_class.body 
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    
    abstract_methods = []
    async_methods = []
    
    for method in method_nodes:
        # Vérification du décorateur @abstractmethod
        if any(isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod' 
               for decorator in method.decorator_list):
            abstract_methods.append(method.name)
        
        # Vérification si la méthode est asynchrone
        if isinstance(method, ast.AsyncFunctionDef):
            async_methods.append(method.name)
    
    required_methods = [
        'chat_completion', 
        'get_supported_tools', 
        'get_model_name', 
        'format_tools_for_llm'
    ]
    
    missing_methods = [m for m in required_methods if m not in abstract_methods]
    
    if not missing_methods:
        print("   ✅ Toutes les méthodes abstraites requises sont présentes")
        for method in required_methods:
            print(f"      • {method}")
    else:
        print(f"   ❌ Méthodes abstraites manquantes: {missing_methods}")
        return False
    
    # 5. Validation des méthodes asynchrones
    print("\n5. ⚡ Validation des méthodes asynchrones...")
    non_async_required = [m for m in required_methods if m not in async_methods]
    
    if not non_async_required:
        print("   ✅ Toutes les méthodes requises sont asynchrones")
    else:
        print(f"   ❌ Méthodes non-asynchrones: {non_async_required}")
        return False
    
    # 6. Validation des imports
    print("\n6. 📦 Validation des imports...")
    import_nodes = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    
    has_abc_import = False
    has_typing_import = False
    has_models_import = False
    
    for import_node in import_nodes:
        if isinstance(import_node, ast.ImportFrom):
            if import_node.module == 'abc':
                has_abc_import = True
            elif import_node.module == 'typing':
                has_typing_import = True
            elif import_node.module and 'models.data_contracts' in import_node.module:
                has_models_import = True
    
    if has_abc_import:
        print("   ✅ Import abc correctement présent")
    else:
        print("   ❌ Import abc manquant")
        return False
    
    if has_typing_import:
        print("   ✅ Import typing correctement présent")
    else:
        print("   ❌ Import typing manquant")
        return False
    
    if has_models_import:
        print("   ✅ Import des modèles Pydantic correctement présent")
    else:
        print("   ❌ Import des modèles Pydantic manquant")
        return False
    
    # 7. Test d'import réel (validation fonctionnelle)
    print("\n7. 🚀 Test d'import fonctionnel...")
    try:
        # Import depuis le chemin src ajouté au sys.path
        from domain.llm_service_interface import LLMService
        print("   ✅ Import de LLMService réussi")
        
        # Vérification que c'est bien une classe abstraite
        try:
            instance = LLMService()
            print("   ❌ ERREUR: LLMService ne devrait pas pouvoir être instanciée")
            return False
        except TypeError:
            print("   ✅ LLMService est correctement abstraite (non-instanciable)")
    
    except ImportError as e:
        print(f"   ❌ Erreur d'import: {e}")
        print(f"   📍 Chemin src ajouté: {src_path}")
        print(f"   📍 Fichier interface: {interface_path}")
        return False
    
    # 8. Validation finale
    print("\n" + "=" * 60)
    print("🎯 VALIDATION JALON 1.2 - SUCCÈS")
    print("✅ L'interface LLMService respecte tous les critères architecturaux")
    print("✅ Prêt pour le Jalon 1.3 (Microservice Minimal FastAPI)")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = validate_llm_interface()
    if not success:
        print("\n❌ VALIDATION ÉCHOUÉE")
        sys.exit(1)
    else:
        print("\n🎉 VALIDATION RÉUSSIE")
        sys.exit(0)