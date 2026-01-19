"""
Module pour récupérer les données de vols via AeroDataBox (RapidAPI).

Données disponibles :
- Arrivées/Départs d'un aéroport (FIDS)
- Statistiques de retards
- Statut des vols

Documentation : https://rapidapi.com/aedbx-aedbx/api/aerodatabox
Plan gratuit : ~600 appels/mois
"""

import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Clé API RapidAPI
RAPIDAPI_KEY = os.getenv("AERODATABOX_API_KEY")

# Configuration de l'API
RAPIDAPI_HOST = "aerodatabox.p.rapidapi.com"
BASE_URL = "https://aerodatabox.p.rapidapi.com"

# Aéroports
AIRPORTS = {
    "BVA": {"icao": "LFOB", "name": "Paris-Beauvais"},
    "CDG": {"icao": "LFPG", "name": "Paris-CDG"},
    "ORY": {"icao": "LFPO", "name": "Paris-Orly"}
}

# Aéroport par défaut
DEFAULT_AIRPORT = "LFOB"


def get_headers():
    """Retourne les headers pour les requêtes API."""
    if not RAPIDAPI_KEY:
        print("⚠️  Clé API non configurée. Ajoutez AERODATABOX_API_KEY dans .env")
        return None
    return {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }


def test_connection():
    """
    Teste la connexion à l'API AeroDataBox.
    
    Returns:
        dict: Statut de la connexion
    """
    headers = get_headers()
    if not headers:
        return {"status": "error", "message": "Clé API non configurée"}
    
    try:
        url = f"{BASE_URL}/health/services/feeds/FlightSchedules"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Connexion AeroDataBox OK !"}
        elif response.status_code == 429:
            return {"status": "warning", "message": "Trop de requêtes. Attends 1 minute."}
        elif response.status_code == 403:
            return {"status": "error", "message": "Clé API invalide ou quota dépassé"}
        else:
            return {"status": "error", "message": f"Erreur HTTP {response.status_code}"}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}


