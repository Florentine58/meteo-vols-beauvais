"""
Module Trajectoires V3 — FlightRadar24 + OpenSky
================================================

Utilise FlightRadar24 (GRATUIT et ILLIMITÉ) pour les vols,
puis OpenSky pour les trajectoires réelles.

Plus besoin d'AeroDataBox !

Projet Mineure Numérique B2 — 2025
"""

import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

# Coordonnées Beauvais
BVA_LAT = 49.4544
BVA_LON = 2.1106
AIRPORT_ICAO = "LFOB"
AIRPORT_IATA = "BVA"

# URLs API OpenSky
OPENSKY_BASE_URL = "https://opensky-network.org/api"
OPENSKY_AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

# Cache token
_token_cache = {"token": None, "expires": None}


# ============================================================================
# FLIGHTRADAR24 - Source principale des vols (GRATUIT)
# ============================================================================

def get_flightradar_airport_flights():
    """
    Récupère les vols de Beauvais via FlightRadar24.
    Compatible avec plusieurs versions de la lib.
    """
    try:
        from FlightRadar24 import FlightRadar24API
        fr_api = FlightRadar24API()

        print("   🔍 Connexion FlightRadar24...")

        details = None
        last_err = None

        # 1) Essai direct avec ICAO
        try:
            details = fr_api.get_airport_details(AIRPORT_ICAO, flight_limit=50)
        except Exception as e:
            last_err = e

        # 2) Essai direct avec IATA
        if details is None:
            try:
                details = fr_api.get_airport_details(AIRPORT_IATA, flight_limit=50)
            except Exception as e:
                last_err = e

        # 3) Essai via get_airport (certaines versions exigent l'objet)
        if details is None:
            try:
                airport_obj = fr_api.get_airport(AIRPORT_IATA)
                # selon versions, get_airport_details accepte objet, dict ou code
                try:
                    details = fr_api.get_airport_details(airport_obj, flight_limit=50)
                except Exception:
                    # fallback: essayer d'extraire des attributs
                    airport_code = getattr(airport_obj, "icao", None) or getattr(airport_obj, "iata", None)
                    if airport_code:
                        details = fr_api.get_airport_details(airport_code, flight_limit=50)
            except Exception as e:
                last_err = e

        if details is None:
            raise RuntimeError(f"Impossible d'obtenir les détails aéroport via FlightRadar24. Dernière erreur: {last_err}")

        plugin_data = details.get('airport', {}).get('pluginData', {})
        schedule = plugin_data.get('schedule', {})

        arrivals_raw = schedule.get('arrivals', {}).get('data', [])
        departures_raw = schedule.get('departures', {}).get('data', [])

        arrivals = []
        for arr in arrivals_raw:
            flight = arr.get('flight', {})
            identification = flight.get('identification', {})
            airport_info = flight.get('airport', {})
            aircraft = flight.get('aircraft', {})
            time_info = flight.get('time', {})

            ts = (time_info.get('real', {}).get('arrival') or
                  time_info.get('estimated', {}).get('arrival') or
                  time_info.get('scheduled', {}).get('arrival') or 0)

            flight_time = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
            icao24 = aircraft.get('hex', '').lower() if aircraft.get('hex') else None

            arrivals.append({
                "callsign": identification.get('number', {}).get('default', 'N/A'),
                "icao24": icao24,
                "registration": aircraft.get('registration', 'N/A'),
                "aircraft_type": aircraft.get('model', {}).get('code', 'N/A'),
                "airline": flight.get('airline', {}).get('name', 'N/A'),
                "origin": airport_info.get('origin', {}).get('code', {}).get('iata', 'N/A'),
                "origin_icao": airport_info.get('origin', {}).get('code', {}).get('icao', 'N/A'),
                "destination": "BVA",
                "status": flight.get('status', {}).get('text', 'N/A'),
                "timestamp": ts,
                "first_seen": flight_time,
                "last_seen": flight_time,
                "is_arrival": True,
                "has_track": False,
                "track": None
            })

        departures = []
        for dep in departures_raw:
            flight = dep.get('flight', {})
            identification = flight.get('identification', {})
            airport_info = flight.get('airport', {})
            aircraft = flight.get('aircraft', {})
            time_info = flight.get('time', {})

            ts = (time_info.get('real', {}).get('departure') or
                  time_info.get('estimated', {}).get('departure') or
                  time_info.get('scheduled', {}).get('departure') or 0)

            flight_time = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
            icao24 = aircraft.get('hex', '').lower() if aircraft.get('hex') else None

            departures.append({
                "callsign": identification.get('number', {}).get('default', 'N/A'),
                "icao24": icao24,
                "registration": aircraft.get('registration', 'N/A'),
                "aircraft_type": aircraft.get('model', {}).get('code', 'N/A'),
                "airline": flight.get('airline', {}).get('name', 'N/A'),
                "origin": "BVA",
                "destination": airport_info.get('destination', {}).get('code', {}).get('iata', 'N/A'),
                "destination_icao": airport_info.get('destination', {}).get('code', {}).get('icao', 'N/A'),
                "status": flight.get('status', {}).get('text', 'N/A'),
                "timestamp": ts,
                "first_seen": flight_time,
                "last_seen": flight_time,
                "is_arrival": False,
                "has_track": False,
                "track": None
            })

        print(f"   ✓ FlightRadar24: {len(arrivals)} arrivées, {len(departures)} départs")
        return {"arrivals": arrivals, "departures": departures}

    except Exception as e:
        print(f"   ❌ Erreur FlightRadar24: {e}")
        return {"arrivals": [], "departures": []}



