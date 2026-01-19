"""
Module pour récupérer les données de vols via AeroDataBox API.

Offre des données de retards, statuts de vols, et informations aéroport.
Documentation : https://rapidapi.com/aedbx-aedbx/api/aerodatabox

Plan gratuit : 600 appels/mois
"""

import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Clé API AeroDataBox (depuis .env)
AERODATABOX_API_KEY = os.getenv("AERODATABOX_API_KEY")

# Configuration API
BASE_URL = "https://aerodatabox.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": AERODATABOX_API_KEY,
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
}

# Code ICAO de Paris-Beauvais
AIRPORT_ICAO = "LFOB"


def test_connection():
    """
    Teste la connexion à l'API AeroDataBox.
    
    Returns:
        dict: Statut de la connexion
    """
    if not AERODATABOX_API_KEY:
        return {
            "status": "error",
            "message": "Clé API non configurée. Ajoutez AERODATABOX_API_KEY dans .env"
        }
    
    try:
        url = f"{BASE_URL}/health/services/feeds/FlightSchedules"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "Connexion AeroDataBox OK !"
            }
        elif response.status_code == 403:
            return {
                "status": "error", 
                "message": "Clé API invalide ou quota dépassé"
            }
        else:
            return {
                "status": "warning",
                "message": f"Code HTTP {response.status_code}"
            }
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Erreur réseau: {e}"
        }


