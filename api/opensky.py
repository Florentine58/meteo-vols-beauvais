"""
Module pour récupérer les données de vols via OpenSky Network.

API gratuite avec authentification OAuth2.
Documentation : https://openskynetwork.github.io/opensky-api/
"""

import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Credentials OpenSky (depuis .env)
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

# Coordonnées de l'aéroport Paris-Beauvais (BVA)
BVA_LAT = 49.4544
BVA_LON = 2.1106
AIRPORT_ICAO = "LFOB"

# Zone de recherche (bounding box autour de Beauvais ~50km)
BBOX = {
    "lamin": BVA_LAT - 0.5,
    "lamax": BVA_LAT + 0.5,
    "lomin": BVA_LON - 0.7,
    "lomax": BVA_LON + 0.7
}

# URL de l'API OpenSky
BASE_URL = "https://opensky-network.org/api"


def get_auth():
    """
    Retourne les credentials pour l'authentification HTTP Basic.
    OpenSky utilise le client_id comme username et client_secret comme password.
    """
    if OPENSKY_CLIENT_ID and OPENSKY_CLIENT_SECRET:
        return (OPENSKY_CLIENT_ID.replace("-api-client", ""), OPENSKY_CLIENT_SECRET)
    return None


def get_flights_by_airport(airport_icao="LFOB", begin=None, end=None, arrival=True):
    """
    Récupère les vols arrivant ou partant d'un aéroport sur une période donnée.
    
    Args:
        airport_icao (str): Code ICAO de l'aéroport (LFOB pour Beauvais)
        begin (datetime): Date de début (défaut: il y a 7 jours)
        end (datetime): Date de fin (défaut: maintenant)
        arrival (bool): True pour les arrivées, False pour les départs
    
    Returns:
        list: Liste des vols avec leurs informations
    """
    if end is None:
        end = datetime.now()
    if begin is None:
        begin = end - timedelta(days=7)
    
    # OpenSky limite à 7 jours max par requête
    if (end - begin).days > 7:
        print("Attention: OpenSky limite à 7 jours par requête. Réduction automatique.")
        begin = end - timedelta(days=7)
    
    # Convertir en timestamp Unix
    begin_ts = int(begin.timestamp())
    end_ts = int(end.timestamp())
    
    # Endpoint selon arrivées ou départs
    endpoint_type = "arrival" if arrival else "departure"
    url = f"{BASE_URL}/flights/{endpoint_type}"
    
    params = {
        "airport": airport_icao,
        "begin": begin_ts,
        "end": end_ts
    }
    
    try:
        auth = get_auth()
        response = requests.get(url, params=params, auth=auth, timeout=30)
        
        if response.status_code == 200:
            flights = response.json()
            
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
        elif response.status_code == 401:
            print("Erreur d'authentification OpenSky. Vérifiez vos credentials.")
            return []
        elif response.status_code == 403:
            print("Accès refusé. Vérifiez que votre compte OpenSky est activé.")
            return []
        else:
            print(f"Erreur API OpenSky: {response.status_code} - {response.text}")
            return []
            
    except requests.RequestException as e:
        print(f"Erreur réseau OpenSky: {e}")
        return []


def get_historical_flights(days=7):
    """
    Récupère l'historique des vols (arrivées + départs) pour Beauvais.
    
    Args:
        days (int): Nombre de jours d'historique (max 7 par requête)
    
    Returns:
        dict: Dictionnaire avec 'arrivals', 'departures', 'total', 'by_day'
    """
    end = datetime.now()
    begin = end - timedelta(days=min(days, 7))
    
    print(f"Récupération des vols du {begin.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}...")
    
    arrivals = get_flights_by_airport(AIRPORT_ICAO, begin, end, arrival=True)
    departures = get_flights_by_airport(AIRPORT_ICAO, begin, end, arrival=False)
    
    # Regrouper par jour
    by_day = {}
    
    for flight in arrivals:
        day = flight['arrival_time'].strftime("%Y-%m-%d")
        if day not in by_day:
            by_day[day] = {"arrivals": 0, "departures": 0}
        by_day[day]["arrivals"] += 1
    
    for flight in departures:
        day = flight['departure_time'].strftime("%Y-%m-%d")
        if day not in by_day:
            by_day[day] = {"arrivals": 0, "departures": 0}
        by_day[day]["departures"] += 1
    
    return {
        "arrivals": arrivals,
        "departures": departures,
        "total": len(arrivals) + len(departures),
        "by_day": by_day,
        "period": {
            "begin": begin.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d")
        }
    }


