"""
Module OpenSky Network AMÉLIORÉ avec support OAuth2 et trajectoires.

Fonctionnalités :
- Authentification OAuth2 (nouveau système OpenSky)
- Récupération des vraies trajectoires (waypoints)
- Vols temps réel
- Historique des vols

Documentation : https://openskynetwork.github.io/opensky-api/rest.html
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

# Coordonnées Beauvais
BVA_LAT = 49.4544
BVA_LON = 2.1106
AIRPORT_ICAO = "LFOB"

# Zone de recherche (bounding box ~50km)
BBOX = {
    "lamin": BVA_LAT - 0.5,
    "lamax": BVA_LAT + 0.5,
    "lomin": BVA_LON - 0.7,
    "lomax": BVA_LON + 0.7
}

# URLs API
BASE_URL = "https://opensky-network.org/api"
AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

# Cache pour le token
_token_cache = {
    "token": None,
    "expires": None
}


def get_oauth_token():
    """
    Obtient un token OAuth2 pour l'API OpenSky.
    Le token est mis en cache pendant 25 minutes (expire après 30).
    
    Returns:
        str: Token d'accès ou None si erreur
    """
    global _token_cache
    
    # Vérifier si on a un token valide en cache
    if _token_cache["token"] and _token_cache["expires"]:
        if datetime.now() < _token_cache["expires"]:
            return _token_cache["token"]
    
    # Vérifier les credentials
    if not OPENSKY_CLIENT_ID or not OPENSKY_CLIENT_SECRET:
        print("⚠️  Credentials OpenSky non configurés")
        print("   Ajoute dans .env:")
        print("   OPENSKY_CLIENT_ID=ton_client_id")
        print("   OPENSKY_CLIENT_SECRET=ton_client_secret")
        return None
    
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": OPENSKY_CLIENT_ID,
            "client_secret": OPENSKY_CLIENT_SECRET
        }
        
        response = requests.post(AUTH_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            _token_cache["token"] = token_data["access_token"]
            _token_cache["expires"] = datetime.now() + timedelta(minutes=25)
            return _token_cache["token"]
        else:
            print(f"❌ Erreur OAuth2: {response.status_code}")
            print(f"   {response.text[:200]}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Erreur réseau OAuth2: {e}")
        return None


def get_headers():
    """
    Retourne les headers avec le token Bearer.
    
    Returns:
        dict: Headers ou None si pas de token
    """
    token = get_oauth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return None


def get_current_flights_in_area(use_auth=True):
    """
    Récupère les avions actuellement dans la zone de Beauvais.
    
    Args:
        use_auth (bool): Utiliser l'authentification (meilleure résolution)
    
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
        headers = get_headers() if use_auth else None
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
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
                        "altitude": state[7] if state[7] else 0,  # mètres géométrique
                        "baro_altitude": state[13] if len(state) > 13 and state[13] else state[7],
                        "on_ground": state[8],
                        "velocity": state[9] if state[9] else 0,  # m/s
                        "heading": state[10] if state[10] else 0,
                        "vertical_rate": state[11] if state[11] else 0,
                        "category": state[16] if len(state) > 16 else None
                    })
            
            return flights
        else:
            print(f"⚠️  OpenSky states: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ Erreur OpenSky states: {e}")
        return []


