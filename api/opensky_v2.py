"""
Module OpenSky Network V2 — Trajectoires historiques pour Beauvais
Récupère les vraies trajectoires des vols pour analyse météo/aviation

Documentation : https://openskynetwork.github.io/opensky-api/rest.html
Gratuit avec compte : ~400 requêtes/jour
"""

import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()

# Credentials OpenSky
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

# Coordonnées Beauvais
BVA_LAT = 49.4544
BVA_LON = 2.1106
AIRPORT_ICAO = "LFOB"

# Zone de recherche (bounding box ~80km autour de Beauvais)
BBOX = {
    "lamin": BVA_LAT - 0.7,
    "lamax": BVA_LAT + 0.7,
    "lomin": BVA_LON - 1.0,
    "lomax": BVA_LON + 1.0
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
    """
    global _token_cache
    
    # Vérifier cache
    if _token_cache["token"] and _token_cache["expires"]:
        if datetime.now() < _token_cache["expires"]:
            return _token_cache["token"]
    
    if not OPENSKY_CLIENT_ID or not OPENSKY_CLIENT_SECRET:
        print("⚠️  Credentials OpenSky non configurés dans .env")
        return None
    
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": OPENSKY_CLIENT_ID,
            "client_secret": OPENSKY_CLIENT_SECRET
        }
        
        response = requests.post(AUTH_URL, data=data, timeout=15)
        
        if response.status_code == 200:
            token_data = response.json()
            _token_cache["token"] = token_data["access_token"]
            _token_cache["expires"] = datetime.now() + timedelta(minutes=25)
            return _token_cache["token"]
        else:
            print(f"❌ Erreur OAuth2: {response.status_code} - {response.text[:200]}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Erreur réseau OAuth2: {e}")
        return None


def get_headers():
    """Retourne les headers avec le token Bearer."""
    token = get_oauth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return None


def test_connection():
    """
    Teste la connexion à l'API OpenSky.
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
        "status": "success" if auth_ok else ("warning" if no_auth_ok else "error"),
        "no_auth": no_auth_ok,
        "with_auth": auth_ok,
        "token_valid": token is not None,
        "can_get_tracks": auth_ok,
        "message": "✅ Connexion OpenSky OK avec authentification" if auth_ok else ("⚠️ Connexion OK sans auth (limité)" if no_auth_ok else "❌ Connexion échouée")
    }


def get_current_flights_in_area():
    """
    Récupère les avions actuellement dans la zone de Beauvais.
    """
    url = f"{BASE_URL}/states/all"
    params = {
        "lamin": BBOX["lamin"],
        "lamax": BBOX["lamax"],
        "lomin": BBOX["lomin"],
        "lomax": BBOX["lomax"]
    }
    
    try:
        headers = get_headers()
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            
            flights = []
            for state in states:
                if len(state) >= 12 and state[5] and state[6]:  # Vérifier lat/lon
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
                        "vertical_rate": state[11] if state[11] else 0,
                    })
            
            return flights
        else:
            print(f"⚠️  OpenSky states: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ Erreur OpenSky: {e}")
        return []


