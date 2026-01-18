"""
Module pour récupérer les données météo de Beauvais via OpenMeteo API.

Inclut : météo actuelle, prévisions 7 jours, et historique 30 jours.
Documentation API : https://open-meteo.com/
"""

import requests
from datetime import datetime, timedelta

# Coordonnées de Beauvais
BEAUVAIS_LAT = 49.4295
BEAUVAIS_LON = 2.0807

# URL de base des APIs OpenMeteo
BASE_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"


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
        response.raise_for_status()
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


def get_7day_forecast():
    """
    Récupère les prévisions météo pour les 7 prochains jours.
    
    Returns:
        dict: Prévisions journalières ou None si erreur
    """
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "weather_code"
        ],
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("daily")
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des prévisions 7 jours : {e}")
        return None


def get_historical_weather(days=30):
    """
    Récupère l'historique météo des X derniers jours.
    
    Args:
        days (int): Nombre de jours d'historique (max 90)
    
    Returns:
        dict: Données historiques journalières ou None si erreur
    """
    end_date = datetime.now() - timedelta(days=1)  # Hier (données complètes)
    start_date = end_date - timedelta(days=days)
    
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "weather_code"
        ],
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(HISTORICAL_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("daily")
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération de l'historique météo : {e}")
        return None


def get_aviation_conditions_forecast():
    """
    Récupère les prévisions avec analyse pour l'aviation.
    
    Returns:
        list: Liste des jours avec score d'impact aviation
    """
    forecast = get_7day_forecast()
    
    if not forecast:
        return None
    
    aviation_forecast = []
    
    for i in range(len(forecast['time'])):
        date = forecast['time'][i]
        wind_max = forecast['wind_speed_10m_max'][i]
        wind_gusts = forecast['wind_gusts_10m_max'][i]
        precipitation = forecast['precipitation_sum'][i]
        weather_code = forecast['weather_code'][i]
        
        # Calculer le score d'impact (100 = parfait, 0 = très mauvais)
        score = 100
        alerts = []
        
        # Impact du vent
        if wind_max > 50:
            score -= 40
            alerts.append(f"🌪️ Vent très fort ({wind_max} km/h)")
        elif wind_max > 35:
            score -= 25
            alerts.append(f"💨 Vent fort ({wind_max} km/h)")
        elif wind_max > 25:
            score -= 10
            alerts.append(f"💨 Vent modéré ({wind_max} km/h)")
        
        # Impact des rafales
        if wind_gusts and wind_gusts > 60:
            score -= 20
            alerts.append(f"⚠️ Rafales dangereuses ({wind_gusts} km/h)")
        elif wind_gusts and wind_gusts > 45:
            score -= 10
            alerts.append(f"⚠️ Rafales fortes ({wind_gusts} km/h)")
        
        # Impact des précipitations
        if precipitation > 20:
            score -= 25
            alerts.append(f"🌧️ Fortes précipitations ({precipitation} mm)")
        elif precipitation > 10:
            score -= 15
            alerts.append(f"🌧️ Précipitations modérées ({precipitation} mm)")
        elif precipitation > 5:
            score -= 5
            alerts.append(f"🌧️ Légères précipitations ({precipitation} mm)")
        
        # Impact du code météo (brouillard, orage, neige)
        if weather_code in [45, 48]:  # Brouillard
            score -= 30
            alerts.append("🌫️ Brouillard prévu")
        elif weather_code in [95, 96, 99]:  # Orage
            score -= 35
            alerts.append("⛈️ Orage prévu")
        elif weather_code in [71, 73, 75, 77]:  # Neige
            score -= 30
            alerts.append("🌨️ Neige prévue")
        
        # S'assurer que le score reste entre 0 et 100
        score = max(0, min(100, score))
        
        # Déterminer le niveau d'alerte
        if score >= 80:
            level = "green"
            status = "✅ Conditions favorables"
        elif score >= 50:
            level = "yellow"
            status = "⚠️ Vigilance recommandée"
        else:
            level = "red"
            status = "❌ Conditions difficiles"
        
        aviation_forecast.append({
            "date": date,
            "date_formatted": datetime.strptime(date, "%Y-%m-%d").strftime("%A %d/%m"),
            "temp_max": forecast['temperature_2m_max'][i],
            "temp_min": forecast['temperature_2m_min'][i],
            "wind_max": wind_max,
            "wind_gusts": wind_gusts,
            "precipitation": precipitation,
            "weather_code": weather_code,
            "score": score,
            "level": level,
            "status": status,
            "alerts": alerts
        })
    
    return aviation_forecast


def get_weather_code_description(code):
    """
    Retourne la description d'un code météo WMO.
    """
    weather_codes = {
        0: ("☀️", "Ciel dégagé"),
        1: ("🌤️", "Peu nuageux"),
        2: ("⛅", "Partiellement nuageux"),
        3: ("☁️", "Couvert"),
        45: ("🌫️", "Brouillard"),
        48: ("🌫️", "Brouillard givrant"),
        51: ("🌧️", "Bruine légère"),
        53: ("🌧️", "Bruine modérée"),
        55: ("🌧️", "Bruine dense"),
        61: ("🌧️", "Pluie légère"),
        63: ("🌧️", "Pluie modérée"),
        65: ("🌧️", "Pluie forte"),
        66: ("🌧️❄️", "Pluie verglaçante légère"),
        67: ("🌧️❄️", "Pluie verglaçante forte"),
        71: ("🌨️", "Neige légère"),
        73: ("🌨️", "Neige modérée"),
        75: ("🌨️", "Neige forte"),
        77: ("🌨️", "Grains de neige"),
        80: ("🌦️", "Averses légères"),
        81: ("🌦️", "Averses modérées"),
        82: ("🌦️", "Averses fortes"),
        85: ("🌨️", "Averses de neige légères"),
        86: ("🌨️", "Averses de neige fortes"),
        95: ("⛈️", "Orage"),
        96: ("⛈️🌨️", "Orage avec grêle légère"),
        99: ("⛈️🌨️", "Orage avec grêle forte")
    }
    
    return weather_codes.get(code, ("❓", "Inconnu"))


# Code pour tester le module directement
if __name__ == "__main__":
    print("=== Test du module météo ===")
    print()
    
    # Météo actuelle
    weather = get_current_weather()
    if weather:
        print("Météo actuelle à Beauvais :")
        print(f"  Température : {weather['temperature_2m']}°C")
        print(f"  Humidité : {weather['relative_humidity_2m']}%")
        print(f"  Vent : {weather['wind_speed_10m']} km/h")
    
    print()
    
    # Prévisions 7 jours
    print("Prévisions 7 jours avec impact aviation :")
    forecast = get_aviation_conditions_forecast()
    if forecast:
        for day in forecast:
            print(f"  {day['date_formatted']}: Score {day['score']}/100 - {day['status']}")
            for alert in day['alerts']:
                print(f"    → {alert}")
    
    print()
    
    # Historique
    print("Historique météo (30 derniers jours) :")
    history = get_historical_weather(days=30)
    if history:
        print(f"  Jours récupérés : {len(history['time'])}")
        print(f"  Temp moyenne du mois : {sum(history['temperature_2m_mean'])/len(history['temperature_2m_mean']):.1f}°C")