def get_flight_track(icao24, time=0):
    """
    🌟 Récupère la VRAIE TRAJECTOIRE d'un avion (liste de waypoints).
    
    Args:
        icao24 (str): Adresse ICAO24 de l'avion (ex: "3c675a")
        time (int): Timestamp Unix. 0 = trajectoire en cours
    
    Returns:
        dict: Trajectoire avec waypoints ou None
        {
            "icao24": "3c675a",
            "callsign": "DLH123",
            "startTime": timestamp,
            "endTime": timestamp,
            "waypoints": [
                {"time": t, "lat": lat, "lon": lon, "altitude": alt, "heading": hdg},
                ...
            ]
        }
    """
    headers = get_headers()
    if not headers:
        return None
    
    url = f"{BASE_URL}/tracks/all"
    params = {
        "icao24": icao24.lower(),
        "time": time
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            waypoints = []
            for point in data.get("path", []):
                # point = [time, lat, lon, baro_altitude, true_track, on_ground]
                if len(point) >= 5:
                    waypoints.append({
                        "time": point[0],
                        "lat": point[1],
                        "lon": point[2],
                        "altitude": point[3],  # mètres
                        "heading": point[4],
                        "on_ground": point[5] if len(point) > 5 else False
                    })
            
            return {
                "icao24": data.get("icao24"),
                "callsign": data.get("callsign", "").strip(),
                "startTime": data.get("startTime"),
                "endTime": data.get("endTime"),
                "waypoints": waypoints
            }
            
        elif response.status_code == 404:
            # Pas de trajectoire disponible
            return None
        else:
            print(f"⚠️  OpenSky tracks: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Erreur OpenSky tracks: {e}")
        return None


def get_flights_in_zone_with_tracks(max_tracks=10):
    """
    Récupère les avions dans la zone AVEC leurs trajectoires.
    
    Args:
        max_tracks (int): Nombre max de trajectoires à récupérer
    
    Returns:
        list: Avions avec leurs waypoints
    """
    flights = get_current_flights_in_area()
    
    # Enrichir avec les trajectoires (limité pour économiser l'API)
    for i, flight in enumerate(flights):
        if i >= max_tracks:
            break
            
        track = get_flight_track(flight["icao24"])
        if track:
            flight["waypoints"] = track["waypoints"]
            flight["track_start"] = track["startTime"]
            flight["track_end"] = track["endTime"]
        else:
            flight["waypoints"] = []
    
    return flights


def get_flights_by_airport(airport_icao="LFOB", days=2, arrival=True):
    """
    Récupère les vols arrivant ou partant d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO (LFOB pour Beauvais)
        days (int): Nombre de jours d'historique (max 7)
        arrival (bool): True = arrivées, False = départs
    
    Returns:
        list: Liste des vols
    """
    headers = get_headers()
    if not headers:
        return []
    
    end = int(datetime.now().timestamp())
    begin = int((datetime.now() - timedelta(days=min(days, 7))).timestamp())
    
    endpoint = "arrival" if arrival else "departure"
    url = f"{BASE_URL}/flights/{endpoint}"
    params = {
        "airport": airport_icao,
        "begin": begin,
        "end": end
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            flights = response.json()
            
            formatted = []
            for flight in flights:
                formatted.append({
                    "icao24": flight.get("icao24", "N/A"),
                    "callsign": (flight.get("callsign") or "N/A").strip(),
                    "origin": flight.get("estDepartureAirport", "N/A"),
                    "destination": flight.get("estArrivalAirport", "N/A"),
                    "first_seen": datetime.fromtimestamp(flight.get("firstSeen", 0)),
                    "last_seen": datetime.fromtimestamp(flight.get("lastSeen", 0))
                })
            
            return formatted
            
        elif response.status_code == 404:
            return []  # Pas de vols trouvés
        else:
            print(f"⚠️  OpenSky flights: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ Erreur OpenSky flights: {e}")
        return []


def get_historical_flights(days=7):
    """
    Récupère l'historique des vols (arrivées + départs) pour Beauvais.
    
    Args:
        days (int): Nombre de jours d'historique (max 7)
    
    Returns:
        dict: Statistiques avec arrivées et départs
    """
    arrivals = get_flights_by_airport(AIRPORT_ICAO, days, arrival=True)
    departures = get_flights_by_airport(AIRPORT_ICAO, days, arrival=False)
    
    # Regrouper par jour
    by_day = {}
    
    for flight in arrivals:
        day = flight['last_seen'].strftime("%Y-%m-%d")
        if day not in by_day:
            by_day[day] = {"arrivals": 0, "departures": 0}
        by_day[day]["arrivals"] += 1
    
    for flight in departures:
        day = flight['first_seen'].strftime("%Y-%m-%d")
        if day not in by_day:
            by_day[day] = {"arrivals": 0, "departures": 0}
        by_day[day]["departures"] += 1
    
    return {
        "arrivals": arrivals,
        "departures": departures,
        "total": len(arrivals) + len(departures),
        "by_day": by_day
    }


def test_connection():
    """
    Teste la connexion à l'API OpenSky.
    
    Returns:
        dict: Statut de la connexion
    """
    # Test sans auth
    try:
        url = f"{BASE_URL}/states/all"
        params = {"lamin": 49, "lamax": 50, "lomin": 2, "lomax": 3}
        response = requests.get(url, params=params, timeout=10)
        
        no_auth_ok = response.status_code == 200
    except:
        no_auth_ok = False
    
    # Test avec auth
    auth_ok = False
    token = get_oauth_token()
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/states/all", params=params, headers=headers, timeout=10)
            auth_ok = response.status_code == 200
        except:
            pass
    
    return {
        "no_auth": no_auth_ok,
        "with_auth": auth_ok,
        "token_valid": token is not None,
        "can_get_tracks": auth_ok,  # Tracks nécessite auth
        "message": "✅ Connexion OK avec auth" if auth_ok else ("⚠️ Connexion OK sans auth" if no_auth_ok else "❌ Connexion échouée")
    }


# =============================================================================
# Utilitaires pour la carte
# =============================================================================

def estimate_flight_path(origin_coords, dest_coords, num_points=20):
    """
    Génère une trajectoire estimée (ligne géodésique simplifiée).
    Utile quand les vraies trajectoires ne sont pas disponibles.
    
    Args:
        origin_coords (tuple): (lat, lon) origine
        dest_coords (tuple): (lat, lon) destination
        num_points (int): Nombre de points intermédiaires
    
    Returns:
        list: Liste de (lat, lon)
    """
    lat1, lon1 = origin_coords
    lat2, lon2 = dest_coords
    
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        points.append((lat, lon))
    
    return points


# Coordonnées des aéroports majeurs (pour tracer les lignes)
AIRPORT_COORDS = {
    "LFOB": (49.4544, 2.1106),   # Beauvais
    "LFPG": (49.0097, 2.5479),   # Paris CDG
    "LFPO": (48.7262, 2.3597),   # Paris Orly
    "EGLL": (51.4700, -0.4543),  # Londres Heathrow
    "LEMD": (40.4719, -3.5626),  # Madrid
    "LIRF": (41.8003, 12.2389),  # Rome
    "LEBL": (41.2971, 2.0785),   # Barcelone
    "LPPT": (38.7813, -9.1359),  # Lisbonne
    "EIDW": (53.4213, -6.2701),  # Dublin
    "EHAM": (52.3086, 4.7639),   # Amsterdam
    "EDDF": (50.0379, 8.5622),   # Francfort
    "EDDM": (48.3538, 11.7861),  # Munich
    "LSZH": (47.4647, 8.5492),   # Zurich
    "LIMC": (45.6301, 8.7231),   # Milan Malpensa
    "LOWW": (48.1103, 16.5697),  # Vienne
    "EPWA": (52.1657, 20.9671),  # Varsovie
    "LKPR": (50.1008, 14.2600),  # Prague
    "LHBP": (47.4369, 19.2556),  # Budapest
    "LGAV": (37.9364, 23.9445),  # Athènes
}


def get_airport_coords(icao_code):
    """
    Retourne les coordonnées d'un aéroport.
    
    Args:
        icao_code (str): Code ICAO
    
    Returns:
        tuple: (lat, lon) ou None
    """
    return AIRPORT_COORDS.get(icao_code.upper())


# =============================================================================
# Test du module
# =============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("TEST MODULE OPENSKY AMÉLIORÉ")
    print("=" * 50)
    print()
    
    # Test connexion
    print("1. Test de connexion...")
    status = test_connection()
    print(f"   {status['message']}")
    print(f"   Token valide: {status['token_valid']}")
    print(f"   Peut récupérer tracks: {status['can_get_tracks']}")
    print()
    
    # Test vols dans la zone
    print("2. Vols dans la zone de Beauvais...")
    flights = get_current_flights_in_area()
    print(f"   Avions détectés: {len(flights)}")
    for f in flights[:5]:
        print(f"      - {f['callsign']:8} | Alt: {f['altitude']}m | {f['origin_country']}")
    print()
    
    # Test trajectoire (si auth disponible)
    if flights and status['can_get_tracks']:
        print("3. Test récupération trajectoire...")
        icao24 = flights[0]['icao24']
        track = get_flight_track(icao24)
        if track:
            print(f"   ✅ Trajectoire pour {track['callsign']}")
            print(f"   Waypoints: {len(track['waypoints'])}")
            if track['waypoints']:
                first = track['waypoints'][0]
                last = track['waypoints'][-1]
                print(f"   Début: ({first['lat']:.2f}, {first['lon']:.2f})")
                print(f"   Fin: ({last['lat']:.2f}, {last['lon']:.2f})")
        else:
            print(f"   Pas de trajectoire disponible pour {icao24}")
