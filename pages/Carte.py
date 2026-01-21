"""
Page Carte — Surveillance de l'aéroport Paris-Beauvais (BVA/LFOB)
Version simplifiée centrée sur Beauvais
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime

# Imports des modules API
from api.weather import get_current_weather, BEAUVAIS_LAT, BEAUVAIS_LON
from api.flights import get_flights_in_area, get_airport_info, BVA_LAT, BVA_LON
from api.air_quality import get_current_air_quality, calculate_aviation_air_impact

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
        padding: 0.4rem 0;
        font-size: 0.85rem;
        color: #94A3B8;
    }
    
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    
    .legend-line {
        width: 20px;
        height: 3px;
        border-radius: 2px;
    }
    
    .info-card {
        background: #1A1F2E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        margin-bottom: 1rem;
    }
    
    .flight-item {
        padding: 0.5rem;
        border-left: 3px solid #00D4FF;
        margin-bottom: 0.5rem;
        background: rgba(0, 212, 255, 0.05);
        border-radius: 0 6px 6px 0;
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
    <h1>🗺️ Carte Interactive — Paris-Beauvais (BVA)</h1>
    <p>Surveillance en temps réel de l'aéroport et du trafic aérien environnant</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Contrôles
# =============================================================================
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

with col1:
    if st.button("🔄 Actualiser", type="secondary", use_container_width=True):
        if 'carte_figee' in st.session_state:
            del st.session_state['carte_figee']
        st.rerun()

with col2:
    if 'carte_figee' not in st.session_state:
        st.session_state['carte_figee'] = False
    
    if st.session_state['carte_figee']:
        if st.button("▶️ Reprendre", type="primary", use_container_width=True):
            st.session_state['carte_figee'] = False
            st.rerun()
    else:
        if st.button("⏸️ Figer", type="secondary", use_container_width=True):
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
if st.session_state.get('carte_figee', False):
    if 'cached_weather' not in st.session_state:
        weather = get_current_weather()
        flights = get_flights_in_area()
        air_quality = get_current_air_quality()
        st.session_state['cached_weather'] = weather
        st.session_state['cached_flights'] = flights
        st.session_state['cached_air_quality'] = air_quality
    else:
        weather = st.session_state['cached_weather']
        flights = st.session_state['cached_flights']
        air_quality = st.session_state.get('cached_air_quality')
else:
    with st.spinner("Chargement des données..."):
        weather = get_current_weather()
        flights = get_flights_in_area()
        air_quality = get_current_air_quality()
        st.session_state['cached_weather'] = weather
        st.session_state['cached_flights'] = flights
        st.session_state['cached_air_quality'] = air_quality

airport = get_airport_info()

# =============================================================================
# Métriques principales
# =============================================================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    temp = weather['temperature_2m'] if weather else "N/A"
    color = "stat-blue"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{temp}°C</div>
        <div class="stat-label">Température</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    wind = weather['wind_speed_10m'] if weather else 0
    color = "stat-red" if wind > 40 else "stat-yellow" if wind > 25 else ""
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{wind} km/h</div>
        <div class="stat-label">Vent</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "stat-blue"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{len(flights)}</div>
        <div class="stat-label">Vols détectés</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    color = "stat-green"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{in_flight}</div>
        <div class="stat-label">En vol</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    if air_quality:
        aqi = air_quality.get('european_aqi', 0)
        aqi_level = air_quality.get('aqi_level', 'N/A')
        if aqi <= 40:
            color = "stat-green"
        elif aqi <= 60:
            color = "stat-yellow"
        else:
            color = "stat-red"
    else:
        aqi = "N/A"
        aqi_level = "N/A"
        color = ""
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{aqi}</div>
        <div class="stat-label">AQI ({aqi_level})</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Carte et informations
# =============================================================================
col_map, col_info = st.columns([3, 1])

with col_map:
    # Créer la carte centrée sur Beauvais
    m = folium.Map(
        location=[BVA_LAT, BVA_LON],
        zoom_start=10,
        tiles='CartoDB dark_matter'
    )
    
    # Zone de surveillance (50 km)
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=50000,
        color='#00D4FF',
        fill=True,
        fillOpacity=0.05,
        weight=2,
        dash_array='10, 5'
    ).add_to(m)
    
    # Zone proche aéroport (10 km)
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=10000,
        color='#22C55E',
        fill=True,
        fillOpacity=0.03,
        weight=1
    ).add_to(m)
    
    # Marqueur aéroport Beauvais
    airport_popup = f"""
    <div style="font-family: Arial; width: 200px; color: #333;">
        <h4 style="margin: 0 0 8px 0; color: #1e3a5f; border-bottom: 2px solid #00D4FF; padding-bottom: 5px;">
            ✈️ {airport['name']}
        </h4>
        <p style="margin: 4px 0;"><b>IATA:</b> {airport['code_iata']}</p>
        <p style="margin: 4px 0;"><b>ICAO:</b> {airport['code_icao']}</p>
        <p style="margin: 4px 0;"><b>Altitude:</b> {airport['altitude']} m</p>
        <p style="margin: 4px 0;"><b>Coordonnées:</b> {BVA_LAT}°N, {BVA_LON}°E</p>
        <hr style="margin: 8px 0;">
        <p style="margin: 4px 0;"><b>Compagnies:</b></p>
        <p style="margin: 4px 0; font-size: 0.9em;">{', '.join(airport['principales_compagnies'])}</p>
    </div>
    """
    folium.Marker(
        location=[BVA_LAT, BVA_LON],
        popup=folium.Popup(airport_popup, max_width=220),
        tooltip="🛫 Aéroport Paris-Beauvais (BVA)",
        icon=folium.Icon(color='red', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Marqueur station météo (centre-ville Beauvais)
    if weather:
        weather_popup = f"""
        <div style="font-family: Arial; width: 180px; color: #333;">
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
            tooltip="🌤️ Station météo Beauvais",
            icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
        ).add_to(m)
    
    # Ajouter les avions
    for flight in flights:
        is_ground = flight.get('on_ground', False)
        color = 'gray' if is_ground else 'green'
        
        origin = flight['origin'] if flight['origin'] != 'N/A' else '---'
        dest = flight['destination'] if flight['destination'] != 'N/A' else '---'
        
        # Popup avion
        flight_popup = f"""
        <div style="font-family: Arial; width: 200px; color: #333;">
            <h4 style="margin: 0 0 8px 0; color: #1e3a5f; border-bottom: 2px solid #00D4FF; padding-bottom: 5px;">
                ✈️ {flight['callsign']}
            </h4>
            <p style="margin: 4px 0;"><b>Route:</b> {origin} → {dest}</p>
            <p style="margin: 4px 0;"><b>Type:</b> {flight['aircraft_type']}</p>
            <p style="margin: 4px 0;"><b>Compagnie:</b> {flight.get('airline_icao', 'N/A')}</p>
            <hr style="margin: 8px 0;">
            <p style="margin: 4px 0;"><b>Altitude:</b> {flight['altitude']} ft ({int(flight['altitude'] * 0.3048)} m)</p>
            <p style="margin: 4px 0;"><b>Vitesse:</b> {flight['ground_speed']} kts ({int(flight['ground_speed'] * 1.852)} km/h)</p>
            <p style="margin: 4px 0;"><b>Cap:</b> {flight['heading']}°</p>
            <p style="margin: 4px 0;"><b>Statut:</b> {'🅿️ Au sol' if is_ground else '🛫 En vol'}</p>
        </div>
        """
        
        # Tooltip
        altitude_text = "Au sol" if is_ground else f"Alt: {flight['altitude']} ft"
        tooltip_text = f"{flight['callsign']} - {altitude_text}"
        
        # Marqueur avion
        folium.Marker(
            location=[flight['latitude'], flight['longitude']],
            popup=folium.Popup(flight_popup, max_width=220),
            tooltip=tooltip_text,
            icon=folium.Icon(color=color, icon='plane', prefix='fa')
        ).add_to(m)
        
        # Trajectoires vers/depuis Beauvais
        if show_trajectories and not is_ground:
            flight_coords = (flight['latitude'], flight['longitude'])
            bva_coords = (BVA_LAT, BVA_LON)
            
            # Déterminer si arrivée ou départ de BVA
            is_arriving = dest == 'BVA' or dest == 'LFOB'
            is_departing = origin == 'BVA' or origin == 'LFOB'
            
            if is_arriving:
                # Ligne verte pointillée : arrivée à BVA
                folium.PolyLine(
                    [flight_coords, bva_coords],
                    color='#22C55E',
                    weight=2,
                    opacity=0.7,
                    dash_array='5, 5',
                    tooltip=f"{flight['callsign']} → BVA"
                ).add_to(m)
            elif is_departing:
                # Ligne orange pointillée : départ de BVA
                folium.PolyLine(
                    [bva_coords, flight_coords],
                    color='#F97316',
                    weight=2,
                    opacity=0.7,
                    dash_array='5, 5',
                    tooltip=f"BVA → {flight['callsign']}"
                ).add_to(m)
            else:
                # Avion de passage (ni arrivée ni départ BVA) - ligne grise fine
                folium.PolyLine(
                    [flight_coords, bva_coords],
                    color='#64748B',
                    weight=1,
                    opacity=0.3,
                    dash_array='3, 6'
                ).add_to(m)
    
    # Afficher la carte
    st_folium(m, width=None, height=550, use_container_width=True, returned_objects=[])

