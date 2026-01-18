"""
Page Vols — Affiche le trafic aérien de l'aéroport Paris-Beauvais
"""

import streamlit as st
from datetime import datetime

# Import direct depuis la racine du projet
from api.flights import get_flights_in_area, get_airport_info, get_arrivals, get_departures

# Configuration de la page
st.set_page_config(
    page_title="Vols Beauvais",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Trafic Aérien — Paris-Beauvais")

# Infos aéroport
airport = get_airport_info()
st.markdown(f"**{airport['name']}** | Code IATA: `{airport['code_iata']}` | Code ICAO: `{airport['code_icao']}`")

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.rerun()

st.divider()


# SECTION 1 : Vols en temps réel dans la zone

st.header("📡 Vols en temps réel")
st.caption(f"Avions dans un rayon de 50 km autour de l'aéroport")

with st.spinner("Recherche des vols en cours..."):
    flights = get_flights_in_area()

if flights:
    st.success(f"✈️ **{len(flights)} vol(s)** détecté(s) dans la zone")
    
    # Afficher en colonnes
    col1, col2, col3 = st.columns(3)
    
    # Compter les avions en vol vs au sol
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    on_ground = len([f for f in flights if f.get('on_ground', False)])
    
    col1.metric("🛫 En vol", in_flight)
    col2.metric("🅿️ Au sol", on_ground)
    col3.metric("📊 Total", len(flights))
    
    st.divider()
    
    # Liste des vols
    for i, flight in enumerate(flights):
        with st.container():
            cols = st.columns([2, 2, 1, 1, 1])
            
            # Callsign et compagnie
            cols[0].markdown(f"**✈️ {flight['callsign']}**")
            cols[0].caption(f"Compagnie: {flight['airline_icao']}")
            
            # Route
            origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
            dest = flight['destination'] if flight['destination'] != 'N/A' else '???'
            cols[1].markdown(f"🛫 {origin} → 🛬 {dest}")
            cols[1].caption(f"Avion: {flight['aircraft_type']}")
            
            # Altitude
            altitude_ft = flight['altitude']
            altitude_m = int(altitude_ft * 0.3048)
            cols[2].metric("Altitude", f"{altitude_ft} ft")
            
            # Vitesse
            speed_kts = flight['ground_speed']
            speed_kmh = int(speed_kts * 1.852)
            cols[3].metric("Vitesse", f"{speed_kts} kts")
            
            # Cap
            cols[4].metric("Cap", f"{flight['heading']}°")
            
            st.divider()

else:
    st.info("🔍 Aucun vol détecté dans la zone actuellement. Cela peut arriver si aucun avion ne survole Beauvais en ce moment.")

st.divider()


# SECTION 2 : Informations aéroport

st.header("ℹ️ Informations sur l'aéroport")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📍 Localisation")
    st.markdown(f"""
    - **Ville** : {airport.get('city', 'Beauvais')}, {airport.get('country', 'France')}
    - **Latitude** : {airport['latitude']}°
    - **Longitude** : {airport['longitude']}°
    - **Altitude** : {airport['altitude']} m
    """)

with col2:
    st.markdown("### 🏢 Compagnies principales")
    for company in airport['principales_compagnies']:
        st.markdown(f"- {company}")

# Footer
st.divider()
st.caption("Données fournies par FlightRadar24 API — Usage éducatif uniquement")