def get_flight_track(icao24, timestamp=0):
    """
    🌟 Récupère la VRAIE TRAJECTOIRE d'un avion (liste de waypoints).
    
    Args:
        icao24 (str): Adresse ICAO24 de l'avion (ex: "3c675a")
        timestamp (int): Timestamp Unix. 0 = trajectoire en cours
    
    Returns:
        dict: Trajectoire avec waypoints ou None
    """
    headers = get_headers()
    if not headers:
        print("⚠️  Token requis pour récupérer les trajectoires")
        return None
    
    url = f"{BASE_URL}/tracks/all"
    params = {
        "icao24": icao24.lower(),
        "time": timestamp
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            waypoints = []
            for point in data.get("path", []):
                # point = [time, lat, lon, baro_altitude, true_track, on_ground]
                if len(point) >= 5 and point[1] and point[2]:
                    waypoints.append({
                        "time": point[0],
                        "lat": point[1],
                        "lon": point[2],
                        "altitude": point[3] if point[3] else 0,
                        "heading": point[4] if point[4] else 0,
                        "on_ground": point[5] if len(point) > 5 else False
                    })
            
            if waypoints:
                return {
                    "icao24": data.get("icao24"),
                    "callsign": (data.get("callsign") or "").strip(),
                    "startTime": data.get("startTime"),
                    "endTime": data.get("endTime"),
                    "waypoints": waypoints
                }
            return None
            
        elif response.status_code == 404:
            return None  # Pas de trajectoire disponible
        else:
            print(f"⚠️  OpenSky tracks: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Erreur trajectoire: {e}")
        return None


def get_flights_by_airport(airport_icao="LFOB", hours=24, arrival=True):
    """
    Récupère les vols arrivant ou partant d'un aéroport.
    
    Args:
        airport_icao (str): Code ICAO (LFOB pour Beauvais)
        hours (int): Nombre d'heures d'historique (max 168 = 7 jours)
        arrival (bool): True = arrivées, False = départs
    
    Returns:
        list: Liste des vols
    """
    headers = get_headers()
    if not headers:
        print("⚠️  Token requis pour l'historique des vols")
        return []
    
    end = int(datetime.now(timezone.utc).timestamp())
    begin = int((datetime.now(timezone.utc) - timedelta(hours=min(hours, 168))).timestamp())
    
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
                first_seen = flight.get("firstSeen", 0)
                last_seen = flight.get("lastSeen", 0)
                
                formatted.append({
                    "icao24": flight.get("icao24", "N/A"),
                    "callsign": (flight.get("callsign") or "N/A").strip(),
                    "origin": flight.get("estDepartureAirport") or "N/A",
                    "destination": flight.get("estArrivalAirport") or "N/A",
                    "first_seen": datetime.fromtimestamp(first_seen, tz=timezone.utc) if first_seen else None,
                    "last_seen": datetime.fromtimestamp(last_seen, tz=timezone.utc) if last_seen else None,
                    "first_seen_ts": first_seen,
                    "last_seen_ts": last_seen,
                    "is_arrival": arrival
                })
            
            return formatted
            
        elif response.status_code == 404:
            return []
        else:
            print(f"⚠️  OpenSky flights/{endpoint}: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ Erreur vols aéroport: {e}")
        return []


def get_beauvais_flights_with_tracks(hours=24, max_tracks=20):
    """
    🎯 Fonction principale : Récupère les vols BVA avec leurs trajectoires réelles.
    
    Args:
        hours (int): Heures d'historique (max 168 = 7 jours)
        max_tracks (int): Nombre max de trajectoires à récupérer (économie API)
    
    Returns:
        dict: {
            "arrivals": [...],
            "departures": [...],
            "total_flights": int,
            "tracks_retrieved": int,
            "period": {"start": datetime, "end": datetime}
        }
    """
    print(f"📡 Récupération des vols BVA des {hours} dernières heures...")
    
    # Récupérer arrivées et départs
    arrivals = get_flights_by_airport(AIRPORT_ICAO, hours, arrival=True)
    time.sleep(0.5)  # Respecter le rate limit
    departures = get_flights_by_airport(AIRPORT_ICAO, hours, arrival=False)
    
    print(f"   Arrivées: {len(arrivals)} | Départs: {len(departures)}")
    
    # Récupérer les trajectoires pour les vols les plus récents
    all_flights = arrivals + departures
    all_flights.sort(key=lambda x: x.get('last_seen_ts', 0) or 0, reverse=True)
    
    tracks_retrieved = 0
    
    for flight in all_flights[:max_tracks]:
        if tracks_retrieved >= max_tracks:
            break
            
        icao24 = flight.get('icao24')
        if not icao24 or icao24 == 'N/A':
            continue
        
        # Utiliser le timestamp du vol pour récupérer sa trajectoire
        ts = flight.get('last_seen_ts', 0)
        
        track = get_flight_track(icao24, timestamp=ts)
        time.sleep(0.3)  # Rate limit
        
        if track and track.get('waypoints'):
            flight['track'] = track
            flight['has_track'] = True
            tracks_retrieved += 1
            print(f"   ✓ Trajectoire {flight['callsign']}: {len(track['waypoints'])} points")
        else:
            flight['track'] = None
            flight['has_track'] = False
    
    # Séparer à nouveau
    arrivals_final = [f for f in all_flights if f.get('is_arrival', False)]
    departures_final = [f for f in all_flights if not f.get('is_arrival', False)]
    
    return {
        "arrivals": arrivals_final,
        "departures": departures_final,
        "total_flights": len(all_flights),
        "tracks_retrieved": tracks_retrieved,
        "period": {
            "start": datetime.now(timezone.utc) - timedelta(hours=hours),
            "end": datetime.now(timezone.utc),
            "hours": hours
        }
    }


def get_historical_flights_by_day(days=7):
    """
    Récupère les vols BVA par jour pour analyse temporelle.
    
    Args:
        days (int): Nombre de jours (max 7)
    
    Returns:
        dict: Statistiques par jour avec vols
    """
    hours = min(days * 24, 168)
    
    arrivals = get_flights_by_airport(AIRPORT_ICAO, hours, arrival=True)
    time.sleep(0.5)
    departures = get_flights_by_airport(AIRPORT_ICAO, hours, arrival=False)
    
    # Regrouper par jour
    by_day = {}
    
    for flight in arrivals:
        if flight.get('last_seen'):
            day = flight['last_seen'].strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = {"arrivals": [], "departures": [], "date": day}
            by_day[day]["arrivals"].append(flight)
    
    for flight in departures:
        if flight.get('first_seen'):
            day = flight['first_seen'].strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = {"arrivals": [], "departures": [], "date": day}
            by_day[day]["departures"].append(flight)
    
    # Calculer stats par jour
    for day, data in by_day.items():
        data["total"] = len(data["arrivals"]) + len(data["departures"])
        data["arrivals_count"] = len(data["arrivals"])
        data["departures_count"] = len(data["departures"])
    
    return {
        "by_day": dict(sorted(by_day.items())),
        "total_arrivals": len(arrivals),
        "total_departures": len(departures),
        "days": len(by_day)
    }


# Coordonnées aéroports majeurs (pour tracer les lignes quand pas de trajectoire)
AIRPORT_COORDS = {
    "LFOB": (49.4544, 2.1106),   # Beauvais
    "LFPG": (49.0097, 2.5479),   # Paris CDG
    "LFPO": (48.7262, 2.3597),   # Paris Orly
    "EGLL": (51.4700, -0.4543),  # Londres Heathrow
    "EGSS": (51.8850, 0.2350),   # Londres Stansted
    "LEMD": (40.4719, -3.5626),  # Madrid
    "LIRF": (41.8003, 12.2389),  # Rome Fiumicino
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
    "LEPA": (39.5517, 2.7388),   # Palma
    "GCTS": (28.0445, -16.5725), # Tenerife Sud
    "LPFR": (37.0144, -7.9659),  # Faro
    "LEAL": (38.2822, -0.5582),  # Alicante
    "LEMG": (36.6749, -4.4991),  # Malaga
    "LFML": (43.4393, 5.2214),   # Marseille
    "LFMN": (43.6584, 7.2159),   # Nice
    "LFLL": (45.7256, 5.0811),   # Lyon
    "LSGG": (46.2381, 6.1089),   # Genève
    "EBBR": (50.9014, 4.4844),   # Bruxelles
    "EGKK": (51.1537, -0.1821),  # Londres Gatwick
    "LIMC": (45.6306, 8.7231),   # Milan Malpensa
    "LIPZ": (45.5053, 12.3519),  # Venise
    "LTFM": (41.2753, 28.7519),  # Istanbul
}


def get_airport_coords(icao_code):
    """Retourne les coordonnées d'un aéroport."""
    if not icao_code or icao_code == "N/A":
        return None
    return AIRPORT_COORDS.get(icao_code.upper())


def estimate_flight_path(origin_coords, dest_coords, num_points=30):
    """
    Génère une trajectoire estimée (ligne géodésique simplifiée).
    Utile quand les vraies trajectoires ne sont pas disponibles.
    """
    if not origin_coords or not dest_coords:
        return []
    
    lat1, lon1 = origin_coords
    lat2, lon2 = dest_coords
    
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = lat1 + t * (lat2 - lat1)
        lon = lon1 + t * (lon2 - lon1)
        points.append({"lat": lat, "lon": lon})
    
    return points


# =============================================================================
# Test du module
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("    TEST MODULE OPENSKY V2 — TRAJECTOIRES BVA")
    print("=" * 60)
    print()
    
    # Test connexion
    print("1. Test de connexion...")
    status = test_connection()
    print(f"   {status['message']}")
    print(f"   Token valide: {status['token_valid']}")
    print(f"   Peut récupérer tracks: {status['can_get_tracks']}")
    print()
    
    if status['with_auth']:
        # Test vols BVA
        print("2. Récupération des vols BVA (24h)...")
        data = get_beauvais_flights_with_tracks(hours=24, max_tracks=5)
        
        print(f"   Total vols: {data['total_flights']}")
        print(f"   Trajectoires récupérées: {data['tracks_retrieved']}")
        print()
        
        # Afficher quelques vols
        if data['arrivals']:
            print("   📥 Arrivées:")
            for f in data['arrivals'][:3]:
                track_info = f"✓ {len(f['track']['waypoints'])} pts" if f.get('has_track') else "✗"
                print(f"      {f['callsign']:8} | {f['origin']} → LFOB | Track: {track_info}")
        
        if data['departures']:
            print("   📤 Départs:")
            for f in data['departures'][:3]:
                track_info = f"✓ {len(f['track']['waypoints'])} pts" if f.get('has_track') else "✗"
                print(f"      {f['callsign']:8} | LFOB → {f['destination']} | Track: {track_info}")
    
    print()
    print("=" * 60)