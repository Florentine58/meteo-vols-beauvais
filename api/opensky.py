"""
Module pour récupérer les données historiques de vols via OpenSky Network.

API gratuite avec historique jusqu'à 30 jours.
Documentation : https://openskynetwork.github.io/opensky-api/
"""

import requests
from datetime import datetime, timedelta

# Coordonnées de l'aéroport Paris-Beauvais (BVA)
BVA_LAT = 49.4544
BVA_LON = 2.1106

# Zone de recherche (bounding box autour de Beauvais)
# Environ 50 km de rayon
BBOX = {
    "lamin": BVA_LAT - 0.5,  # latitude min
    "lamax": BVA_LAT + 0.5,  # latitude max
    "lomin": BVA_LON - 0.7,  # longitude min
    "lomax": BVA_LON + 0.7   # longitude max
}

# URL de l'API OpenSky
BASE_URL = "https://opensky-network.org/api"


def get_flights_by_airport(airport_icao="LFOB", begin=None, end=None, arrival=True):
    """
    Récupère les vols arrivant ou partant d'un aéroport sur une période donnée.
    
    Args:
        airport_icao (str): Code ICAO de l'aéroport (LFOB pour Beauvais)
        begin (datetime): Date de début (défaut: il y a 7 jours)
        end (datetime): Date de fin (défaut: maintenant)
        arrival (bool): True pour les arrivées, False pour les départs
    
    Returns:
        list: Liste des vols
    """
    if end is None:
        end = datetime.now()
    if begin is None:
        begin = end - timedelta(days=7)
    
    # Convertir en timestamp Unix
    begin_ts = int(begin.timestamp())
    end_ts = int(end.timestamp())
    
    # Endpoint selon arrivées ou départs
    if arrival:
        endpoint = f"{BASE_URL}/flights/arrival"
        params = {
            "airport": airport_icao,
            "begin": begin_ts,
            "end": end_ts
        }
    else:
        endpoint = f"{BASE_URL}/flights/departure"
        params = {
            "airport": airport_icao,
            "begin": begin_ts,
            "end": end_ts
        }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        
        if response.status_code == 200:
            flights = response.json()
            
            # Formater les données
            formatted_flights = []
            for flight in flights:
                formatted_flights.append({
                    "icao24": flight.get("icao24", "N/A"),
                    "callsign": (flight.get("callsign") or "N/A").strip(),
                    "origin": flight.get("estDepartureAirport", "N/A"),
                    "destination": flight.get("estArrivalAirport", "N/A"),
                    "first_seen": datetime.fromtimestamp(flight.get("firstSeen", 0)),
                    "last_seen": datetime.fromtimestamp(flight.get("lastSeen", 0)),
                    "departure_time": datetime.fromtimestamp(flight.get("firstSeen", 0)),
                    "arrival_time": datetime.fromtimestamp(flight.get("lastSeen", 0))
                })
            
            return formatted_flights
        
        elif response.status_code == 404:
            print(f"Aucun vol trouvé pour {airport_icao}")
            return []
        else:
            print(f"Erreur API OpenSky: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des vols historiques : {e}")
        return []


def get_historical_flights_in_area(begin=None, end=None):
    """
    Récupère tous les vols historiques (arrivées + départs) pour Beauvais.
    
    Args:
        begin (datetime): Date de début
        end (datetime): Date de fin
    
    Returns:
        dict: Dictionnaire avec 'arrivals' et 'departures'
    """
    arrivals = get_flights_by_airport("LFOB", begin, end, arrival=True)
    departures = get_flights_by_airport("LFOB", begin, end, arrival=False)
    
    return {
        "arrivals": arrivals,
        "departures": departures,
        "total": len(arrivals) + len(departures)
    }


def get_daily_flight_counts(days=7):
    """
    Récupère le nombre de vols par jour sur les X derniers jours.
    
    Args:
        days (int): Nombre de jours à analyser
    
    Returns:
        list: Liste de dictionnaires avec date et nombre de vols
    """
    daily_counts = []
    
    for i in range(days, 0, -1):
        day_end = datetime.now() - timedelta(days=i-1)
        day_start = datetime.now() - timedelta(days=i)
        
        # Définir les bornes de la journée
        day_start = day_start.replace(hour=0, minute=0, second=0)
        day_end = day_end.replace(hour=23, minute=59, second=59)
        
        flights = get_historical_flights_in_area(day_start, day_end)
        
        daily_counts.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "date_formatted": day_start.strftime("%d/%m"),
            "arrivals": len(flights["arrivals"]),
            "departures": len(flights["departures"]),
            "total": flights["total"]
        })
    
    return daily_counts


def get_hourly_distribution(days=7):
    """
    Analyse la distribution horaire des vols sur les X derniers jours.
    
    Args:
        days (int): Nombre de jours à analyser
    
    Returns:
        dict: Distribution par heure (0-23)
    """
    end = datetime.now()
    begin = end - timedelta(days=days)
    
    flights_data = get_historical_flights_in_area(begin, end)
    
    # Initialiser les compteurs par heure
    hourly_dist = {hour: 0 for hour in range(24)}
    
    # Compter les arrivées par heure
    for flight in flights_data["arrivals"]:
        hour = flight["arrival_time"].hour
        hourly_dist[hour] += 1
    
    # Compter les départs par heure
    for flight in flights_data["departures"]:
        hour = flight["departure_time"].hour
        hourly_dist[hour] += 1
    
    return hourly_dist


def get_current_states_in_area():
    """
    Récupère les avions actuellement dans la zone de Beauvais via OpenSky.
    Alternative gratuite à FlightRadar24.
    
    Returns:
        list: Liste des avions dans la zone
    """
    endpoint = f"{BASE_URL}/states/all"
    params = {
        "lamin": BBOX["lamin"],
        "lamax": BBOX["lamax"],
        "lomin": BBOX["lomin"],
        "lomax": BBOX["lomax"]
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            
            flights = []
            for state in states:
                flights.append({
                    "icao24": state[0],
                    "callsign": (state[1] or "N/A").strip(),
                    "origin_country": state[2],
                    "longitude": state[5],
                    "latitude": state[6],
                    "altitude": state[7],  # mètres (géométrique)
                    "on_ground": state[8],
                    "velocity": state[9],  # m/s
                    "heading": state[10],
                    "vertical_rate": state[11]
                })
            
            return flights
        else:
            print(f"Erreur API OpenSky: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des états : {e}")
        return []


# Code pour tester le module directement
if __name__ == "__main__":
    print("=== Test du module OpenSky ===")
    print()
    
    # Test des vols en temps réel
    print("Avions actuellement dans la zone de Beauvais...")
    current = get_current_states_in_area()
    print(f"Avions détectés : {len(current)}")
    for flight in current[:5]:
        print(f"  - {flight['callsign']} | Alt: {flight['altitude']}m | {flight['origin_country']}")
    
    print()
    
    # Test des vols historiques
    print("Vols des 7 derniers jours à Beauvais (LFOB)...")
    end = datetime.now()
    begin = end - timedelta(days=7)
    historical = get_historical_flights_in_area(begin, end)
    print(f"Arrivées : {len(historical['arrivals'])}")
    print(f"Départs : {len(historical['departures'])}")
    print(f"Total : {historical['total']}")