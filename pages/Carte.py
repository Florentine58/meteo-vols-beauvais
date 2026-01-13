"""
Page Carte — Carte interactive avec météo et positions des avions
"""

import streamlit as st
import folium
from streamlit_folium import st_folium

# Import direct depuis la racine du projet
from api.weather import get_current_weather, BEAUVAIS_LAT, BEAUVAIS_LON
from api.flights import get_flights_in_area, get_airport_info, BVA_LAT, BVA_LON

# Configuration de la page
st.set_page_config(
    page_title="Carte Beauvais",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Carte Interactive")
st.markdown("*Visualisation en temps réel de la météo et du trafic aérien*")

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.rerun()

st.divider()

# =============================================================================
# Récupération des données
# =============================================================================
with st.spinner("Chargement des données..."):
    weather = get_current_weather()
    flights = get_flights_in_area()
    airport = get_airport_info()

# =============================================================================
# Création de la carte
# =============================================================================

# Centre de la carte (entre Beauvais ville et l'aéroport)
center_lat = (BEAUVAIS_LAT + BVA_LAT) / 2
center_lon = (BEAUVAIS_LON + BVA_LON) / 2

# Créer la carte Folium
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles="OpenStreetMap"
)

# =============================================================================
# Marqueur : Ville de Beauvais (météo)
# =============================================================================
if weather:
    weather_popup = f"""
    <div style="font-family: Arial; width: 200px;">
        <h4 style="margin: 0; color: #2d3748;">🌤️ Météo Beauvais</h4>
        <hr style="margin: 5px 0;">
        <p style="margin: 3px 0;"><b>🌡️ Température:</b> {weather['temperature_2m']}°C</p>
        <p style="margin: 3px 0;"><b>💧 Humidité:</b> {weather['relative_humidity_2m']}%</p>
        <p style="margin: 3px 0;"><b>💨 Vent:</b> {weather['wind_speed_10m']} km/h</p>
        <p style="margin: 3px 0;"><b>🧭 Direction:</b> {weather['wind_direction_10m']}°</p>
    </div>
    """
    
    folium.Marker(
        location=[BEAUVAIS_LAT, BEAUVAIS_LON],
        popup=folium.Popup(weather_popup, max_width=250),
        tooltip="🌤️ Météo Beauvais",
        icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
    ).add_to(m)

# =============================================================================
# Marqueur : Aéroport Paris-Beauvais
# =============================================================================
airport_popup = f"""
<div style="font-family: Arial; width: 200px;">
    <h4 style="margin: 0; color: #2d3748;">✈️ {airport['name']}</h4>
    <hr style="margin: 5px 0;">
    <p style="margin: 3px 0;"><b>Code IATA:</b> {airport['code_iata']}</p>
    <p style="margin: 3px 0;"><b>Code ICAO:</b> {airport['code_icao']}</p>
    <p style="margin: 3px 0;"><b>Altitude:</b> {airport['altitude']} m</p>
</div>
"""

folium.Marker(
    location=[BVA_LAT, BVA_LON],
    popup=folium.Popup(airport_popup, max_width=250),
    tooltip="🛫 Aéroport Paris-Beauvais",
    icon=folium.Icon(color='red', icon='plane', prefix='fa')
).add_to(m)

# Cercle autour de l'aéroport (zone de surveillance)
folium.Circle(
    location=[BVA_LAT, BVA_LON],
    radius=50000,  # 50 km en mètres
    color='red',
    fill=True,
    fillOpacity=0.05,
    popup="Zone de surveillance (50 km)"
).add_to(m)

# =============================================================================
# Marqueurs : Avions en vol
# =============================================================================
for flight in flights:
    # Couleur selon si l'avion est au sol ou en vol
    if flight.get('on_ground', False):
        color = 'gray'
        icon_name = 'plane'
    else:
        color = 'green'
        icon_name = 'plane'
    
    # Construire le popup
    origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
    dest = flight['destination'] if flight['destination'] != 'N/A' else '???'
    
    flight_popup = f"""
    <div style="font-family: Arial; width: 200px;">
        <h4 style="margin: 0; color: #2d3748;">✈️ {flight['callsign']}</h4>
        <hr style="margin: 5px 0;">
        <p style="margin: 3px 0;"><b>Route:</b> {origin} → {dest}</p>
        <p style="margin: 3px 0;"><b>Avion:</b> {flight['aircraft_type']}</p>
        <p style="margin: 3px 0;"><b>Altitude:</b> {flight['altitude']} ft</p>
        <p style="margin: 3px 0;"><b>Vitesse:</b> {flight['ground_speed']} kts</p>
        <p style="margin: 3px 0;"><b>Cap:</b> {flight['heading']}°</p>
    </div>
    """
    
    folium.Marker(
        location=[flight['latitude'], flight['longitude']],
        popup=folium.Popup(flight_popup, max_width=250),
        tooltip=f"✈️ {flight['callsign']}",
        icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
    ).add_to(m)

# =============================================================================
# Affichage de la carte
# =============================================================================

# Statistiques au-dessus de la carte
col1, col2, col3, col4 = st.columns(4)

with col1:
    if weather:
        st.metric("🌡️ Température", f"{weather['temperature_2m']}°C")
    else:
        st.metric("🌡️ Température", "N/A")

with col2:
    if weather:
        st.metric("💨 Vent", f"{weather['wind_speed_10m']} km/h")
    else:
        st.metric("💨 Vent", "N/A")

with col3:
    st.metric("✈️ Vols détectés", len(flights))

with col4:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.metric("🛫 En vol", in_flight)

st.divider()

# Afficher la carte
st_folium(m, width=None, height=600, use_container_width=True)

# =============================================================================
# Légende
# =============================================================================
st.divider()
st.markdown("### 🔍 Légende")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🔵 **Marqueur bleu** — Météo Beauvais")
    
with col2:
    st.markdown("🔴 **Marqueur rouge** — Aéroport BVA")

with col3:
    st.markdown("🟢 **Marqueur vert** — Avion en vol")
    st.markdown("⚫ **Marqueur gris** — Avion au sol")

# =============================================================================
# Liste des vols (optionnel)
# =============================================================================
with st.expander("📋 Liste des vols détectés"):
    if flights:
        for flight in flights:
            status = "🅿️ Au sol" if flight.get('on_ground', False) else "🛫 En vol"
            st.markdown(f"**{flight['callsign']}** — {flight['origin']} → {flight['destination']} — {status}")
    else:
        st.info("Aucun vol détecté")

# Footer
st.divider()
st.caption("Carte générée avec Folium — Données FlightRadar24 & OpenMeteo")