"""
Script de test — Vérifie les connexions API et les trajectoires
Lance ce script avant d'utiliser l'application
"""

import os
import sys

# Ajouter le dossier racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("   TEST DES CONNEXIONS API — BVA Monitor")
print("=" * 60)
print()

# 1. Test OpenSky
print("1️⃣  Test OpenSky Network...")
try:
    from api.opensky_v2 import test_connection, get_beauvais_flights_with_tracks
    
    status = test_connection()
    print(f"   {status['message']}")
    print(f"   Token valide: {status['token_valid']}")
    print(f"   Peut récupérer trajectoires: {status['can_get_tracks']}")
    
    if status['with_auth']:
        print()
        print("   📡 Test récupération vols BVA (24h, max 3 trajectoires)...")
        data = get_beauvais_flights_with_tracks(hours=24, max_tracks=3)
        print(f"   ✅ Total vols: {data['total_flights']}")
        print(f"   ✅ Arrivées: {len(data['arrivals'])}")
        print(f"   ✅ Départs: {len(data['departures'])}")
        print(f"   ✅ Trajectoires récupérées: {data['tracks_retrieved']}")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# 2. Test AeroDataBox
print("2️⃣  Test AeroDataBox...")
try:
    from api.aerodatabox import test_connection as test_aero
    
    status = test_aero()
    print(f"   {status['message']}")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# 3. Test OpenMeteo (météo)
print("3️⃣  Test OpenMeteo (Météo)...")
try:
    from api.weather import get_current_weather, get_historical_weather
    
    weather = get_current_weather()
    if weather:
        print(f"   ✅ Météo actuelle: {weather['temperature_2m']}°C, Vent: {weather['wind_speed_10m']} km/h")
    else:
        print("   ❌ Impossible de récupérer la météo")
    
    history = get_historical_weather(days=7)
    if history:
        print(f"   ✅ Historique météo: {len(history['time'])} jours")
    else:
        print("   ❌ Impossible de récupérer l'historique")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# 4. Test FlightRadar24
print("4️⃣  Test FlightRadar24...")
try:
    from api.flights import get_flights_in_area
    
    flights = get_flights_in_area()
    print(f"   ✅ Vols temps réel dans la zone: {len(flights)}")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()
print("=" * 60)
print("   FIN DES TESTS")
print("=" * 60)
print()
print("💡 Pour lancer l'application :")
print("   streamlit run app.py")
print()
print("📍 La page 'Carte Historique' est maintenant disponible dans le menu !")