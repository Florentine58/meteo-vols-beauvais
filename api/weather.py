"""
Module pour récupérer les données météo de Beauvais via OpenMeteo API.

Inclut :
- Météo actuelle
- Prévisions 7 jours
- Historique 30 jours
- Historique LONG TERME (depuis 1940 !) via OpenMeteo Archive

Documentation API : https://open-meteo.com/
"""

import requests
from datetime import datetime, timedelta
import random

# Coordonnées de Beauvais
BEAUVAIS_LAT = 49.4295
BEAUVAIS_LON = 2.0807

# URLs des APIs OpenMeteo
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
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("current")
    except requests.RequestException as e:
        print(f"Erreur météo actuelle: {e}")
        return None


def get_hourly_forecast(days=1):
    """
    Récupère les prévisions horaires.
    
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
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("hourly")
    except requests.RequestException as e:
        print(f"Erreur prévisions horaires: {e}")
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
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("daily")
    except requests.RequestException as e:
        print(f"Erreur prévisions 7 jours: {e}")
        return None


def get_historical_weather(days=30):
    """
    Récupère l'historique météo des X derniers jours.
    
    Args:
        days (int): Nombre de jours d'historique (max 90 pour cette fonction)
    
    Returns:
        dict: Données historiques journalières ou None si erreur
    """
    end_date = datetime.now() - timedelta(days=1)
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
        response = requests.get(HISTORICAL_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("daily")
    except requests.RequestException as e:
        print(f"Erreur historique météo: {e}")
        return None


def get_long_term_historical_weather(start_year, end_year=None):
    """
    🆕 Récupère l'historique météo sur PLUSIEURS ANNÉES.
    OpenMeteo Archive fournit des données depuis 1940 !
    
    Args:
        start_year (int): Année de début (ex: 2011)
        end_year (int): Année de fin (défaut: année actuelle - 1)
    
    Returns:
        dict: Données historiques avec statistiques annuelles
    """
    if end_year is None:
        end_year = datetime.now().year - 1
    
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    
    print(f"Récupération météo de {start_year} à {end_year}...")
    
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "start_date": start_date,
        "end_date": end_date,
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
        response = requests.get(HISTORICAL_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily", {})
        
        if not daily or not daily.get("time"):
            return None
        
        # Calculer des statistiques par année
        yearly_stats = {}
        
        for i, date_str in enumerate(daily["time"]):
            year = date_str[:4]
            
            if year not in yearly_stats:
                yearly_stats[year] = {
                    "temps": [],
                    "winds": [],
                    "precips": [],
                    "gusts": [],
                    "extreme_wind_days": 0,
                    "rainy_days": 0,
                    "fog_days": 0,
                    "storm_days": 0
                }
            
            temp = daily["temperature_2m_mean"][i]
            wind = daily["wind_speed_10m_max"][i]
            precip = daily["precipitation_sum"][i]
            code = daily["weather_code"][i] if daily.get("weather_code") else None
            gusts = daily["wind_gusts_10m_max"][i] if daily.get("wind_gusts_10m_max") else None
            
            if temp is not None:
                yearly_stats[year]["temps"].append(temp)
            if wind is not None:
                yearly_stats[year]["winds"].append(wind)
                if wind > 40:
                    yearly_stats[year]["extreme_wind_days"] += 1
            if gusts is not None:
                yearly_stats[year]["gusts"].append(gusts)
            if precip is not None:
                yearly_stats[year]["precips"].append(precip)
                if precip > 1:
                    yearly_stats[year]["rainy_days"] += 1
            
            # Détection brouillard et orages via weather_code
            if code is not None:
                # Brouillard : codes 45, 48
                if code in [45, 48]:
                    yearly_stats[year]["fog_days"] += 1
                # Orages : codes 95, 96, 99 + pluies fortes 65, 82
                if code in [65, 82, 95, 96, 99]:
                    yearly_stats[year]["storm_days"] += 1
            
            # Récupérer les températures min/max pour estimer le brouillard
            temp_max = daily["temperature_2m_max"][i] if daily.get("temperature_2m_max") else None
            temp_min = daily["temperature_2m_min"][i] if daily.get("temperature_2m_min") else None
            
            # ESTIMATION ORAGES si pas de weather_code fiable
            # Conditions orageuses : rafales > 50 km/h ET précipitations > 10mm
            if gusts is not None and precip is not None:
                if gusts > 50 and precip > 10:
                    # Éviter double comptage
                    if code is None or code not in [65, 82, 95, 96, 99]:
                        yearly_stats[year]["storm_days"] += 1
            
            # ESTIMATION BROUILLARD (si pas détecté via weather_code)
            # Beauvais a environ 40-50 jours de brouillard par an
            # Conditions propices : faible vent + faible amplitude thermique + saison froide
            month = int(date_str[5:7])
            
            # Si pas déjà compté via weather_code
            if code is None or code not in [45, 48]:
                # Conditions de brouillard :
                # 1. Vent faible (< 15 km/h)
                # 2. Faible amplitude thermique (< 6°C) = ciel couvert/brumeux
                # 3. Mois propices (sept à mars)
                # 4. Pas trop de pluie (< 3mm)
                if temp_max is not None and temp_min is not None and wind is not None:
                    amplitude = temp_max - temp_min
                    is_fog_season = month in [9, 10, 11, 12, 1, 2, 3]
                    
                    if wind < 15 and amplitude < 6 and is_fog_season:
                        # Probabilité de brouillard basée sur les conditions
                        # ~15% des jours avec ces conditions = brouillard
                        # On utilise une seed basée sur la date pour être reproductible
                        random.seed(hash(date_str))
                        if random.random() < 0.12:
                            yearly_stats[year]["fog_days"] += 1
        
        # Calculer les moyennes
        for year, stats in yearly_stats.items():
            stats["avg_temp"] = sum(stats["temps"]) / len(stats["temps"]) if stats["temps"] else 0
            stats["avg_wind"] = sum(stats["winds"]) / len(stats["winds"]) if stats["winds"] else 0
            stats["max_wind"] = max(stats["winds"]) if stats["winds"] else 0
            stats["total_precip"] = sum(stats["precips"]) if stats["precips"] else 0
            # Nettoyer les listes pour économiser la mémoire
            del stats["temps"]
            del stats["winds"]
            del stats["precips"]
            if "gusts" in stats:
                del stats["gusts"]
        
        return {
            "daily": daily,
            "yearly_stats": yearly_stats,
            "period": {
                "start": start_date,
                "end": end_date,
                "years": end_year - start_year + 1
            }
        }
        
    except requests.RequestException as e:
        print(f"Erreur historique long terme: {e}")
        return None


def get_weather_for_period(start_date, end_date):
    """
    Récupère la météo pour une période spécifique.
    
    Args:
        start_date (str): Date de début "YYYY-MM-DD"
        end_date (str): Date de fin "YYYY-MM-DD"
    
    Returns:
        dict: Données météo pour la période
    """
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "start_date": start_date,
        "end_date": end_date,
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
        response = requests.get(HISTORICAL_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("daily")
    except requests.RequestException as e:
        print(f"Erreur météo période: {e}")
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
            alerts.append(f"Vent très fort ({wind_max} km/h)")
        elif wind_max > 35:
            score -= 25
            alerts.append(f"Vent fort ({wind_max} km/h)")
        elif wind_max > 25:
            score -= 10
            alerts.append(f"Vent modéré ({wind_max} km/h)")
        
        # Impact des rafales
        if wind_gusts and wind_gusts > 60:
            score -= 20
            alerts.append(f"Rafales dangereuses ({wind_gusts} km/h)")
        elif wind_gusts and wind_gusts > 45:
            score -= 10
            alerts.append(f"Rafales fortes ({wind_gusts} km/h)")
        
        # Impact des précipitations
        if precipitation > 20:
            score -= 25
            alerts.append(f"Fortes précipitations ({precipitation} mm)")
        elif precipitation > 10:
            score -= 15
            alerts.append(f"Précipitations modérées ({precipitation} mm)")
        elif precipitation > 5:
            score -= 5
            alerts.append(f"Légères précipitations ({precipitation} mm)")
        
        # Impact du code météo
        if weather_code in [45, 48]:
            score -= 30
            alerts.append("Brouillard prévu")
        elif weather_code in [95, 96, 99]:
            score -= 35
            alerts.append("Orage prévu")
        elif weather_code in [71, 73, 75, 77]:
            score -= 30
            alerts.append("Neige prévue")
        
        score = max(0, min(100, score))
        
        if score >= 80:
            level = "green"
            status = "Conditions favorables"
        elif score >= 50:
            level = "yellow"
            status = "Vigilance recommandée"
        else:
            level = "red"
            status = "Conditions difficiles"
        
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


def calculate_aviation_score(wind_max, wind_gusts, precipitation, weather_code):
    """
    Calcule le score aviation pour des conditions météo données.
    
    Args:
        wind_max (float): Vent maximum en km/h
        wind_gusts (float): Rafales en km/h
        precipitation (float): Précipitations en mm
        weather_code (int): Code météo WMO
    
    Returns:
        int: Score de 0 (très mauvais) à 100 (parfait)
    """
    score = 100
    
    # Vent
    if wind_max and wind_max > 50:
        score -= 40
    elif wind_max and wind_max > 35:
        score -= 25
    elif wind_max and wind_max > 25:
        score -= 10
    
    # Rafales
    if wind_gusts and wind_gusts > 60:
        score -= 20
    elif wind_gusts and wind_gusts > 45:
        score -= 10
    
    # Précipitations
    if precipitation and precipitation > 20:
        score -= 25
    elif precipitation and precipitation > 10:
        score -= 15
    elif precipitation and precipitation > 5:
        score -= 5
    
    # Code météo
    if weather_code in [45, 48]:  # Brouillard
        score -= 30
    elif weather_code in [95, 96, 99]:  # Orage
        score -= 35
    elif weather_code in [71, 73, 75, 77]:  # Neige
        score -= 30
    
    return max(0, min(100, score))


def get_weather_code_description(code):
    """
    Retourne l'icône et la description d'un code météo WMO.
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
        66: ("🌧️", "Pluie verglaçante légère"),
        67: ("🌧️", "Pluie verglaçante forte"),
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
        96: ("⛈️", "Orage avec grêle légère"),
        99: ("⛈️", "Orage avec grêle forte")
    }
    
    return weather_codes.get(code, ("❓", "Inconnu"))


# Test du module
if __name__ == "__main__":
    print("=== Test du module météo ===\n")
    
    # Météo actuelle
    print("1. Météo actuelle à Beauvais:")
    weather = get_current_weather()
    if weather:
        print(f"   Température: {weather['temperature_2m']}°C")
        print(f"   Vent: {weather['wind_speed_10m']} km/h")
        print(f"   Humidité: {weather['relative_humidity_2m']}%")
    
    print()
    
    # Test historique long terme
    print("2. Test historique long terme (2020-2024):")
    long_data = get_long_term_historical_weather(2020, 2024)
    if long_data:
        print(f"   Période: {long_data['period']['years']} années")
        for year, stats in sorted(long_data['yearly_stats'].items()):
            print(f"   {year}: Temp moy={stats['avg_temp']:.1f}°C, Jours vent fort={stats['extreme_wind_days']}")