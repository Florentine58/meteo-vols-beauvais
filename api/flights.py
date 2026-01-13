"""
Module pour récupérer les données de vols à Paris-Beauvais (BVA) via Flightradar24.

Note : Flightradar24 n'a pas d'API publique officielle gratuite.
Ce module utilise des méthodes alternatives (scraping ou API non-officielle).

Documentation utile : https://www.flightradar24.com/
"""

import requests
from datetime import datetime

# Coordonnées de l'aéroport Paris-Beauvais (BVA)
BVA_LAT = 49.4544
BVA_LON = 2.1106

# Code IATA de l'aéroport
AIRPORT_CODE = "BVA"

# Zone de recherche autour de l'aéroport (en degrés)
# Environ 50km de rayon
SEARCH_RADIUS = 0.5


def get_flights_in_area():
    """
    Récupère les vols dans la zone de Beauvais.
    
    Note : Cette fonction est un placeholder. 
    L'implémentation réelle dépendra de la méthode choisie :
    - FlightRadar24 API (payante)
    - Scraping (fragile)
    - OpenSky Network (alternative gratuite)
    
    Returns:
        list: Liste des vols ou liste vide si erreur
    """
    # TODO: Implémenter la récupération réelle des données
    
    # Pour l'instant, on retourne des données de démonstration
    demo_flights = [
        {
            "flight_id": "FR1234",
            "airline": "Ryanair",
            "origin": "Porto (OPO)",
            "destination": "Beauvais (BVA)",
            "aircraft": "Boeing 737-800",
            "altitude": 3000,  # pieds
            "speed": 250,  # noeuds
            "status": "En approche"
        },
        {
            "flight_id": "W64567",
            "airline": "Wizz Air",
            "origin": "Beauvais (BVA)",
            "destination": "Budapest (BUD)",
            "aircraft": "Airbus A320",
            "altitude": 0,
            "speed": 0,
            "status": "Au sol"
        }
    ]
    
    return demo_flights


def get_airport_info():
    """
    Retourne les informations de l'aéroport Paris-Beauvais.
    
    Returns:
        dict: Informations de l'aéroport
    """
    return {
        "name": "Paris-Beauvais-Tillé",
        "code_iata": "BVA",
        "code_icao": "LFOB",
        "latitude": BVA_LAT,
        "longitude": BVA_LON,
        "altitude": 109,  # mètres
        "timezone": "Europe/Paris",
        "principales_compagnies": ["Ryanair", "Wizz Air"]
    }


# Code pour tester le module directement
if __name__ == "__main__":
    print("=== Test du module vols ===")
    print()
    
    # Infos aéroport
    info = get_airport_info()
    print(f"Aéroport : {info['name']} ({info['code_iata']})")
    print(f"Position : {info['latitude']}, {info['longitude']}")
    print()
    
    # Vols (démo)
    flights = get_flights_in_area()
    print(f"Vols trouvés : {len(flights)}")
    for flight in flights:
        print(f"  - {flight['flight_id']} ({flight['airline']}) : {flight['status']}")