with col_info:
    # Légende
    st.markdown("#### Légende")
    st.markdown("""
    <div class="legend-box">
        <div class="legend-item">
            <div class="legend-dot" style="background: #CC0000;"></div>
            Aéroport BVA
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #0066CC;"></div>
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
        <hr style="border: none; border-top: 1px solid #2D3748; margin: 0.5rem 0;">
        <div class="legend-item">
            <div class="legend-line" style="background: #22C55E;"></div>
            Arrivée à BVA
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #F97316;"></div>
            Départ de BVA
        </div>
        <div class="legend-item">
            <div class="legend-line" style="background: #64748B; opacity: 0.5;"></div>
            Passage (transit)
        </div>
        <hr style="border: none; border-top: 1px solid #2D3748; margin: 0.5rem 0;">
        <div class="legend-item" style="font-size: 0.75rem;">
            <div style="width: 20px; height: 20px; border: 2px dashed #00D4FF; border-radius: 50%;"></div>
            Zone 50 km
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Qualité de l'air
    st.markdown("#### Qualité de l'air")
    if air_quality:
        pm25 = air_quality.get('pm2_5', 0)
        pm10 = air_quality.get('pm10', 0)
        no2 = air_quality.get('nitrogen_dioxide', 0)
        o3 = air_quality.get('ozone', 0)
        
        st.markdown(f"""
        <div class="legend-box">
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem;">
                <b>PM2.5:</b> {pm25:.1f} µg/m³
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem;">
                <b>PM10:</b> {pm10:.1f} µg/m³
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem;">
                <b>NO₂:</b> {no2:.1f} µg/m³
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
                <b>O₃:</b> {o3:.1f} µg/m³
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption("Non disponible")
    
    st.markdown("")
    
    # Impact estimé
    st.markdown("#### Impact estimé")
    wind_speed = weather['wind_speed_10m'] if weather else 10
    impact = calculate_aviation_air_impact(len(flights), wind_speed)
    
    impact_color = impact['impact_color']
    st.markdown(f"""
    <div class="legend-box">
        <div style="font-size: 0.85rem; color: {impact_color}; font-weight: 600; margin-bottom: 0.5rem;">
            {impact['impact_level']} ({impact['impact_score']}/100)
        </div>
        <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.3rem;">
            CO₂: {impact['co2_tonnes']:.1f} t
        </div>
        <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.3rem;">
            NOx: {impact['nox_kg']:.1f} kg
        </div>
        <div style="font-size: 0.8rem; color: #94A3B8;">
            Dispersion: {impact['dispersion']}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Liste des vols
# =============================================================================
st.markdown("#### Liste des vols détectés")

if flights:
    # Séparer arrivées/départs/transit
    arrivals = [f for f in flights if f['destination'] in ['BVA', 'LFOB']]
    departures = [f for f in flights if f['origin'] in ['BVA', 'LFOB']]
    transit = [f for f in flights if f not in arrivals and f not in departures]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**🛬 Arrivées BVA ({len(arrivals)})**")
        if arrivals:
            for f in arrivals[:5]:
                status = "Au sol" if f.get('on_ground') else f"{f['altitude']} ft"
                st.markdown(f"""
                <div class="flight-item">
                    <strong style="color: #22C55E;">{f['callsign']}</strong>
                    <span style="color: #64748B;"> depuis {f['origin']}</span><br>
                    <span style="font-size: 0.8rem; color: #94A3B8;">{f['aircraft_type']} • {status}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Aucune arrivée en cours")
    
    with col2:
        st.markdown(f"**🛫 Départs BVA ({len(departures)})**")
        if departures:
            for f in departures[:5]:
                status = "Au sol" if f.get('on_ground') else f"{f['altitude']} ft"
                st.markdown(f"""
                <div class="flight-item" style="border-left-color: #F97316;">
                    <strong style="color: #F97316;">{f['callsign']}</strong>
                    <span style="color: #64748B;"> vers {f['destination']}</span><br>
                    <span style="font-size: 0.8rem; color: #94A3B8;">{f['aircraft_type']} • {status}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Aucun départ en cours")
    
    with col3:
        st.markdown(f"**✈️ Transit ({len(transit)})**")
        if transit:
            for f in transit[:5]:
                status = "Au sol" if f.get('on_ground') else f"{f['altitude']} ft"
                origin = f['origin'] if f['origin'] != 'N/A' else '?'
                dest = f['destination'] if f['destination'] != 'N/A' else '?'
                st.markdown(f"""
                <div class="flight-item" style="border-left-color: #64748B;">
                    <strong style="color: #94A3B8;">{f['callsign']}</strong>
                    <span style="color: #64748B;"> {origin}→{dest}</span><br>
                    <span style="font-size: 0.8rem; color: #94A3B8;">{f['aircraft_type']} • {status}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Aucun transit")
    
    # Tableau complet en expander
    with st.expander("📋 Voir tous les vols (tableau)"):
        import pandas as pd
        df = pd.DataFrame(flights)
        cols_to_show = ['callsign', 'airline_icao', 'aircraft_type', 'origin', 'destination', 'altitude', 'ground_speed', 'on_ground']
        df_display = df[[c for c in cols_to_show if c in df.columns]].copy()
        df_display.columns = ['Callsign', 'Compagnie', 'Type', 'Origine', 'Destination', 'Altitude (ft)', 'Vitesse (kts)', 'Au sol']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

else:
    st.info("🔍 Aucun vol détecté dans la zone de surveillance (50 km autour de BVA)")

# =============================================================================
# Footer
# =============================================================================
st.markdown(f"""
<div class="footer">
    Carte : OpenStreetMap / CartoDB Dark Matter • Données : FlightRadar24 & OpenMeteo<br>
    Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')} • Zone : 50 km autour de Paris-Beauvais (BVA)
</div>
""", unsafe_allow_html=True)