def get_airport_departures(airport_icao=DEFAULT_AIRPORT, hours=24):
    """
    Récupère les départs d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO (LFOB, LFPG, LFPO...)
        hours (int): Nombre d'heures à récupérer (défaut: 24)
    
    Returns:
        list: Liste des départs
    """
    headers = get_headers()
    if not headers:
        return []
    
    # Utiliser timezone-aware datetime (corrige le warning)
    now = datetime.now(timezone.utc)
    from_time = now.strftime("%Y-%m-%dT%H:%M")
    to_time = (now + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M")
    
    url = f"{BASE_URL}/flights/airports/icao/{airport_icao}/{from_time}/{to_time}"
    
    params = {
        "direction": "Departure",
        "withLeg": "true",
        "withCancelled": "true",
        "withCodeshared": "false"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            departures = data.get("departures", [])
            
            formatted = []
            for dep in departures:
                flight_info = {
                    "flight_number": dep.get("number", "N/A"),
                    "airline": dep.get("airline", {}).get("name", "N/A"),
                    "destination": dep.get("arrival", {}).get("airport", {}).get("iata", "N/A"),
                    "destination_name": dep.get("arrival", {}).get("airport", {}).get("name", "N/A"),
                    "scheduled_time": dep.get("departure", {}).get("scheduledTimeLocal", "N/A"),
                    "actual_time": dep.get("departure", {}).get("actualTimeLocal"),
                    "status": dep.get("status", "Unknown"),
                    "delay_minutes": None,
                    "aircraft": dep.get("aircraft", {}).get("model", "N/A")
                }
                
                # Calculer le retard
                scheduled = dep.get("departure", {}).get("scheduledTimeUtc")
                actual = dep.get("departure", {}).get("actualTimeUtc")
                if scheduled and actual:
                    try:
                        sched_dt = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                        actual_dt = datetime.fromisoformat(actual.replace("Z", "+00:00"))
                        delay = (actual_dt - sched_dt).total_seconds() / 60
                        flight_info["delay_minutes"] = round(delay)
                    except:
                        pass
                
                formatted.append(flight_info)
            
            return formatted
            
        elif response.status_code == 429:
            print("⚠️  Trop de requêtes (429). Attends 1 minute.")
            return []
        else:
            print(f"Erreur AeroDataBox départs: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"Erreur réseau: {e}")
        return []


def get_airport_arrivals(airport_icao=DEFAULT_AIRPORT, hours=24):
    """
    Récupère les arrivées d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO
        hours (int): Nombre d'heures à récupérer
    
    Returns:
        list: Liste des arrivées
    """
    headers = get_headers()
    if not headers:
        return []
    
    now = datetime.now(timezone.utc)
    from_time = now.strftime("%Y-%m-%dT%H:%M")
    to_time = (now + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M")
    
    url = f"{BASE_URL}/flights/airports/icao/{airport_icao}/{from_time}/{to_time}"
    
    params = {
        "direction": "Arrival",
        "withLeg": "true",
        "withCancelled": "true",
        "withCodeshared": "false"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            arrivals = data.get("arrivals", [])
            
            formatted = []
            for arr in arrivals:
                flight_info = {
                    "flight_number": arr.get("number", "N/A"),
                    "airline": arr.get("airline", {}).get("name", "N/A"),
                    "origin": arr.get("departure", {}).get("airport", {}).get("iata", "N/A"),
                    "origin_name": arr.get("departure", {}).get("airport", {}).get("name", "N/A"),
                    "scheduled_time": arr.get("arrival", {}).get("scheduledTimeLocal", "N/A"),
                    "actual_time": arr.get("arrival", {}).get("actualTimeLocal"),
                    "status": arr.get("status", "Unknown"),
                    "delay_minutes": None,
                    "aircraft": arr.get("aircraft", {}).get("model", "N/A")
                }
                
                # Calculer le retard
                scheduled = arr.get("arrival", {}).get("scheduledTimeUtc")
                actual = arr.get("arrival", {}).get("actualTimeUtc")
                if scheduled and actual:
                    try:
                        sched_dt = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                        actual_dt = datetime.fromisoformat(actual.replace("Z", "+00:00"))
                        delay = (actual_dt - sched_dt).total_seconds() / 60
                        flight_info["delay_minutes"] = round(delay)
                    except:
                        pass
                
                formatted.append(flight_info)
            
            return formatted
            
        elif response.status_code == 429:
            print("⚠️  Trop de requêtes (429). Attends 1 minute.")
            return []
        else:
            return []
            
    except requests.RequestException as e:
        print(f"Erreur réseau: {e}")
        return []


def get_delay_statistics(airport_icao=DEFAULT_AIRPORT, hours=24):
    """
    Calcule les statistiques de retards pour un aéroport.
    
    Args:
        airport_icao (str): Code ICAO
        hours (int): Période d'analyse
    
    Returns:
        dict: Statistiques complètes
    """
    departures = get_airport_departures(airport_icao, hours)
    arrivals = get_airport_arrivals(airport_icao, hours)
    
    # Extraire les retards
    dep_delays = [f["delay_minutes"] for f in departures if f.get("delay_minutes") is not None]
    arr_delays = [f["delay_minutes"] for f in arrivals if f.get("delay_minutes") is not None]
    
    # Compter les annulations
    cancelled_dep = len([f for f in departures if "cancel" in f.get("status", "").lower()])
    cancelled_arr = len([f for f in arrivals if "cancel" in f.get("status", "").lower()])
    
    # Compter les retards > 15 min
    delayed_dep = len([d for d in dep_delays if d > 15])
    delayed_arr = len([d for d in arr_delays if d > 15])
    
    stats = {
        "airport": airport_icao,
        "period_hours": hours,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "departures": {
            "total": len(departures),
            "delayed": delayed_dep,
            "cancelled": cancelled_dep,
            "avg_delay": round(sum(dep_delays) / len(dep_delays), 1) if dep_delays else 0,
            "max_delay": max(dep_delays) if dep_delays else 0,
            "flights": departures  # Liste complète pour affichage
        },
        "arrivals": {
            "total": len(arrivals),
            "delayed": delayed_arr,
            "cancelled": cancelled_arr,
            "avg_delay": round(sum(arr_delays) / len(arr_delays), 1) if arr_delays else 0,
            "max_delay": max(arr_delays) if arr_delays else 0,
            "flights": arrivals
        },
        "summary": {
            "total_flights": len(departures) + len(arrivals),
            "total_delayed": delayed_dep + delayed_arr,
            "total_cancelled": cancelled_dep + cancelled_arr
        }
    }
    
    # Calculer le taux de ponctualité
    total = stats["summary"]["total_flights"]
    if total > 0:
        on_time = total - stats["summary"]["total_delayed"] - stats["summary"]["total_cancelled"]
        stats["summary"]["on_time_rate"] = round((on_time / total) * 100, 1)
    else:
        stats["summary"]["on_time_rate"] = None
    
    return stats


def get_airport_info(airport_icao=DEFAULT_AIRPORT):
    """
    Récupère les informations d'un aéroport.
    
    Returns:
        dict: Informations de l'aéroport
    """
    headers = get_headers()
    if not headers:
        return None
    
    url = f"{BASE_URL}/airports/icao/{airport_icao}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "icao": data.get("icao"),
                "iata": data.get("iata"),
                "name": data.get("fullName") or data.get("shortName"),
                "city": data.get("municipalityName"),
                "country": data.get("countryCode"),
                "latitude": data.get("location", {}).get("lat"),
                "longitude": data.get("location", {}).get("lon"),
                "timezone": data.get("timeZone")
            }
        return None
    except:
        return None


# =============================================================================
# TEST DU MODULE
# =============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("    TEST MODULE AERODATABOX")
    print("=" * 50)
    print()
    
    # 1. Test connexion
    print("1. Test de connexion...")
    result = test_connection()
    if result["status"] == "success":
        print(f"   ✅ {result['message']}")
    else:
        print(f"   ❌ {result['message']}")
        exit()
    print()
    
    # 2. Test avec CDG (plus de vols)
    print("2. Test avec Paris-CDG (LFPG) - plus de trafic...")
    stats = get_delay_statistics("LFPG", hours=6)  # 6h pour économiser l'API
    
    print(f"   Vols trouvés: {stats['summary']['total_flights']}")
    print(f"   - Départs: {stats['departures']['total']}")
    print(f"   - Arrivées: {stats['arrivals']['total']}")
    print(f"   Retardés: {stats['summary']['total_delayed']}")
    print(f"   Annulés: {stats['summary']['total_cancelled']}")
    if stats['summary']['on_time_rate']:
        print(f"   Ponctualité: {stats['summary']['on_time_rate']}%")
    print()
    
    # 3. Afficher quelques vols
    if stats['departures']['flights']:
        print("   Exemples de départs:")
        for flight in stats['departures']['flights'][:3]:
            delay = f" (+{flight['delay_minutes']}min)" if flight.get('delay_minutes') and flight['delay_minutes'] > 0 else ""
            print(f"   ✈️  {flight['flight_number']} → {flight['destination']} | {flight['status']}{delay}")
    
    print()
    print("=" * 50)
    print("3. Test avec Beauvais (LFOB)...")
    stats_bva = get_delay_statistics("LFOB", hours=24)
    print(f"   Vols trouvés: {stats_bva['summary']['total_flights']}")
    if stats_bva['summary']['total_flights'] == 0:
        print("   ℹ️  Normal - Beauvais a peu de vols (surtout Ryanair/Wizz)")
    print("=" * 50)