def get_airport_delays(airport_icao=AIRPORT_ICAO):
    """
    Récupère les statistiques de retards actuels pour un aéroport.
    
    Args:
        airport_icao (str): Code ICAO de l'aéroport (LFOB pour Beauvais)
    
    Returns:
        dict: Statistiques de retards ou None si erreur
    """
    if not AERODATABOX_API_KEY:
        print("Erreur: AERODATABOX_API_KEY non configurée")
        return None
    
    url = f"{BASE_URL}/airports/icao/{airport_icao}/delays"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "airport": airport_icao,
                "timestamp": datetime.now().isoformat(),
                "departures": {
                    "delay_index": data.get("departures", {}).get("delayIndex"),
                    "median_delay_minutes": data.get("departures", {}).get("medianDelayMinutes"),
                    "cancelled": data.get("departures", {}).get("cancelled", 0)
                },
                "arrivals": {
                    "delay_index": data.get("arrivals", {}).get("delayIndex"),
                    "median_delay_minutes": data.get("arrivals", {}).get("medianDelayMinutes"),
                    "cancelled": data.get("arrivals", {}).get("cancelled", 0)
                },
                "raw": data
            }
        elif response.status_code == 404:
            print(f"Pas de données de retards pour {airport_icao}")
            return None
        elif response.status_code == 403:
            print("Erreur 403: Vérifiez votre clé API ou quota")
            return None
        else:
            print(f"Erreur AeroDataBox: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"Erreur réseau AeroDataBox: {e}")
        return None


def get_airport_departures(airport_icao=AIRPORT_ICAO, hours_from_now=12):
    """
    Récupère les départs prévus d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO de l'aéroport
        hours_from_now (int): Nombre d'heures à partir de maintenant
    
    Returns:
        list: Liste des départs ou liste vide si erreur
    """
    if not AERODATABOX_API_KEY:
        print("Erreur: AERODATABOX_API_KEY non configurée")
        return []
    
    # Calculer la période
    now = datetime.utcnow()
    from_time = now.strftime("%Y-%m-%dT%H:%M")
    to_time = (now + timedelta(hours=hours_from_now)).strftime("%Y-%m-%dT%H:%M")
    
    url = f"{BASE_URL}/flights/airports/icao/{airport_icao}/{from_time}/{to_time}"
    
    params = {
        "direction": "Departure",
        "withCancelled": "true",
        "withCodeshared": "false",
        "withLocation": "false"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            departures = data.get("departures", [])
            
            formatted = []
            for flight in departures:
                departure_info = flight.get("departure", {})
                arrival_info = flight.get("arrival", {})
                
                # Calculer le retard
                scheduled = departure_info.get("scheduledTimeLocal")
                actual = departure_info.get("actualTimeLocal") or departure_info.get("estimatedTimeLocal")
                
                delay_minutes = None
                if scheduled and actual:
                    try:
                        sched_dt = datetime.fromisoformat(scheduled.replace("+", "").split("+")[0])
                        actual_dt = datetime.fromisoformat(actual.replace("+", "").split("+")[0])
                        delay_minutes = int((actual_dt - sched_dt).total_seconds() / 60)
                    except:
                        pass
                
                formatted.append({
                    "flight_number": flight.get("number", "N/A"),
                    "airline": flight.get("airline", {}).get("name", "N/A"),
                    "destination": arrival_info.get("airport", {}).get("iata", "N/A"),
                    "destination_name": arrival_info.get("airport", {}).get("name", "N/A"),
                    "scheduled": scheduled,
                    "actual": actual,
                    "delay_minutes": delay_minutes,
                    "status": flight.get("status", "N/A"),
                    "aircraft": flight.get("aircraft", {}).get("model", "N/A")
                })
            
            return formatted
        else:
            print(f"Erreur AeroDataBox départs: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"Erreur réseau: {e}")
        return []


def get_airport_arrivals(airport_icao=AIRPORT_ICAO, hours_from_now=12):
    """
    Récupère les arrivées prévues d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO de l'aéroport
        hours_from_now (int): Nombre d'heures à partir de maintenant
    
    Returns:
        list: Liste des arrivées ou liste vide si erreur
    """
    if not AERODATABOX_API_KEY:
        return []
    
    now = datetime.utcnow()
    from_time = now.strftime("%Y-%m-%dT%H:%M")
    to_time = (now + timedelta(hours=hours_from_now)).strftime("%Y-%m-%dT%H:%M")
    
    url = f"{BASE_URL}/flights/airports/icao/{airport_icao}/{from_time}/{to_time}"
    
    params = {
        "direction": "Arrival",
        "withCancelled": "true",
        "withCodeshared": "false"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            arrivals = data.get("arrivals", [])
            
            formatted = []
            for flight in arrivals:
                departure_info = flight.get("departure", {})
                arrival_info = flight.get("arrival", {})
                
                scheduled = arrival_info.get("scheduledTimeLocal")
                actual = arrival_info.get("actualTimeLocal") or arrival_info.get("estimatedTimeLocal")
                
                delay_minutes = None
                if scheduled and actual:
                    try:
                        sched_dt = datetime.fromisoformat(scheduled.split("+")[0])
                        actual_dt = datetime.fromisoformat(actual.split("+")[0])
                        delay_minutes = int((actual_dt - sched_dt).total_seconds() / 60)
                    except:
                        pass
                
                formatted.append({
                    "flight_number": flight.get("number", "N/A"),
                    "airline": flight.get("airline", {}).get("name", "N/A"),
                    "origin": departure_info.get("airport", {}).get("iata", "N/A"),
                    "origin_name": departure_info.get("airport", {}).get("name", "N/A"),
                    "scheduled": scheduled,
                    "actual": actual,
                    "delay_minutes": delay_minutes,
                    "status": flight.get("status", "N/A"),
                    "aircraft": flight.get("aircraft", {}).get("model", "N/A")
                })
            
            return formatted
        else:
            return []
            
    except requests.RequestException as e:
        print(f"Erreur réseau: {e}")
        return []


def get_flight_status(flight_number, date=None):
    """
    Récupère le statut d'un vol spécifique.
    
    Args:
        flight_number (str): Numéro de vol (ex: "FR1234")
        date (str): Date au format YYYY-MM-DD (défaut: aujourd'hui)
    
    Returns:
        dict: Informations sur le vol ou None si erreur
    """
    if not AERODATABOX_API_KEY:
        return None
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/flights/number/{flight_number}/{date}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                flight = data[0]
                return {
                    "flight_number": flight.get("number"),
                    "airline": flight.get("airline", {}).get("name"),
                    "status": flight.get("status"),
                    "departure": {
                        "airport": flight.get("departure", {}).get("airport", {}).get("iata"),
                        "scheduled": flight.get("departure", {}).get("scheduledTimeLocal"),
                        "actual": flight.get("departure", {}).get("actualTimeLocal")
                    },
                    "arrival": {
                        "airport": flight.get("arrival", {}).get("airport", {}).get("iata"),
                        "scheduled": flight.get("arrival", {}).get("scheduledTimeLocal"),
                        "actual": flight.get("arrival", {}).get("actualTimeLocal")
                    },
                    "aircraft": flight.get("aircraft", {}).get("model")
                }
            return None
        else:
            return None
            
    except requests.RequestException as e:
        print(f"Erreur: {e}")
        return None


def get_delay_statistics(airport_icao=AIRPORT_ICAO):
    """
    Compile des statistiques de retards à partir des vols actuels.
    
    Returns:
        dict: Statistiques compilées
    """
    departures = get_airport_departures(airport_icao, hours_from_now=6)
    arrivals = get_airport_arrivals(airport_icao, hours_from_now=6)
    
    all_delays_dep = [f['delay_minutes'] for f in departures if f['delay_minutes'] is not None]
    all_delays_arr = [f['delay_minutes'] for f in arrivals if f['delay_minutes'] is not None]
    
    cancelled_dep = len([f for f in departures if 'cancel' in str(f.get('status', '')).lower()])
    cancelled_arr = len([f for f in arrivals if 'cancel' in str(f.get('status', '')).lower()])
    
    delayed_dep = len([d for d in all_delays_dep if d > 15])
    delayed_arr = len([d for d in all_delays_arr if d > 15])
    
    return {
        "timestamp": datetime.now().isoformat(),
        "airport": airport_icao,
        "departures": {
            "total": len(departures),
            "delayed": delayed_dep,
            "cancelled": cancelled_dep,
            "avg_delay": sum(all_delays_dep) / len(all_delays_dep) if all_delays_dep else 0,
            "max_delay": max(all_delays_dep) if all_delays_dep else 0
        },
        "arrivals": {
            "total": len(arrivals),
            "delayed": delayed_arr,
            "cancelled": cancelled_arr,
            "avg_delay": sum(all_delays_arr) / len(all_delays_arr) if all_delays_arr else 0,
            "max_delay": max(all_delays_arr) if all_delays_arr else 0
        },
        "summary": {
            "total_flights": len(departures) + len(arrivals),
            "total_delayed": delayed_dep + delayed_arr,
            "total_cancelled": cancelled_dep + cancelled_arr,
            "on_time_percentage": round(
                (1 - (delayed_dep + delayed_arr) / max(len(departures) + len(arrivals), 1)) * 100, 1
            )
        }
    }


def get_airport_info(airport_icao=AIRPORT_ICAO):
    """
    Récupère les informations détaillées d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO de l'aéroport
    
    Returns:
        dict: Informations de l'aéroport ou None
    """
    if not AERODATABOX_API_KEY:
        return None
    
    url = f"{BASE_URL}/airports/icao/{airport_icao}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "icao": data.get("icao"),
                "iata": data.get("iata"),
                "name": data.get("fullName") or data.get("name"),
                "city": data.get("municipalityName"),
                "country": data.get("countryCode"),
                "latitude": data.get("location", {}).get("lat"),
                "longitude": data.get("location", {}).get("lon"),
                "elevation_m": data.get("elevation", {}).get("m"),
                "timezone": data.get("timeZone")
            }
        return None
    except:
        return None


# Test du module
if __name__ == "__main__":
    print("=== Test du module AeroDataBox ===\n")
    
    # Test connexion
    print("1. Test de connexion...")
    result = test_connection()
    print(f"   {result['status'].upper()}: {result['message']}\n")
    
    if result['status'] == 'success':
        # Test infos aéroport
        print("2. Informations aéroport LFOB...")
        info = get_airport_info()
        if info:
            print(f"   {info['name']} ({info['iata']})")
            print(f"   {info['city']}, {info['country']}\n")
        
        # Test statistiques
        print("3. Statistiques de retards...")
        stats = get_delay_statistics()
        if stats:
            print(f"   Vols total: {stats['summary']['total_flights']}")
            print(f"   Retardés: {stats['summary']['total_delayed']}")
            print(f"   Ponctualité: {stats['summary']['on_time_percentage']}%")