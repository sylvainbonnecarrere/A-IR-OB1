"""ToolExecutor - Exécuteur d'outils avec routing et exécution asynchrone"""

import asyncio
import json
import traceback
from typing import Dict, Callable, Any, List, Optional
from src.models.data_contracts import ToolCall, ToolResult
from src.infrastructure.tools import (
    get_current_time,
    complex_api_call, 
    calculate_expression,
    get_system_info
)


class ToolExecutor:
    """
    Exécuteur d'outils responsable du routing et de l'exécution asynchrone des tools
    """
    
    def __init__(self):
        """Initialise l'exécuteur avec le registre des outils disponibles"""
        self.tool_registry: Dict[str, Callable] = {
            "get_current_time": get_current_time,
            "complex_api_call": complex_api_call,
            "calculate_expression": calculate_expression,
            "get_system_info": get_system_info
        }
    
    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Exécute un outil spécifique de façon asynchrone
        
        Args:
            tool_call: Appel d'outil à exécuter
            
        Returns:
            Résultat de l'exécution de l'outil
        """
        try:
            # Vérification que l'outil existe
            if tool_call.tool_name not in self.tool_registry:
                available_tools = list(self.tool_registry.keys())
                error_msg = f"Outil '{tool_call.tool_name}' non trouvé. Outils disponibles: {available_tools}"
                
                return ToolResult(
                    tool_call_id=tool_call.id,
                    success=False,
                    result=None,
                    error=error_msg
                )
            
            # Récupération de la fonction
            tool_function = self.tool_registry[tool_call.tool_name]
            
            # Préparation des arguments
            kwargs = self._prepare_arguments(tool_function, tool_call.arguments)
            
            # Exécution asynchrone de l'outil (même si la fonction est synchrone)
            result = await asyncio.to_thread(tool_function, **kwargs)
            
            return ToolResult(
                tool_call_id=tool_call.id,
                success=True,
                result=result,
                error=None
            )
            
        except Exception as e:
            # Capture complète de l'erreur pour debugging
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
                "traceback": traceback.format_exc()
            }
            
            return ToolResult(
                tool_call_id=tool_call.id,
                success=False,
                result=None,
                error=f"Erreur lors de l'exécution de '{tool_call.tool_name}': {str(e)}"
            )
    
    async def execute_multiple_tools(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Exécute plusieurs outils en parallèle
        
        Args:
            tool_calls: Liste des appels d'outils à exécuter
            
        Returns:
            Liste des résultats d'exécution
        """
        if not tool_calls:
            return []
        
        # Exécution en parallèle pour de meilleures performances
        tasks = [self.execute_tool(tool_call) for tool_call in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traitement des exceptions potentielles
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Création d'un ToolResult d'erreur si une exception s'est produite
                error_result = ToolResult(
                    tool_call_id=tool_calls[i].id,
                    success=False,
                    result=None,
                    error=f"Exception lors de l'exécution: {str(result)}"
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _prepare_arguments(self, tool_function: Callable, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare et valide les arguments pour l'appel de fonction
        
        Args:
            tool_function: Fonction à appeler
            arguments: Arguments fournis par l'IA
            
        Returns:
            Arguments préparés et validés
        """
        import inspect
        
        try:
            # Inspection de la signature de la fonction
            sig = inspect.signature(tool_function)
            prepared_args = {}
            
            for param_name, param in sig.parameters.items():
                if param_name in arguments:
                    # Argument fourni par l'IA
                    value = arguments[param_name]
                    prepared_args[param_name] = value
                elif param.default != inspect.Parameter.empty:
                    # Argument optionnel avec valeur par défaut - ne pas l'inclure
                    continue
                else:
                    # Argument requis manquant
                    raise ValueError(f"Argument requis '{param_name}' manquant pour l'outil '{tool_function.__name__}'")
            
            return prepared_args
            
        except Exception as e:
            # En cas d'erreur d'inspection, on retourne les arguments tels quels
            print(f"Avertissement lors de la préparation des arguments: {e}")
            return arguments
    
    def get_available_tools(self) -> List[str]:
        """Retourne la liste des outils disponibles"""
        return list(self.tool_registry.keys())
    
    def register_tool(self, name: str, tool_function: Callable) -> None:
        """
        Enregistre un nouvel outil
        
        Args:
            name: Nom de l'outil
            tool_function: Fonction à exécuter
        """
        self.tool_registry[name] = tool_function
    
    def unregister_tool(self, name: str) -> bool:
        """
        Désenregistre un outil
        
        Args:
            name: Nom de l'outil à supprimer
            
        Returns:
            True si l'outil a été supprimé, False s'il n'existait pas
        """
        if name in self.tool_registry:
            del self.tool_registry[name]
            return True
        return False
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtient des informations détaillées sur un outil
        
        Args:
            tool_name: Nom de l'outil
            
        Returns:
            Informations sur l'outil ou None si non trouvé
        """
        if tool_name not in self.tool_registry:
            return None
        
        import inspect
        
        tool_function = self.tool_registry[tool_name]
        sig = inspect.signature(tool_function)
        
        # Extraction des informations de la fonction
        info = {
            "name": tool_name,
            "function_name": tool_function.__name__,
            "docstring": tool_function.__doc__ or "Pas de documentation disponible",
            "parameters": {},
            "is_async": inspect.iscoroutinefunction(tool_function)
        }
        
        # Analyse des paramètres
        for param_name, param in sig.parameters.items():
            param_info = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "required": param.default == inspect.Parameter.empty,
                "default": param.default if param.default != inspect.Parameter.empty else None
            }
            info["parameters"][param_name] = param_info
        
        return info