def get_extended_historical_flights(weeks=4):
    """
    Récupère l'historique sur plusieurs semaines en faisant plusieurs requêtes.
    
    Args:
        weeks (int): Nombre de semaines d'historique
    
    Returns:
        dict: Données agrégées sur toute la période
    """
    all_arrivals = []
    all_departures = []
    all_by_day = {}
    
    end = datetime.now()
    
    for week in range(weeks):
        week_end = end - timedelta(weeks=week)
        week_begin = week_end - timedelta(days=7)
        
        print(f"Semaine {week + 1}/{weeks}: {week_begin.strftime('%d/%m')} - {week_end.strftime('%d/%m')}")
        
        arrivals = get_flights_by_airport(AIRPORT_ICAO, week_begin, week_end, arrival=True)
        departures = get_flights_by_airport(AIRPORT_ICAO, week_begin, week_end, arrival=False)
        
        all_arrivals.extend(arrivals)
        all_departures.extend(departures)
        
        # Agréger par jour
        for flight in arrivals:
            day = flight['arrival_time'].strftime("%Y-%m-%d")
            if day not in all_by_day:
                all_by_day[day] = {"arrivals": 0, "departures": 0}
            all_by_day[day]["arrivals"] += 1
        
        for flight in departures:
            day = flight['departure_time'].strftime("%Y-%m-%d")
            if day not in all_by_day:
                all_by_day[day] = {"arrivals": 0, "departures": 0}
            all_by_day[day]["departures"] += 1
    
    return {
        "arrivals": all_arrivals,
        "departures": all_departures,
        "total": len(all_arrivals) + len(all_departures),
        "by_day": all_by_day,
        "weeks": weeks
    }


def get_current_flights_in_area():
    """
    Récupère les avions actuellement dans la zone de Beauvais.
    
    Returns:
        list: Liste des avions avec leurs positions
    """
    url = f"{BASE_URL}/states/all"
    params = {
        "lamin": BBOX["lamin"],
        "lamax": BBOX["lamax"],
        "lomin": BBOX["lomin"],
        "lomax": BBOX["lomax"]
    }
    
    try:
        auth = get_auth()
        response = requests.get(url, params=params, auth=auth, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            
            flights = []
            for state in states:
                if len(state) >= 12:
                    flights.append({
                        "icao24": state[0],
                        "callsign": (state[1] or "N/A").strip(),
                        "origin_country": state[2],
                        "longitude": state[5],
                        "latitude": state[6],
                        "altitude": state[7] if state[7] else 0,
                        "on_ground": state[8],
                        "velocity": state[9] if state[9] else 0,
                        "heading": state[10] if state[10] else 0,
                        "vertical_rate": state[11] if state[11] else 0
                    })
            
            return flights
        else:
            print(f"Erreur API OpenSky: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"Erreur réseau: {e}")
        return []


def get_daily_flight_stats(days=7):
    """
    Retourne les statistiques de vols par jour.
    
    Args:
        days (int): Nombre de jours
    
    Returns:
        list: Liste de dicts avec date, arrivals, departures, total
    """
    data = get_historical_flights(days=days)
    
    stats = []
    for date_str, counts in sorted(data['by_day'].items()):
        stats.append({
            "date": date_str,
            "date_formatted": datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m"),
            "arrivals": counts["arrivals"],
            "departures": counts["departures"],
            "total": counts["arrivals"] + counts["departures"]
        })
    
    return stats


def test_connection():
    """
    Teste la connexion à l'API OpenSky.
    
    Returns:
        dict: Statut de la connexion
    """
    auth = get_auth()
    
    if not auth:
        return {
            "status": "error",
            "message": "Credentials non configurés. Vérifiez votre fichier .env"
        }
    
    try:
        # Test simple : récupérer les vols actuels
        response = requests.get(
            f"{BASE_URL}/states/all",
            params={"lamin": 49, "lamax": 50, "lomin": 2, "lomax": 3},
            auth=auth,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "Connexion OpenSky OK !",
                "authenticated": True
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "message": "Authentification échouée. Vérifiez vos credentials."
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


# Test du module
if __name__ == "__main__":
    print("=== Test du module OpenSky ===\n")
    
    # Test connexion
    print("1. Test de connexion...")
    result = test_connection()
    print(f"   {result['status'].upper()}: {result['message']}\n")
    
    if result['status'] == 'success':
        # Test historique
        print("2. Récupération de l'historique (7 jours)...")
        data = get_historical_flights(days=7)
        print(f"   Arrivées: {len(data['arrivals'])}")
        print(f"   Départs: {len(data['departures'])}")
        print(f"   Total: {data['total']}\n")
        
        # Stats par jour
        print("3. Statistiques par jour:")
        for day, counts in sorted(data['by_day'].items()):
            print(f"   {day}: {counts['arrivals']} arr. / {counts['departures']} dep.")