"""Implémentations réelles des outils que l'IA peut appeler"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json


def get_current_time(timezone_name: Optional[str] = "UTC") -> str:
    """
    Obtient l'heure et la date actuelles du système
    
    Args:
        timezone_name: Fuseau horaire (UTC par défaut)
        
    Returns:
        String formatée avec l'heure actuelle
    """
    try:
        if timezone_name == "UTC" or timezone_name is None:
            current_time = datetime.now(timezone.utc)
            tz_display = "UTC"
        elif timezone_name.lower() == "europe/paris":
            # Simulation d'un fuseau horaire (en production, utiliser pytz)
            current_time = datetime.now(timezone.utc)
            # Approximation UTC+1 pour Paris (sans gestion DST)
            current_time = current_time.replace(hour=(current_time.hour + 1) % 24)
            tz_display = "Europe/Paris"
        else:
            # Fuseau par défaut si non reconnu
            current_time = datetime.now(timezone.utc)
            tz_display = timezone_name
            
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return f"Heure actuelle: {formatted_time} ({tz_display})"
        
    except Exception as e:
        return f"Erreur lors de la récupération de l'heure: {str(e)}"


def complex_api_call(city: str) -> str:
    """
    Simule un appel API complexe pour obtenir des informations sur une ville
    
    Args:
        city: Nom de la ville
        
    Returns:
        Information formatée sur la ville
    """
    try:
        # Simulation d'un appel API bloquant
        time.sleep(0.5)  # Simule la latence réseau
        
        # Base de données simulée de villes
        city_data = {
            "paris": {
                "country": "France",
                "population": "2,161,000",
                "temperature": "15°C",
                "weather": "Partiellement nuageux",
                "timezone": "Europe/Paris"
            },
            "london": {
                "country": "United Kingdom", 
                "population": "8,982,000",
                "temperature": "12°C",
                "weather": "Pluvieux",
                "timezone": "Europe/London"
            },
            "tokyo": {
                "country": "Japan",
                "population": "13,960,000", 
                "temperature": "22°C",
                "weather": "Ensoleillé",
                "timezone": "Asia/Tokyo"
            },
            "new york": {
                "country": "United States",
                "population": "8,336,000",
                "temperature": "18°C", 
                "weather": "Nuageux",
                "timezone": "America/New_York"
            }
        }
        
        city_key = city.lower().strip()
        
        if city_key in city_data:
            data = city_data[city_key]
            result = f"""Informations pour {city.title()}:
Pays: {data['country']}
Population: {data['population']} habitants
Température: {data['temperature']}
Météo: {data['weather']}
Fuseau horaire: {data['timezone']}
Source: API Météo Simulée"""
        else:
            result = f"Ville '{city}' non trouvée dans la base de données.\nVilles disponibles: Paris, London, Tokyo, New York"
            
        return result
        
    except Exception as e:
        return f"Erreur lors de l'appel API pour {city}: {str(e)}"


def calculate_expression(expression: str) -> str:
    """
    Évalue une expression mathématique simple de façon sécurisée
    
    Args:
        expression: Expression mathématique (ex: "2 + 3 * 4")
        
    Returns:
        Résultat de l'expression ou message d'erreur
    """
    try:
        # Nettoyage et sécurisation de l'expression
        expression = expression.strip()
        
        # Vérification basique de sécurité (pas de lettres sauf en variables simples)
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return f"Expression non autorisée: '{expression}'. Seuls les chiffres et opérateurs (+, -, *, /, (), espace) sont autorisés."
        
        # Évaluation sécurisée
        result = eval(expression, {"__builtins__": {}}, {})
        
        return f"Calcul: {expression} = {result}"
        
    except ZeroDivisionError:
        return f"Erreur: Division par zéro dans '{expression}'"
    except SyntaxError:
        return f"Erreur de syntaxe dans l'expression: '{expression}'"
    except Exception as e:
        return f"Erreur lors du calcul de '{expression}': {str(e)}"


def get_system_info() -> str:
    """
    Obtient des informations basiques sur le système
    
    Returns:
        Informations système formatées
    """
    try:
        import platform
        import psutil
        
        # Informations système
        system_info = {
            "os": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": f"{psutil.virtual_memory().total // (1024**3)} GB",
            "memory_available": f"{psutil.virtual_memory().available // (1024**3)} GB"
        }
        
        result = f"""Informations Système:
OS: {system_info['os']}
Version: {system_info['version']}
Architecture: {system_info['architecture']}
Processeur: {system_info['processor']}
Python: {system_info['python_version']}
CPU Cores: {system_info['cpu_count']}
RAM Totale: {system_info['memory_total']}
RAM Disponible: {system_info['memory_available']}"""
        
        return result
        
    except ImportError:
        return "Module psutil non disponible. Informations système limitées."
    except Exception as e:
        return f"Erreur lors de la récupération des informations système: {str(e)}"