"""
Module pour récupérer les données de vols à Paris-Beauvais (BVA) via FlightRadar24.

Utilise la librairie non-officielle FlightRadarAPI (usage éducatif uniquement).
Source : https://github.com/JeanExtreme002/FlightRadarAPI
"""

from FlightRadar24 import FlightRadar24API
from datetime import datetime

# Initialiser l'API
fr_api = FlightRadar24API()

# Coordonnées de l'aéroport Beauvais (BVA)
BVA_LAT = 49.4544
BVA_LON = 2.1106

# Code ICAO de l'aéroport
AIRPORT_ICAO = "LFOB"
AIRPORT_IATA = "BVA"

# Rayon de recherche autour de l'aéroport (en mètres)
SEARCH_RADIUS = 50000  # 50 km


def get_flights_in_area(radius=SEARCH_RADIUS):
    """
    Récupère les vols dans un rayon autour de l'aéroport de Beauvais.
    
    Args:
        radius (int): Rayon de recherche en mètres (défaut: 50000)
    
    Returns:
        list: Liste des vols avec leurs informations
    """
    try:
        # Définir la zone de recherche autour de Beauvais
        bounds = fr_api.get_bounds_by_point(BVA_LAT, BVA_LON, radius)
        
        # Récupérer les vols dans cette zone
        flights = fr_api.get_flights(bounds=bounds)
        
        # Formater les données
        flights_data = []
        for flight in flights:
            flight_info = {
                "id": flight.id,
                "callsign": flight.callsign or "N/A",
                "registration": flight.registration or "N/A",
                "aircraft_type": flight.aircraft_code or "N/A",
                "latitude": flight.latitude,
                "longitude": flight.longitude,
                "altitude": flight.altitude,  # en pieds
                "ground_speed": flight.ground_speed,  # en noeuds
                "heading": flight.heading,
                "vertical_speed": flight.vertical_speed,
                "airline_icao": flight.airline_icao or "N/A",
                "origin": flight.origin_airport_iata or "N/A",
                "destination": flight.destination_airport_iata or "N/A",
                "on_ground": flight.on_ground
            }
            flights_data.append(flight_info)
        
        return flights_data
    
    except Exception as e:
        print(f"Erreur lors de la récupération des vols : {e}")
        return []


def get_airport_info():
    """
    Retourne les informations de base de l'aéroport Paris-Beauvais.
    
    Returns:
        dict: Informations de l'aéroport
    """
    return {
        "name": "Paris-Beauvais-Tillé",
        "code_iata": AIRPORT_IATA,
        "code_icao": AIRPORT_ICAO,
        "latitude": BVA_LAT,
        "longitude": BVA_LON,
        "altitude": 109,  # mètres
        "timezone": "Europe/Paris",
        "city": "Beauvais",
        "country": "France",
        "principales_compagnies": ["Ryanair", "Wizz Air"]
    }


def get_arrivals(limit=20):
    """
    Récupère les arrivées à l'aéroport de Beauvais.
    
    Args:
        limit (int): Nombre maximum de vols à retourner
    
    Returns:
        list: Liste des vols en arrivée
    """
    try:
        airport = fr_api.get_airport(AIRPORT_ICAO)
        details = fr_api.get_airport_details(airport, flight_limit=limit)
        
        arrivals_data = details.get('airport', {}).get('pluginData', {}).get('schedule', {}).get('arrivals', {}).get('data', [])
        
        arrivals_formatted = []
        for arrival in arrivals_data:
            flight = arrival.get('flight', {})
            arrivals_formatted.append({
                "flight_number": flight.get('identification', {}).get('number', {}).get('default', 'N/A'),
                "callsign": flight.get('identification', {}).get('callsign', 'N/A'),
                "origin": flight.get('airport', {}).get('origin', {}).get('code', {}).get('iata', 'N/A'),
                "origin_city": flight.get('airport', {}).get('origin', {}).get('position', {}).get('region', {}).get('city', 'N/A'),
                "airline": flight.get('airline', {}).get('name', 'N/A'),
                "aircraft": flight.get('aircraft', {}).get('model', {}).get('code', 'N/A'),
                "status": flight.get('status', {}).get('text', 'N/A'),
            })
        
        return arrivals_formatted
    
    except Exception as e:
        print(f"Erreur lors de la récupération des arrivées : {e}")
        return []


def get_departures(limit=20):
    """
    Récupère les départs de l'aéroport de Beauvais.
    
    Args:
        limit (int): Nombre maximum de vols à retourner
    
    Returns:
        list: Liste des vols au départ
    """
    try:
        airport = fr_api.get_airport(AIRPORT_ICAO)
        details = fr_api.get_airport_details(airport, flight_limit=limit)
        
        departures_data = details.get('airport', {}).get('pluginData', {}).get('schedule', {}).get('departures', {}).get('data', [])
        
        departures_formatted = []
        for departure in departures_data:
            flight = departure.get('flight', {})
            departures_formatted.append({
                "flight_number": flight.get('identification', {}).get('number', {}).get('default', 'N/A'),
                "callsign": flight.get('identification', {}).get('callsign', 'N/A'),
                "destination": flight.get('airport', {}).get('destination', {}).get('code', {}).get('iata', 'N/A'),
                "destination_city": flight.get('airport', {}).get('destination', {}).get('position', {}).get('region', {}).get('city', 'N/A'),
                "airline": flight.get('airline', {}).get('name', 'N/A'),
                "aircraft": flight.get('aircraft', {}).get('model', {}).get('code', 'N/A'),
                "status": flight.get('status', {}).get('text', 'N/A'),
            })
        
        return departures_formatted
    
    except Exception as e:
        print(f"Erreur lors de la récupération des départs : {e}")
        return []


def get_airlines_stats(flights):
    """
    Calcule les statistiques des compagnies aériennes.
    
    Args:
        flights (list): Liste des vols
    
    Returns:
        dict: Statistiques par compagnie
    """
    airlines_count = {}
    for flight in flights:
        airline = flight.get('airline_icao', 'Inconnu')
        if airline and airline != 'N/A':
            airlines_count[airline] = airlines_count.get(airline, 0) + 1
    
    return airlines_count


def get_aircraft_stats(flights):
    """
    Calcule les statistiques des types d'avions.
    
    Args:
        flights (list): Liste des vols
    
    Returns:
        dict: Statistiques par type d'avion
    """
    aircraft_count = {}
    for flight in flights:
        aircraft = flight.get('aircraft_type', 'Inconnu')
        if aircraft and aircraft != 'N/A':
            aircraft_count[aircraft] = aircraft_count.get(aircraft, 0) + 1
    
    return aircraft_count


# Code pour tester le module directement
if __name__ == "__main__":
    print("=== Test du module vols ===")
    print()
    
    # Infos aéroport
    info = get_airport_info()
    print(f"Aéroport : {info['name']} ({info['code_iata']})")
    print(f"Position : {info['latitude']}, {info['longitude']}")
    print()
    
    # Vols dans la zone
    print("Recherche des vols dans la zone (50 km)...")
    flights = get_flights_in_area()
    print(f"Vols trouvés : {len(flights)}")
    
    if flights:
        for flight in flights[:5]:
            print(f"  - {flight['callsign']} | {flight['origin']} → {flight['destination']} | Alt: {flight['altitude']}ft")
    else:
        print("  Aucun vol détecté dans la zone actuellement.")
