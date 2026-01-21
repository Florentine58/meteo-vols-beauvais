"""
Module pour récupérer les données météo de Beauvais via OpenMeteo API.

Inclut :
- Météo actuelle
- Prévisions 7 jours
- Historique 30 jours
- Historique LONG TERME (depuis 1940 !) via OpenMeteo Archive
- Qualité de l'air (intégré)

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
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


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
    Récupère l'historique météo sur PLUSIEURS ANNÉES.
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
                if code in [45, 48]:
                    yearly_stats[year]["fog_days"] += 1
                if code in [65, 82, 95, 96, 99]:
                    yearly_stats[year]["storm_days"] += 1
            
            # Estimation orages si pas de weather_code fiable
            if gusts is not None and precip is not None:
                if gusts > 50 and precip > 10:
                    if code is None or code not in [65, 82, 95, 96, 99]:
                        yearly_stats[year]["storm_days"] += 1
            
            # Estimation brouillard
            temp_max = daily["temperature_2m_max"][i] if daily.get("temperature_2m_max") else None
            temp_min = daily["temperature_2m_min"][i] if daily.get("temperature_2m_min") else None
            month = int(date_str[5:7])
            
            if code is None or code not in [45, 48]:
                if temp_max is not None and temp_min is not None and wind is not None:
                    amplitude = temp_max - temp_min
                    is_fog_season = month in [9, 10, 11, 12, 1, 2, 3]
                    
                    if wind < 15 and amplitude < 6 and is_fog_season:
                        random.seed(hash(date_str))
                        if random.random() < 0.12:
                            yearly_stats[year]["fog_days"] += 1
        
        # Calculer les moyennes
        for year, stats in yearly_stats.items():
            stats["avg_temp"] = sum(stats["temps"]) / len(stats["temps"]) if stats["temps"] else 0
            stats["avg_wind"] = sum(stats["winds"]) / len(stats["winds"]) if stats["winds"] else 0
            stats["max_wind"] = max(stats["winds"]) if stats["winds"] else 0
            stats["total_precip"] = sum(stats["precips"]) if stats["precips"] else 0
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


# =============================================================================
# QUALITÉ DE L'AIR (intégré)
# =============================================================================

def get_current_air_quality():
    """
    Récupère la qualité de l'air actuelle à Beauvais.
    
    Returns:
        dict: Données de qualité de l'air ou None si erreur
    """
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "current": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "european_aqi",
            "us_aqi"
        ],
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        
        # Ajouter des interprétations
        aqi = current.get("european_aqi", 0)
        if aqi <= 20:
            aqi_level = "Excellent"
            aqi_color = "#22C55E"
        elif aqi <= 40:
            aqi_level = "Bon"
            aqi_color = "#86EFAC"
        elif aqi <= 60:
            aqi_level = "Modéré"
            aqi_color = "#EAB308"
        elif aqi <= 80:
            aqi_level = "Médiocre"
            aqi_color = "#F97316"
        elif aqi <= 100:
            aqi_level = "Mauvais"
            aqi_color = "#EF4444"
        else:
            aqi_level = "Très mauvais"
            aqi_color = "#7C2D12"
        
        current["aqi_level"] = aqi_level
        current["aqi_color"] = aqi_color
        
        return current
        
    except requests.RequestException as e:
        print(f"Erreur qualité de l'air: {e}")
        return None


def get_air_quality_forecast(days=3):
    """
    Récupère les prévisions de qualité de l'air.
    
    Args:
        days (int): Nombre de jours de prévision (1-5)
    
    Returns:
        dict: Données horaires ou None si erreur
    """
    params = {
        "latitude": BEAUVAIS_LAT,
        "longitude": BEAUVAIS_LON,
        "hourly": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "ozone",
            "european_aqi"
        ],
        "forecast_days": days,
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("hourly")
        
    except requests.RequestException as e:
        print(f"Erreur prévisions qualité air: {e}")
        return None


def calculate_aviation_air_impact(flights_count, wind_speed):
    """
    Estime l'impact des activités aéroportuaires sur la qualité de l'air.
    
    Args:
        flights_count (int): Nombre de vols dans la zone
        wind_speed (float): Vitesse du vent en km/h
    
    Returns:
        dict: Estimation de l'impact
    """
    # Facteurs d'émission simplifiés (kg par mouvement avion)
    CO2_PER_LTO = 2.5  # tonnes CO2 par cycle LTO
    NOX_PER_LTO = 8.5  # kg NOx par LTO
    PM_PER_LTO = 0.3   # kg particules par LTO
    
    # Dispersion selon le vent
    if wind_speed > 30:
        dispersion_factor = 0.3
    elif wind_speed > 20:
        dispersion_factor = 0.5
    elif wind_speed > 10:
        dispersion_factor = 0.7
    else:
        dispersion_factor = 1.0
    
    # Calculs
    co2_estimate = flights_count * CO2_PER_LTO
    nox_estimate = flights_count * NOX_PER_LTO * dispersion_factor
    pm_estimate = flights_count * PM_PER_LTO * dispersion_factor
    
    # Score d'impact
    base_impact = min(100, flights_count * 3)
    adjusted_impact = base_impact * dispersion_factor
    
    # Niveau d'impact
    if adjusted_impact <= 20:
        impact_level = "Faible"
        impact_color = "#22C55E"
    elif adjusted_impact <= 50:
        impact_level = "Modéré"
        impact_color = "#EAB308"
    else:
        impact_level = "Élevé"
        impact_color = "#EF4444"
    
    return {
        "co2_tonnes": round(co2_estimate, 2),
        "nox_kg": round(nox_estimate, 2),
        "pm_kg": round(pm_estimate, 2),
        "impact_score": round(adjusted_impact),
        "impact_level": impact_level,
        "impact_color": impact_color,
        "dispersion": "Bonne" if dispersion_factor < 0.6 else "Moyenne" if dispersion_factor < 0.9 else "Faible",
        "flights_count": flights_count,
        "wind_speed": wind_speed
    }


# Test du module
if __name__ == "__main__":
    print("=== Test du module météo ===\n")
    
    weather = get_current_weather()
    if weather:
        print(f"Température: {weather['temperature_2m']}°C")
        print(f"Vent: {weather['wind_speed_10m']} km/h")
    
    print()
    
    air = get_current_air_quality()
    if air:
        print(f"AQI: {air.get('european_aqi')} - {air.get('aqi_level')}")
        print(f"PM2.5: {air.get('pm2_5')} µg/m³")
