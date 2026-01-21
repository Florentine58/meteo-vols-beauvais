"""
Page Carte Interactive AMÉLIORÉE
- Trajectoires des avions (vraies ou estimées)
- Qualité de l'air en temps réel
- Conditions météo
- Impact environnemental
"""

import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import json
from datetime import datetime

# Imports des modules API
from api.weather import get_current_weather, BEAUVAIS_LAT, BEAUVAIS_LON
from api.flights import get_flights_in_area, get_airport_info, BVA_LAT, BVA_LON

# Imports des nouveaux modules (on va les créer dans le projet)
try:
    from api.air_quality import get_current_air_quality, calculate_aviation_air_impact
    HAS_AIR_QUALITY = True
except ImportError:
    HAS_AIR_QUALITY = False

try:
    from api.opensky_v2 import get_current_flights_in_area, get_flight_track, get_airport_coords, estimate_flight_path, test_connection
    HAS_OPENSKY_TRACKS = True
except ImportError:
    HAS_OPENSKY_TRACKS = False

# Configuration
st.set_page_config(
    page_title="BVA Monitor | Carte",
    page_icon="✈️",
    layout="wide"
)

# =============================================================================
# CSS Professionnel
# =============================================================================
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
    
    .stat-card {
        background: #151B28;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    .stat-value { font-size: 1.5rem; font-weight: 700; color: #FAFAFA; }
    .stat-label { font-size: 0.7rem; color: #64748B; text-transform: uppercase; }
    .stat-green { color: #22C55E; }
    .stat-yellow { color: #EAB308; }
    .stat-red { color: #EF4444; }
    .stat-blue { color: #00D4FF; }
    
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
    
    .legend-box {
        background: #151B28;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0;
        font-size: 0.8rem;
        color: #94A3B8;
    }
    
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    
    .legend-line {
        width: 20px;
        height: 3px;
        border-radius: 2px;
    }
    
    .info-panel {
        background: #1A1F2E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        margin-top: 0.5rem;
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

# =============================================================================
# En-tête
# =============================================================================
st.markdown("""
<div class="page-header">
    <h1>Carte Interactive - Trafic Aérien & Environnement</h1>
    <p>Visualisation temps réel des vols, trajectoires et qualité de l'air</p>
</div>
""", unsafe_allow_html=True)

# Contrôles
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

with col1:
    if st.button("Actualiser", type="secondary", use_container_width=True):
        if 'carte_figee' in st.session_state:
            del st.session_state['carte_figee']
        st.cache_data.clear()
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
    show_trajectories = st.checkbox("Trajectoires", value=True)

with col4:
    if st.session_state.get('carte_figee', False):
        st.markdown('<span class="status-paused">● Carte figée</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-live">● Mode temps réel</span>', unsafe_allow_html=True)

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
@st.cache_data(ttl=60)
def load_all_data():
    """Charge toutes les données nécessaires."""
    weather = get_current_weather()
    flights = get_flights_in_area()
    airport = get_airport_info()
    
    # Qualité de l'air
    air_quality = None
    if HAS_AIR_QUALITY:
        try:
            air_quality = get_current_air_quality()
        except:
            pass
    
    # Impact environnemental
    air_impact = None
    if HAS_AIR_QUALITY and weather:
        try:
            air_impact = calculate_aviation_air_impact(
                len(flights),
                weather.get('wind_speed_10m', 10)
            )
        except:
            pass
    
    return weather, flights, airport, air_quality, air_impact

if st.session_state.get('carte_figee', False):
    if 'cached_data' not in st.session_state:
        st.session_state['cached_data'] = load_all_data()
    weather, flights, airport, air_quality, air_impact = st.session_state['cached_data']
else:
    with st.spinner("Chargement..."):
        weather, flights, airport, air_quality, air_impact = load_all_data()
        st.session_state['cached_data'] = (weather, flights, airport, air_quality, air_impact)

# =============================================================================
# Métriques
# =============================================================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    temp = weather['temperature_2m'] if weather else "N/A"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-blue">{temp}°C</div>
        <div class="stat-label">Température</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    wind = weather['wind_speed_10m'] if weather else "N/A"
    wind_class = "stat-red" if weather and wind > 40 else "stat-yellow" if weather and wind > 25 else ""
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {wind_class}">{wind} km/h</div>
        <div class="stat-label">Vent</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-blue">{len(flights)}</div>
        <div class="stat-label">Vols détectés</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-green">{in_flight}</div>
        <div class="stat-label">En vol</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    if air_quality:
        aqi = air_quality.get('european_aqi', 'N/A')
        aqi_level = air_quality.get('aqi_level', '')
        aqi_color = "stat-green" if aqi and aqi <= 40 else "stat-yellow" if aqi and aqi <= 60 else "stat-red"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value {aqi_color}">{aqi}</div>
            <div class="stat-label">AQI ({aqi_level})</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">-</div>
            <div class="stat-label">AQI</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Carte Interactive
# =============================================================================
col_map, col_info = st.columns([3, 1])

with col_map:
    # Créer la carte
    center_lat = (BEAUVAIS_LAT + BVA_LAT) / 2
    center_lon = (BEAUVAIS_LON + BVA_LON) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB dark_matter'
    )
    
    # Cercle de la zone de surveillance (50km)
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=50000,
        color='#00D4FF',
        fill=True,
        fillOpacity=0.03,
        weight=1,
        dash_array='5,5'
    ).add_to(m)
    
    # Cercle intérieur (20km)
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=20000,
        color='#00D4FF',
        fill=True,
        fillOpacity=0.05,
        weight=1
    ).add_to(m)
    
    # Marqueur aéroport
    airport_popup = f"""
    <div style="font-family: Arial; width: 200px;">
        <h4 style="margin: 0 0 8px 0; color: #1e3a5f;">✈️ {airport['name']}</h4>
        <p style="margin: 4px 0;"><b>IATA:</b> {airport['code_iata']}</p>
        <p style="margin: 4px 0;"><b>ICAO:</b> {airport['code_icao']}</p>
        <p style="margin: 4px 0;"><b>Altitude:</b> {airport['altitude']} m</p>
        <p style="margin: 4px 0;"><b>Vols détectés:</b> {len(flights)}</p>
    </div>
    """
    
    # Icône personnalisée pour l'aéroport
    folium.Marker(
        location=[BVA_LAT, BVA_LON],
        popup=folium.Popup(airport_popup, max_width=220),
        tooltip=f"Aéroport {airport['code_iata']}",
        icon=folium.Icon(color='red', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Marqueur météo
    if weather:
        weather_popup = f"""
        <div style="font-family: Arial; width: 180px;">
            <h4 style="margin: 0 0 8px 0; color: #1e3a5f;">🌤️ Météo Beauvais</h4>
            <p style="margin: 4px 0;"><b>Température:</b> {weather['temperature_2m']}°C</p>
            <p style="margin: 4px 0;"><b>Humidité:</b> {weather['relative_humidity_2m']}%</p>
            <p style="margin: 4px 0;"><b>Vent:</b> {weather['wind_speed_10m']} km/h</p>
            <p style="margin: 4px 0;"><b>Direction:</b> {weather['wind_direction_10m']}°</p>
        </div>
        """
        folium.Marker(
            location=[BEAUVAIS_LAT, BEAUVAIS_LON],
            popup=folium.Popup(weather_popup, max_width=200),
            tooltip="Météo Beauvais",
            icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
        ).add_to(m)
    
    # Coordonnées des aéroports pour les trajectoires
    AIRPORT_COORDS = {
        "LFOB": (49.4544, 2.1106),   # Beauvais
        "BVA": (49.4544, 2.1106),
        "LFPG": (49.0097, 2.5479),   # Paris CDG
        "CDG": (49.0097, 2.5479),
        "LFPO": (48.7262, 2.3597),   # Paris Orly
        "ORY": (48.7262, 2.3597),
        "EGLL": (51.4700, -0.4543),  # Londres Heathrow
        "LHR": (51.4700, -0.4543),
        "LEMD": (40.4719, -3.5626),  # Madrid
        "MAD": (40.4719, -3.5626),
        "LIRF": (41.8003, 12.2389),  # Rome
        "FCO": (41.8003, 12.2389),
        "LEBL": (41.2971, 2.0785),   # Barcelone
        "BCN": (41.2971, 2.0785),
        "LPPT": (38.7813, -9.1359),  # Lisbonne
        "LIS": (38.7813, -9.1359),
        "EIDW": (53.4213, -6.2701),  # Dublin
        "DUB": (53.4213, -6.2701),
        "EHAM": (52.3086, 4.7639),   # Amsterdam
        "AMS": (52.3086, 4.7639),
        "EDDF": (50.0379, 8.5622),   # Francfort
        "FRA": (50.0379, 8.5622),
        "EDDM": (48.3538, 11.7861),  # Munich
        "MUC": (48.3538, 11.7861),
        "EGKK": (51.1481, -0.1903),  # Londres Gatwick
        "LGW": (51.1481, -0.1903),
        "EGGW": (51.8747, -0.3683),  # Londres Luton
        "LTN": (51.8747, -0.3683),
        "EGSS": (51.8850, 0.2350),   # Londres Stansted
        "STN": (51.8850, 0.2350),
        "EPWA": (52.1657, 20.9671),  # Varsovie
        "WAW": (52.1657, 20.9671),
        "LKPR": (50.1008, 14.2600),  # Prague
        "PRG": (50.1008, 14.2600),
        "LHBP": (47.4369, 19.2556),  # Budapest
        "BUD": (47.4369, 19.2556),
        "LGAV": (37.9364, 23.9445),  # Athènes
        "ATH": (37.9364, 23.9445),
        "LIMC": (45.6301, 8.7231),   # Milan
        "MXP": (45.6301, 8.7231),
        "LOWW": (48.1103, 16.5697),  # Vienne
        "VIE": (48.1103, 16.5697),
        "LSZH": (47.4647, 8.5492),   # Zurich
        "ZRH": (47.4647, 8.5492),
        "ESSA": (59.6519, 17.9186),  # Stockholm
        "ARN": (59.6519, 17.9186),
        "EKCH": (55.6180, 12.6508),  # Copenhague
        "CPH": (55.6180, 12.6508),
        "ENGM": (60.1939, 11.1004),  # Oslo
        "OSL": (60.1939, 11.1004),
        "LEPA": (39.5517, 2.7388),   # Palma
        "PMI": (39.5517, 2.7388),
        "GCTS": (28.0445, -16.5725), # Tenerife Sud
        "TFS": (28.0445, -16.5725),
        "LEMG": (36.6749, -4.4991),  # Malaga
        "AGP": (36.6749, -4.4991),
        "LPFR": (37.0144, -7.9659),  # Faro
        "FAO": (37.0144, -7.9659),
        "LFML": (43.4393, 5.2214),   # Marseille
        "MRS": (43.4393, 5.2214),
        "LFMN": (43.6584, 7.2159),   # Nice
        "NCE": (43.6584, 7.2159),
        "LFLL": (45.7256, 5.0811),   # Lyon
        "LYS": (45.7256, 5.0811),
    }
    
    # Avions et trajectoires
    for flight in flights:
        is_ground = flight.get('on_ground', False)
        
        # Couleur selon statut
        if is_ground:
            color = 'gray'
            flight_color = '#6B7280'
        else:
            color = 'green'
            flight_color = '#22C55E'
        
        origin = flight['origin'] if flight['origin'] != 'N/A' else None
        dest = flight['destination'] if flight['destination'] != 'N/A' else None
        
        # Popup détaillé
        flight_popup = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: #1e3a5f;">{flight['callsign']}</h4>
            <p style="margin: 4px 0;"><b>Route:</b> {origin or '???'} → {dest or '???'}</p>
            <p style="margin: 4px 0;"><b>Type:</b> {flight.get('aircraft_type', 'N/A')}</p>
            <p style="margin: 4px 0;"><b>Altitude:</b> {flight['altitude']} ft ({int(flight['altitude'] * 0.3048)} m)</p>
            <p style="margin: 4px 0;"><b>Vitesse:</b> {flight['ground_speed']} kts ({int(flight['ground_speed'] * 1.852)} km/h)</p>
            <p style="margin: 4px 0;"><b>Cap:</b> {flight.get('heading', 'N/A')}°</p>
            <p style="margin: 4px 0;"><b>Compagnie:</b> {flight.get('airline_icao', 'N/A')}</p>
        </div>
        """
        
        # Marqueur avion
        altitude_text = "Au sol" if is_ground else f"Alt: {flight['altitude']} ft"
        tooltip_text = f"{flight['callsign']} - {altitude_text}"
        
        folium.Marker(
            location=[flight['latitude'], flight['longitude']],
            popup=folium.Popup(flight_popup, max_width=220),
            tooltip=tooltip_text,
            icon=folium.Icon(color=color, icon='plane', prefix='fa')
        ).add_to(m)
        
        # Trajectoires (lignes vers/depuis Beauvais)
        if show_trajectories and not is_ground:
            bva_coords = (BVA_LAT, BVA_LON)
            flight_coords = (flight['latitude'], flight['longitude'])
            
            # Ligne origine → position actuelle (si origine connue)
            if origin and origin in AIRPORT_COORDS:
                origin_coords = AIRPORT_COORDS[origin]
                # Ligne de l'origine à la position actuelle
                folium.PolyLine(
                    [origin_coords, flight_coords],
                    color='#00D4FF',
                    weight=2,
                    opacity=0.4,
                    dash_array='5,10'
                ).add_to(m)
            
            # Ligne position actuelle → destination (si destination connue)
            if dest and dest in AIRPORT_COORDS:
                dest_coords = AIRPORT_COORDS[dest]
                # Ligne de la position actuelle à la destination
                folium.PolyLine(
                    [flight_coords, dest_coords],
                    color='#8B5CF6',
                    weight=2,
                    opacity=0.4,
                    dash_array='5,10'
                ).add_to(m)
            
            # Si le vol est lié à Beauvais (arrivée ou départ)
            if origin == 'BVA' or dest == 'BVA':
                # Ligne plus visible pour les vols Beauvais
                if origin == 'BVA':
                    folium.PolyLine(
                        [bva_coords, flight_coords],
                        color='#22C55E',
                        weight=3,
                        opacity=0.7
                    ).add_to(m)
                if dest == 'BVA':
                    folium.PolyLine(
                        [flight_coords, bva_coords],
                        color='#EAB308',
                        weight=3,
                        opacity=0.7
                    ).add_to(m)
    
    # Afficher la carte
    st_folium(m, width=None, height=550, use_container_width=True, returned_objects=[])

with col_info:
    # Légende
    st.markdown("#### Légende")
    st.markdown("""
    <div class="legend-box">
        <div class="legend-item">
            <div class="legend-dot" style="background: #DC2626;"></div>
            Aéroport BVA
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #2563EB;"></div>
            Station météo
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #22C55E;"></div>
            Avion en vol
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #6B7280;"></div>
            Avion au sol
        </div>
        <hr style="margin: 0.5rem 0; border-color: #2D3748;">
        <div class="legend-item">
            <div class="legend-line" style="background: #00D4FF;"></div>
            Trajet depuis origine
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #8B5CF6;"></div>
            Trajet vers destination
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #22C55E;"></div>
            Départ de BVA
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #EAB308;"></div>
            Arrivée à BVA
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Qualité de l'air
    if air_quality:
        st.markdown("#### Qualité de l'air")
        st.markdown(f"""
        <div class="info-panel">
            <p style="margin: 0 0 0.5rem 0;"><b>PM2.5:</b> {air_quality.get('pm2_5', 'N/A')} µg/m³</p>
            <p style="margin: 0 0 0.5rem 0;"><b>PM10:</b> {air_quality.get('pm10', 'N/A')} µg/m³</p>
            <p style="margin: 0 0 0.5rem 0;"><b>NO₂:</b> {air_quality.get('nitrogen_dioxide', 'N/A')} µg/m³</p>
            <p style="margin: 0;"><b>O₃:</b> {air_quality.get('ozone', 'N/A')} µg/m³</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Impact environnemental
    if air_impact:
        st.markdown("#### Impact estimé")
        impact_color = air_impact.get('impact_color', '#94A3B8')
        st.markdown(f"""
        <div class="info-panel">
            <p style="margin: 0 0 0.5rem 0; color: {impact_color}; font-weight: 600;">
                {air_impact.get('impact_level', 'N/A')} ({air_impact.get('impact_score', 0)}/100)
            </p>
            <p style="margin: 0 0 0.3rem 0; font-size: 0.8rem;"><b>CO₂:</b> ~{air_impact.get('co2_tonnes', 0)} t</p>
            <p style="margin: 0 0 0.3rem 0; font-size: 0.8rem;"><b>NOx:</b> ~{air_impact.get('nox_kg', 0)} kg</p>
            <p style="margin: 0; font-size: 0.8rem;"><b>PM:</b> ~{air_impact.get('pm_kg', 0)} kg</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; color: #64748B;">
                Dispersion: {air_impact.get('dispersion', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Liste des vols
# =============================================================================
with st.expander("Liste des vols détectés", expanded=False):
    if flights:
        # Trier: en vol d'abord, puis par altitude décroissante
        sorted_flights = sorted(flights, key=lambda x: (x.get('on_ground', False), -x.get('altitude', 0)))
        
        for flight in sorted_flights:
            status = "Au sol" if flight.get('on_ground', False) else "En vol"
            status_color = "#6B7280" if flight.get('on_ground', False) else "#22C55E"
            origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
            dest = flight['destination'] if flight['destination'] != 'N/A' else '???'
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; 
                        padding: 0.5rem; background: #1A1F2E; border-radius: 4px; margin-bottom: 0.5rem;
                        border-left: 3px solid {status_color};">
                <div>
                    <span style="font-weight: 600; color: #FAFAFA;">{flight['callsign']}</span>
                    <span style="color: #64748B;"> • {origin} → {dest}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: {status_color}; font-size: 0.8rem;">{status}</span>
                    <span style="color: #94A3B8; font-size: 0.75rem;"> • {flight['altitude']} ft</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("Aucun vol détecté dans la zone")

# =============================================================================
# Footer
# =============================================================================
st.markdown("""
<div class="footer">
    Carte : OpenStreetMap / CartoDB • Données : FlightRadar24, OpenMeteo<br>
    Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)
