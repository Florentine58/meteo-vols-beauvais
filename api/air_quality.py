"""
Module pour récupérer les données de qualité de l'air via OpenMeteo Air Quality API.

Données disponibles (gratuites) :
- PM2.5, PM10 (particules fines)
- CO (monoxyde de carbone)
- NO2 (dioxyde d'azote)
- O3 (ozone)
- SO2 (dioxyde de soufre)
- European AQI (indice qualité air)

Documentation : https://open-meteo.com/en/docs/air-quality-api
"""

import requests
from datetime import datetime, timedelta

# Coordonnées de Beauvais (aéroport)
BEAUVAIS_LAT = 49.4544
BEAUVAIS_LON = 2.1106

# URL de l'API
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


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
            aqi_color = "#22C55E"  # vert
        elif aqi <= 40:
            aqi_level = "Bon"
            aqi_color = "#86EFAC"  # vert clair
        elif aqi <= 60:
            aqi_level = "Modéré"
            aqi_color = "#EAB308"  # jaune
        elif aqi <= 80:
            aqi_level = "Médiocre"
            aqi_color = "#F97316"  # orange
        elif aqi <= 100:
            aqi_level = "Mauvais"
            aqi_color = "#EF4444"  # rouge
        else:
            aqi_level = "Très mauvais"
            aqi_color = "#7C2D12"  # rouge foncé
        
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


def get_air_quality_history(days=7):
    """
    Récupère l'historique de la qualité de l'air.
    Note: L'API historique OpenMeteo pour air quality est limitée.
    
    Args:
        days (int): Nombre de jours d'historique
    
    Returns:
        dict: Données historiques ou None
    """
    # L'API air-quality a un historique limité, on utilise les prévisions passées
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
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
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "timezone": "Europe/Paris"
    }
    
    try:
        response = requests.get(AIR_QUALITY_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("hourly")
        
    except requests.RequestException as e:
        print(f"Erreur historique qualité air: {e}")
        return None


def calculate_aviation_air_impact(flights_count, wind_speed):
    """
    Estime l'impact des activités aéroportuaires sur la qualité de l'air.
    
    Cette fonction utilise des facteurs simplifiés pour estimer
    l'impact relatif du trafic aérien sur la qualité de l'air locale.
    
    Args:
        flights_count (int): Nombre de vols dans la zone
        wind_speed (float): Vitesse du vent en km/h
    
    Returns:
        dict: Estimation de l'impact
    """
    # Facteurs d'émission simplifiés (kg par mouvement avion)
    # Sources: ICAO, EUROCONTROL
    CO2_PER_LTO = 2.5  # tonnes CO2 par cycle LTO (Landing/Take-Off)
    NOX_PER_LTO = 8.5  # kg NOx par LTO
    PM_PER_LTO = 0.3   # kg particules par LTO
    
    # Dispersion selon le vent (plus le vent est fort, meilleure dispersion)
    if wind_speed > 30:
        dispersion_factor = 0.3  # Très bonne dispersion
    elif wind_speed > 20:
        dispersion_factor = 0.5  # Bonne dispersion
    elif wind_speed > 10:
        dispersion_factor = 0.7  # Dispersion moyenne
    else:
        dispersion_factor = 1.0  # Faible dispersion (accumulation)
    
    # Calculs
    co2_estimate = flights_count * CO2_PER_LTO
    nox_estimate = flights_count * NOX_PER_LTO * dispersion_factor
    pm_estimate = flights_count * PM_PER_LTO * dispersion_factor
    
    # Score d'impact (0-100, 100 = fort impact)
    base_impact = min(100, flights_count * 3)  # 33 vols = impact max
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


def get_aqi_health_recommendations(aqi):
    """
    Retourne des recommandations de santé basées sur l'AQI.
    
    Args:
        aqi (int): European Air Quality Index
    
    Returns:
        dict: Recommandations
    """
    if aqi <= 20:
        return {
            "level": "Excellent",
            "icon": "🟢",
            "general": "Qualité de l'air idéale pour toutes les activités.",
            "sensitive": "Aucune restriction.",
            "outdoor": "Parfait pour les activités en extérieur."
        }
    elif aqi <= 40:
        return {
            "level": "Bon",
            "icon": "🟢",
            "general": "Qualité de l'air satisfaisante.",
            "sensitive": "Très peu de risque pour les personnes sensibles.",
            "outdoor": "Conditions favorables."
        }
    elif aqi <= 60:
        return {
            "level": "Modéré",
            "icon": "🟡",
            "general": "Qualité de l'air acceptable.",
            "sensitive": "Les personnes sensibles peuvent ressentir des effets.",
            "outdoor": "Activités normales possibles."
        }
    elif aqi <= 80:
        return {
            "level": "Médiocre",
            "icon": "🟠",
            "general": "Risque pour la santé des personnes sensibles.",
            "sensitive": "Limiter les activités prolongées en extérieur.",
            "outdoor": "Réduire les efforts intenses."
        }
    elif aqi <= 100:
        return {
            "level": "Mauvais",
            "icon": "🔴",
            "general": "Effets sur la santé possibles pour tous.",
            "sensitive": "Éviter les sorties si possible.",
            "outdoor": "Limiter les activités extérieures."
        }
    else:
        return {
            "level": "Très mauvais",
            "icon": "🟤",
            "general": "Alerte sanitaire - Effets graves possibles.",
            "sensitive": "Rester à l'intérieur.",
            "outdoor": "Éviter toute activité extérieure."
        }


# =============================================================================
# Test du module
# =============================================================================
if __name__ == "__main__":
    print("=== Test du module Air Quality ===\n")
    
    # Test qualité actuelle
    print("1. Qualité de l'air actuelle:")
    current = get_current_air_quality()
    if current:
        print(f"   PM2.5: {current.get('pm2_5')} µg/m³")
        print(f"   PM10: {current.get('pm10')} µg/m³")
        print(f"   NO2: {current.get('nitrogen_dioxide')} µg/m³")
        print(f"   O3: {current.get('ozone')} µg/m³")
        print(f"   AQI: {current.get('european_aqi')} - {current.get('aqi_level')}")
    
    print()
    
    # Test impact aviation
    print("2. Estimation impact aviation (20 vols, vent 25 km/h):")
    impact = calculate_aviation_air_impact(20, 25)
    print(f"   CO2: {impact['co2_tonnes']} tonnes")
    print(f"   NOx: {impact['nox_kg']} kg")
    print(f"   PM: {impact['pm_kg']} kg")
    print(f"   Impact: {impact['impact_level']} ({impact['impact_score']}/100)")
