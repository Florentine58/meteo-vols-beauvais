"""
Page Carte — Carte interactive version professionnelle
"""

import streamlit as st
import folium
from streamlit_folium import st_folium

from api.weather import get_current_weather, BEAUVAIS_LAT, BEAUVAIS_LON
from api.flights import get_flights_in_area, get_airport_info, BVA_LAT, BVA_LON

# Configuration
st.set_page_config(
    page_title="BVA Monitor | Carte",
    page_icon="✈️",
    layout="wide"
)

# CSS Professionnel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    
    .page-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #00D4FF;
    }
    .page-header h1 { color: #FAFAFA; font-weight: 600; margin: 0; font-size: 1.35rem; }
    .page-header p { color: #94A3B8; margin: 0.25rem 0 0 0; font-size: 0.85rem; }
    
    .control-panel {
        background: #151B28;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        margin-bottom: 1rem;
    }
    
    .status-live {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(34, 197, 94, 0.15);
        color: #86EFAC;
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-paused {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(234, 179, 8, 0.15);
        color: #FDE047;
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0;
        font-size: 0.85rem;
        color: #94A3B8;
    }
    
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #64748B;
        font-size: 0.75rem;
        border-top: 1px solid #2D3748;
        margin-top: 2rem;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    hr { border: none; border-top: 1px solid #2D3748; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# En-tête
st.markdown("""
<div class="page-header">
    <h1>Carte Interactive</h1>
    <p>Visualisation en temps réel de la météo et du trafic aérien</p>
</div>
""", unsafe_allow_html=True)

# Contrôles
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("Actualiser", type="secondary", use_container_width=True):
        if 'carte_figee' in st.session_state:
            del st.session_state['carte_figee']
        st.rerun()

with col2:
    if 'carte_figee' not in st.session_state:
        st.session_state['carte_figee'] = False
    
    if st.session_state['carte_figee']:
        if st.button("Reprendre", type="primary", use_container_width=True):
            st.session_state['carte_figee'] = False
            st.rerun()
    else:
        if st.button("Figer", type="secondary", use_container_width=True):
            st.session_state['carte_figee'] = True
            st.rerun()

with col3:
    if st.session_state.get('carte_figee', False):
        st.markdown('<span class="status-paused">● Carte figée</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-live">● Mode temps réel</span>', unsafe_allow_html=True)

st.divider()

# Chargement des données
if st.session_state.get('carte_figee', False):
    if 'cached_weather' not in st.session_state:
        weather = get_current_weather()
        flights = get_flights_in_area()
        st.session_state['cached_weather'] = weather
        st.session_state['cached_flights'] = flights
    else:
        weather = st.session_state['cached_weather']
        flights = st.session_state['cached_flights']
else:
    with st.spinner("Chargement..."):
        weather = get_current_weather()
        flights = get_flights_in_area()
        st.session_state['cached_weather'] = weather
        st.session_state['cached_flights'] = flights

airport = get_airport_info()

# Métriques
col1, col2, col3, col4 = st.columns(4)

with col1:
    temp = weather['temperature_2m'] if weather else "N/A"
    st.metric("TEMPÉRATURE", f"{temp}°C" if weather else "N/A")

with col2:
    wind = weather['wind_speed_10m'] if weather else "N/A"
    st.metric("VENT", f"{wind} km/h" if weather else "N/A")

with col3:
    st.metric("VOLS DÉTECTÉS", len(flights))

with col4:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.metric("EN VOL", in_flight)

st.divider()

# Carte
center_lat = (BEAUVAIS_LAT + BVA_LAT) / 2
center_lon = (BEAUVAIS_LON + BVA_LON) / 2

# Style de carte sombre
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles='CartoDB dark_matter'
)

# Marqueur météo
if weather:
    weather_popup = f"""
    <div style="font-family: Arial; width: 180px; color: #333;">
        <h4 style="margin: 0 0 8px 0; color: #1e3a5f;">Météo Beauvais</h4>
        <p style="margin: 4px 0;"><b>Température:</b> {weather['temperature_2m']}°C</p>
        <p style="margin: 4px 0;"><b>Humidité:</b> {weather['relative_humidity_2m']}%</p>
        <p style="margin: 4px 0;"><b>Vent:</b> {weather['wind_speed_10m']} km/h</p>
    </div>
    """
    folium.Marker(
        location=[BEAUVAIS_LAT, BEAUVAIS_LON],
        popup=folium.Popup(weather_popup, max_width=200),
        tooltip="Météo Beauvais",
        icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
    ).add_to(m)

# Marqueur aéroport
airport_popup = f"""
<div style="font-family: Arial; width: 180px; color: #333;">
    <h4 style="margin: 0 0 8px 0; color: #1e3a5f;">{airport['name']}</h4>
    <p style="margin: 4px 0;"><b>IATA:</b> {airport['code_iata']}</p>
    <p style="margin: 4px 0;"><b>ICAO:</b> {airport['code_icao']}</p>
    <p style="margin: 4px 0;"><b>Altitude:</b> {airport['altitude']} m</p>
</div>
"""
folium.Marker(
    location=[BVA_LAT, BVA_LON],
    popup=folium.Popup(airport_popup, max_width=200),
    tooltip="Aéroport BVA",
    icon=folium.Icon(color='red', icon='plane', prefix='fa')
).add_to(m)

# Zone de surveillance
folium.Circle(
    location=[BVA_LAT, BVA_LON],
    radius=50000,
    color='#00D4FF',
    fill=True,
    fillOpacity=0.05,
    weight=1
).add_to(m)

# Avions
for flight in flights:
    is_ground = flight.get('on_ground', False)
    color = 'gray' if is_ground else 'green'
    
    origin = flight['origin'] if flight['origin'] != 'N/A' else '---'
    dest = flight['destination'] if flight['destination'] != 'N/A' else '---'
    
    flight_popup = f"""
    <div style="font-family: Arial; width: 180px; color: #333;">
        <h4 style="margin: 0 0 8px 0; color: #1e3a5f;">{flight['callsign']}</h4>
        <p style="margin: 4px 0;"><b>Route:</b> {origin} → {dest}</p>
        <p style="margin: 4px 0;"><b>Type:</b> {flight['aircraft_type']}</p>
        <p style="margin: 4px 0;"><b>Altitude:</b> {flight['altitude']} ft</p>
        <p style="margin: 4px 0;"><b>Vitesse:</b> {flight['ground_speed']} kts</p>
    </div>
    """
    
    folium.Marker(
        location=[flight['latitude'], flight['longitude']],
        popup=folium.Popup(flight_popup, max_width=200),
        tooltip=flight['callsign'],
        icon=folium.Icon(color=color, icon='plane', prefix='fa')
    ).add_to(m)

# Afficher la carte
st_folium(m, width=None, height=550, use_container_width=True, returned_objects=[])

st.divider()

# Légende
st.markdown("#### Légende")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="legend-item">
        <div class="legend-dot" style="background: #0066CC;"></div>
        Météo Beauvais
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="legend-item">
        <div class="legend-dot" style="background: #CC0000;"></div>
        Aéroport BVA
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="legend-item">
        <div class="legend-dot" style="background: #22C55E;"></div>
        Avion en vol
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="legend-item">
        <div class="legend-dot" style="background: #6B7280;"></div>
        Avion au sol
    </div>
    """, unsafe_allow_html=True)

# Liste des vols
with st.expander("Liste des vols détectés"):
    if flights:
        for flight in flights:
            status = "Au sol" if flight.get('on_ground', False) else "En vol"
            st.caption(f"**{flight['callsign']}** — {flight['origin']} → {flight['destination']} — {status}")
    else:
        st.caption("Aucun vol détecté")

# Footer
st.markdown("""
<div class="footer">
    Carte : OpenStreetMap / CartoDB • Données : FlightRadar24 & OpenMeteo
</div>
""", unsafe_allow_html=True)