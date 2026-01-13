"""
Module pour récupérer les données météo de Beauvais via OpenMeteo API.

Documentation API : https://open-meteo.com/
"""

import requests
from datetime import datetime

# Coordonnées de Beauvais
BEAUVAIS_LAT = 49.4295
BEAUVAIS_LON = 2.0807

# URL de base de l'API OpenMeteo
BASE_URL = "https://api.open-meteo.com/v1/forecast"


def get_current_weather():
    """
    Récupère la météo actuelle à Beauvais.
    
    Returns:
        dict: Données météo actuelles ou None si erreur
    """
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "current": [
            "temperature_2m",
            "relative_humidity_2m", 
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code"
        ],
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Lève une erreur si statut != 200
        data = response.json()
        return data.get("current")
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération météo : {e}")
        return None


def get_hourly_forecast(days=1):
    """
    Récupère les prévisions horaires pour les prochains jours.
    
    Args:
        days (int): Nombre de jours de prévision (1 à 7)
    
    Returns:
        dict: Données horaires ou None si erreur
    """
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "hourly": [
            "temperature_2m",
            "precipitation",
            "wind_speed_10m",
            "visibility"
        ],
        "forecast_days": days,
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("hourly")
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des prévisions : {e}")
        return None


# Code pour tester le module directement
if __name__ == "__main__":
    print("=== Test du module météo ===")
    print()
    
    weather = get_current_weather()
    if weather:
        print("Météo actuelle à Beauvais :")
        print(f"  Température : {weather['temperature_2m']}°C")
        print(f"  Humidité : {weather['relative_humidity_2m']}%")
        print(f"  Vent : {weather['wind_speed_10m']} km/h")
    else:
        print("Impossible de récupérer la météo.")