# ============================================================================
# OPENSKY - Authentification et trajectoires
# ============================================================================

def get_oauth_token():
    """Obtient un token OAuth2 pour OpenSky."""
    global _token_cache
    
    if _token_cache["token"] and _token_cache["expires"]:
        if datetime.now() < _token_cache["expires"]:
            return _token_cache["token"]
    
    if not OPENSKY_CLIENT_ID or not OPENSKY_CLIENT_SECRET:
        return None
    
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": OPENSKY_CLIENT_ID,
            "client_secret": OPENSKY_CLIENT_SECRET
        }
        response = requests.post(OPENSKY_AUTH_URL, data=data, timeout=15)
        
        if response.status_code == 200:
            token_data = response.json()
            _token_cache["token"] = token_data["access_token"]
            _token_cache["expires"] = datetime.now() + timedelta(minutes=25)
            print("   ✓ Token OpenSky obtenu")
            return _token_cache["token"]
        else:
            print(f"   ⚠️ Erreur token OpenSky: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Exception token: {e}")
    return None


def get_flight_track(icao24, timestamp=0):
    """
    Récupère la trajectoire réelle d'un avion via OpenSky.
    
    Args:
        icao24: Code hex de l'avion (ex: "3c675a")
        timestamp: Timestamp Unix du vol
    
    Returns:
        dict avec waypoints ou None
    """
    token = get_oauth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{OPENSKY_BASE_URL}/tracks/all"
    params = {"icao24": icao24.lower(), "time": timestamp}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            waypoints = []
            
            for point in data.get("path", []):
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
                    "waypoints": waypoints
                }
    except Exception as e:
        print(f"   ⚠️ Erreur trajectoire {icao24}: {e}")
    
    return None


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def get_beauvais_flights_with_tracks(hours=24, max_tracks=20):
    """
    🎯 Récupère les vols BVA avec trajectoires.
    
    Stratégie :
    1. FlightRadar24 → Vols (GRATUIT ILLIMITÉ)
    2. OpenSky → Trajectoires réelles
    
    Args:
        hours: Période (ignoré, FR24 donne les vols du jour)
        max_tracks: Nombre max de trajectoires à récupérer
    
    Returns:
        dict avec arrivals, departures, stats
    """
    print(f"📡 Récupération des vols BVA...")
    
    # Étape 1 : FlightRadar24
    fr_data = get_flightradar_airport_flights()
    arrivals = fr_data.get("arrivals", [])
    departures = fr_data.get("departures", [])
    
    # Étape 2 : Trajectoires OpenSky
    all_flights = arrivals + departures
    tracks_retrieved = 0
    
    token = get_oauth_token()
    if token and all_flights:
        print(f"   🔍 Récupération trajectoires OpenSky (max {max_tracks})...")
        
        # Trier par timestamp (plus récents d'abord)
        all_flights.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        for flight in all_flights[:max_tracks]:
            icao24 = flight.get('icao24')
            if not icao24 or len(icao24) < 4:
                continue
            
            ts = flight.get('timestamp', 0)
            track = get_flight_track(icao24, timestamp=ts)
            time.sleep(0.3)  # Rate limit
            
            if track and track.get('waypoints'):
                flight['track'] = track
                flight['has_track'] = True
                tracks_retrieved += 1
                print(f"   ✓ Trajectoire {flight['callsign']}: {len(track['waypoints'])} pts")
        
        print(f"   ✓ Total trajectoires: {tracks_retrieved}")
    else:
        print("   ⚠️ OpenSky non authentifié - trajectoires estimées uniquement")
    
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
    Fonction de compatibilité - retourne les vols actuels.
    (L'historique long terme nécessiterait une API premium)
    """
    data = get_beauvais_flights_with_tracks(hours=24, max_tracks=10)
    return {
        "by_day": {},
        "total": data['total_flights'],
        "arrivals": data['arrivals'],
        "departures": data['departures']
    }


# ============================================================================
# TEST DE CONNEXION
# ============================================================================

def test_connection():
    """Teste les connexions aux APIs."""
    result = {
        "status": "error",
        "flightradar": False,
        "opensky_auth": False,
        "can_get_tracks": False,
        "message": ""
    }
    
    # Test FlightRadar24
    try:
        from FlightRadar24 import FlightRadar24API
        fr_api = FlightRadar24API()
        bounds = fr_api.get_bounds_by_point(BVA_LAT, BVA_LON, 10000)
        result["flightradar"] = True
    except Exception as e:
        print(f"FlightRadar24 erreur: {e}")
    
    # Test OpenSky
    token = get_oauth_token()
    result["opensky_auth"] = token is not None
    result["can_get_tracks"] = token is not None
    
    # Statut global
    if result["flightradar"]:
        if result["opensky_auth"]:
            result["status"] = "success"
            result["message"] = "FlightRadar24 + OpenSky OK"
        else:
            result["status"] = "warning"
            result["message"] = "FlightRadar24 OK (trajectoires estimées)"
    else:
        result["status"] = "error"
        result["message"] = "FlightRadar24 indisponible"
    
    return result


# ============================================================================
# COORDONNÉES AÉROPORTS (pour trajectoires estimées)
# ============================================================================

AIRPORT_COORDS = {
    # France
    "LFOB": (49.4544, 2.1106), "BVA": (49.4544, 2.1106),
    "LFPG": (49.0097, 2.5479), "CDG": (49.0097, 2.5479),
    "LFPO": (48.7262, 2.3597), "ORY": (48.7262, 2.3597),
    
    # UK & Ireland
    "EGLL": (51.4700, -0.4543), "LHR": (51.4700, -0.4543),
    "EGSS": (51.8850, 0.2350), "STN": (51.8850, 0.2350),
    "EGKK": (51.1537, -0.1821), "LGW": (51.1537, -0.1821),
    "EGGW": (51.8747, -0.3683), "LTN": (51.8747, -0.3683),
    "EGCC": (53.3537, -2.2750), "MAN": (53.3537, -2.2750),
    "EIDW": (53.4213, -6.2701), "DUB": (53.4213, -6.2701),
    "EICK": (51.8413, -8.4911), "ORK": (51.8413, -8.4911),
    
    # Spain
    "LEMD": (40.4719, -3.5626), "MAD": (40.4719, -3.5626),
    "LEBL": (41.2971, 2.0785), "BCN": (41.2971, 2.0785),
    "LEPA": (39.5517, 2.7388), "PMI": (39.5517, 2.7388),
    "GCTS": (28.0445, -16.5725), "TFS": (28.0445, -16.5725),
    "LEAL": (38.2822, -0.5582), "ALC": (38.2822, -0.5582),
    "LEMG": (36.6749, -4.4991), "AGP": (36.6749, -4.4991),
    "LEGE": (41.9009, 2.7606), "GRO": (41.9009, 2.7606),
    
    # Portugal
    "LPPT": (38.7813, -9.1359), "LIS": (38.7813, -9.1359),
    "LPFR": (37.0144, -7.9659), "FAO": (37.0144, -7.9659),
    "LPPR": (41.2481, -8.6814), "OPO": (41.2481, -8.6814),
    
    # Italy
    "LIRF": (41.8003, 12.2389), "FCO": (41.8003, 12.2389),
    "LIMC": (45.6306, 8.7231), "MXP": (45.6306, 8.7231),
    "LIME": (45.6739, 9.7042), "BGY": (45.6739, 9.7042),
    "LIPZ": (45.5053, 12.3519), "VCE": (45.5053, 12.3519),
    "LIPH": (45.6484, 12.1944), "TSF": (45.6484, 12.1944),
    "LIRN": (40.8860, 14.2908), "NAP": (40.8860, 14.2908),
    "LICJ": (38.1760, 13.0910), "PMO": (38.1760, 13.0910),
    
    # Germany
    "EDDF": (50.0379, 8.5622), "FRA": (50.0379, 8.5622),
    "EDDM": (48.3538, 11.7861), "MUC": (48.3538, 11.7861),
    "EDDB": (52.3622, 13.5009), "BER": (52.3622, 13.5009),
    
    # Central Europe
    "LOWW": (48.1103, 16.5697), "VIE": (48.1103, 16.5697),
    "EPWA": (52.1657, 20.9671), "WAW": (52.1657, 20.9671),
    "EPMO": (52.4511, 20.6517), "WMI": (52.4511, 20.6517),
    "LKPR": (50.1008, 14.2600), "PRG": (50.1008, 14.2600),
    "LHBP": (47.4369, 19.2556), "BUD": (47.4369, 19.2556),
    "LROP": (44.5711, 26.0850), "OTP": (44.5711, 26.0850),
    
    # Benelux
    "EHAM": (52.3086, 4.7639), "AMS": (52.3086, 4.7639),
    "EBCI": (50.4592, 4.4538), "CRL": (50.4592, 4.4538),
    
    # Scandinavia
    "EKCH": (55.6180, 12.6560), "CPH": (55.6180, 12.6560),
    "ESSA": (59.6519, 17.9186), "ARN": (59.6519, 17.9186),
    
    # Greece
    "LGAV": (37.9364, 23.9445), "ATH": (37.9364, 23.9445),
    "LGIR": (35.3397, 25.1803), "HER": (35.3397, 25.1803),
    
    # Morocco
    "GMMN": (33.3675, -7.5900), "CMN": (33.3675, -7.5900),
    "GMMX": (31.6069, -8.0363), "RAK": (31.6069, -8.0363),
    "GMFF": (33.9273, -4.9780), "FEZ": (33.9273, -4.9780),
}


def get_airport_coords(code):
    """Retourne les coordonnées d'un aéroport."""
    if not code or code == "N/A":
        return None
    return AIRPORT_COORDS.get(code.upper())


def estimate_flight_path(origin_coords, dest_coords, num_points=30):
    """Génère une trajectoire estimée (ligne droite)."""
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


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   TEST MODULE TRAJECTOIRES V3")
    print("=" * 60)
    
    status = test_connection()
    print(f"\n{status['message']}")
    print(f"   FlightRadar24: {'✓' if status['flightradar'] else '✗'}")
    print(f"   OpenSky Auth: {'✓' if status['opensky_auth'] else '✗'}")
    
    if status['flightradar']:
        print("\n📡 Test récupération vols...")
        data = get_beauvais_flights_with_tracks(hours=24, max_tracks=5)
        print(f"\n   Total: {data['total_flights']} vols")
        print(f"   Arrivées: {len(data['arrivals'])}")
        print(f"   Départs: {len(data['departures'])}")
        print(f"   Trajectoires: {data['tracks_retrieved']}")
        
        if data['arrivals']:
            print("\n   Exemples arrivées:")
            for f in data['arrivals'][:3]:
                print(f"   - {f['callsign']} depuis {f['origin']} ({f['airline']})")