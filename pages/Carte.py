"""
Page Carte — Surveillance temps réel de l'aéroport Paris-Beauvais (BVA/LFOB)
Visualisation du trafic aérien et de la qualité de l'air
"""

import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime

# Imports des modules API
from api.weather import get_current_weather, BEAUVAIS_LAT, BEAUVAIS_LON
from api.flights import get_flights_in_area, get_airport_info, BVA_LAT, BVA_LON
from api.air_quality import get_current_air_quality, calculate_aviation_air_impact

# Configuration
st.set_page_config(
    page_title="BVA Monitor | Carte",
    page_icon="",
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
    
    .info-box {
        background: rgba(0, 212, 255, 0.1);
        border-left: 3px solid #00D4FF;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        font-size: 0.85rem;
        color: #7DD3FC;
    }
    
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
    
    .aqi-indicator {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 0.5rem;
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
    <p>Surveillance en temps réel du trafic aérien et de la qualité de l'air</p>
</div>
""", unsafe_allow_html=True)

# Explication de la page
st.markdown("""
<div class="info-box">
    <b>💡 À quoi sert cette carte ?</b><br><br>
    Cette carte affiche en temps réel :<br>
    • <b>Tous les avions</b> dans un rayon de 50 km autour de Beauvais (pas seulement ceux de BVA)<br>
    • Les <b>zones de qualité de l'air</b> colorées selon l'AQI européen<br>
    • L'<b>impact environnemental estimé</b> du trafic aérien<br>
    • Les <b>trajectoires</b> des vols vers/depuis Beauvais<br><br>
    <b>🎯 Objectif :</b> Visualiser la corrélation entre le trafic aérien et la qualité de l'air locale.
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Contrôles
# =============================================================================
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

with col1:
    if st.button("🔄 Actualiser", type="primary", use_container_width=True):
        if 'carte_figee' in st.session_state:
            del st.session_state['carte_figee']
        st.rerun()

with col2:
    if 'carte_figee' not in st.session_state:
        st.session_state['carte_figee'] = False
    
    if st.session_state['carte_figee']:
        if st.button("▶️ Reprendre", type="secondary", use_container_width=True):
            st.session_state['carte_figee'] = False
            st.rerun()
    else:
        if st.button("⏸️ Figer", type="secondary", use_container_width=True):
            st.session_state['carte_figee'] = True
            st.rerun()

with col3:
    show_aqi_zones = st.checkbox("Zones AQI", value=True)
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
# Calcul qualité air et impact
# =============================================================================
wind_speed = weather['wind_speed_10m'] if weather else 10
impact = calculate_aviation_air_impact(len(flights), wind_speed)

# Déterminer couleur AQI pour la carte
if air_quality:
    aqi = air_quality.get('european_aqi', 50)
    if aqi <= 20:
        aqi_color = '#22C55E'  # Vert
        aqi_opacity = 0.15
    elif aqi <= 40:
        aqi_color = '#84CC16'  # Vert clair
        aqi_opacity = 0.15
    elif aqi <= 60:
        aqi_color = '#EAB308'  # Jaune
        aqi_opacity = 0.2
    elif aqi <= 80:
        aqi_color = '#F97316'  # Orange
        aqi_opacity = 0.25
    else:
        aqi_color = '#EF4444'  # Rouge
        aqi_opacity = 0.3
else:
    aqi = 50
    aqi_color = '#64748B'
    aqi_opacity = 0.1

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
    if air_quality:
        aqi_val = air_quality.get('european_aqi', 0)
        aqi_level = air_quality.get('aqi_level', 'N/A')
        if aqi_val <= 40:
            color = "stat-green"
        elif aqi_val <= 60:
            color = "stat-yellow"
        else:
            color = "stat-red"
    else:
        aqi_val = "N/A"
        aqi_level = "N/A"
        color = ""
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{aqi_val}</div>
        <div class="stat-label">AQI ({aqi_level})</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    impact_score = impact['impact_score']
    impact_level = impact['impact_level']
    if impact_score <= 30:
        color = "stat-green"
    elif impact_score <= 60:
        color = "stat-yellow"
    else:
        color = "stat-red"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value {color}">{impact_score}</div>
        <div class="stat-label">Impact ({impact_level})</div>
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
    
    # =========================================================================
    # ZONE DE QUALITÉ DE L'AIR (cercle coloré)
    # =========================================================================
    if show_aqi_zones:
        # Zone principale 20km - couleur selon AQI
        folium.Circle(
            location=[BVA_LAT, BVA_LON],
            radius=20000,
            color=aqi_color,
            fill=True,
            fillOpacity=aqi_opacity,
            weight=2,
            popup=f"Zone qualité air<br>AQI: {aqi} ({air_quality.get('aqi_level', 'N/A') if air_quality else 'N/A'})"
        ).add_to(m)
        
        # Zone impact direct 5km (plus dense)
        folium.Circle(
            location=[BVA_LAT, BVA_LON],
            radius=5000,
            color=impact['impact_color'],
            fill=True,
            fillOpacity=0.2,
            weight=2,
            popup=f"Zone impact direct<br>Score: {impact['impact_score']}/100"
        ).add_to(m)
    
    # Zone de surveillance (50 km) - contour pointillé
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=50000,
        color='#00D4FF',
        fill=False,
        weight=2,
        dash_array='10, 5',
        popup="Zone de surveillance (50 km)"
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
        
        origin = flight['origin'] if flight['origin'] != 'N/A' else '---'
        dest = flight['destination'] if flight['destination'] != 'N/A' else '---'
        
        # Déterminer si lié à BVA
        is_bva_arrival = dest in ['BVA', 'LFOB']
        is_bva_departure = origin in ['BVA', 'LFOB']
        
        if is_bva_arrival:
            color = 'green'
            category = "Arrivée BVA"
        elif is_bva_departure:
            color = 'orange'
            category = "Départ BVA"
        elif is_ground:
            color = 'gray'
            category = "Au sol"
        else:
            color = 'lightblue'
            category = "Transit"
        
        # Popup avion
        flight_popup = f"""
        <div style="font-family: Arial; width: 200px; color: #333;">
            <h4 style="margin: 0 0 8px 0; color: #1e3a5f; border-bottom: 2px solid #00D4FF; padding-bottom: 5px;">
                ✈️ {flight['callsign']}
            </h4>
            <p style="margin: 4px 0;"><b>Catégorie:</b> {category}</p>
            <p style="margin: 4px 0;"><b>Route:</b> {origin} → {dest}</p>
            <p style="margin: 4px 0;"><b>Type:</b> {flight['aircraft_type']}</p>
            <hr style="margin: 8px 0;">
            <p style="margin: 4px 0;"><b>Altitude:</b> {flight['altitude']} ft</p>
            <p style="margin: 4px 0;"><b>Vitesse:</b> {flight['ground_speed']} kts</p>
            <p style="margin: 4px 0;"><b>Cap:</b> {flight['heading']}°</p>
        </div>
        """
        
        # Marqueur avion
        folium.Marker(
            location=[flight['latitude'], flight['longitude']],
            popup=folium.Popup(flight_popup, max_width=220),
            tooltip=f"{flight['callsign']} - {category}",
            icon=folium.Icon(color=color, icon='plane', prefix='fa')
        ).add_to(m)
        
        # Trajectoires vers/depuis Beauvais
        if show_trajectories and not is_ground:
            flight_coords = (flight['latitude'], flight['longitude'])
            bva_coords = (BVA_LAT, BVA_LON)
            
            if is_bva_arrival:
                folium.PolyLine(
                    [flight_coords, bva_coords],
                    color='#22C55E',
                    weight=2,
                    opacity=0.7,
                    dash_array='5, 5',
                    tooltip=f"{flight['callsign']} → BVA"
                ).add_to(m)
            elif is_bva_departure:
                folium.PolyLine(
                    [bva_coords, flight_coords],
                    color='#F97316',
                    weight=2,
                    opacity=0.7,
                    dash_array='5, 5',
                    tooltip=f"BVA → {flight['callsign']}"
                ).add_to(m)
    
    # Afficher la carte
    st_folium(m, width=None, height=550, use_container_width=True, returned_objects=[])

with col_info:
    # Légende
    st.markdown("#### Légende")
    st.markdown(f"""
    <div class="legend-box">
        <div class="legend-item">
            <div class="legend-dot" style="background: #CC0000;"></div>
            Aéroport BVA
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #0066CC;"></div>
            Station météo
        </div>
        <hr style="border: none; border-top: 1px solid #2D3748; margin: 0.5rem 0;">
        <div class="legend-item">
            <div class="legend-dot" style="background: #22C55E;"></div>
            Arrivée BVA
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #F97316;"></div>
            Départ BVA
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #7DD3FC;"></div>
            Transit (survol)
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background: #6B7280;"></div>
            Au sol
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Zones de qualité de l'air
    st.markdown("#### Zones colorées")
    st.markdown(f"""
    <div class="legend-box">
        <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.5rem;">
            <b>Zone qualité air (20 km)</b>
        </div>
        <div class="aqi-indicator" style="background: {aqi_color}; opacity: 0.8;">
            <span style="color: #FFF; font-weight: 600;">AQI: {aqi}</span>
        </div>
        <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.5rem;">
            🟢 0-40 Bon<br>
            🟡 41-60 Modéré<br>
            🟠 61-80 Médiocre<br>
            🔴 81+ Mauvais
        </div>
        <hr style="border: none; border-top: 1px solid #2D3748; margin: 0.75rem 0;">
        <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.5rem;">
            <b>Zone impact (5 km)</b>
        </div>
        <div class="aqi-indicator" style="background: {impact['impact_color']}; opacity: 0.8;">
            <span style="color: #FFF; font-weight: 600;">{impact['impact_level']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Détails pollution
    st.markdown("#### Polluants")
    if air_quality:
        pm25 = air_quality.get('pm2_5', 0)
        pm10 = air_quality.get('pm10', 0)
        no2 = air_quality.get('nitrogen_dioxide', 0)
        
        st.markdown(f"""
        <div class="legend-box">
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem;">
                <b>PM2.5:</b> {pm25:.1f} µg/m³ {'⚠️' if pm25 > 15 else '✅'}
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem;">
                <b>PM10:</b> {pm10:.1f} µg/m³ {'⚠️' if pm10 > 45 else '✅'}
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
                <b>NO₂:</b> {no2:.1f} µg/m³ {'⚠️' if no2 > 25 else '✅'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption("Non disponible")

st.divider()

# =============================================================================
# Liste des vols par catégorie
# =============================================================================
st.markdown("#### Détail des vols détectés")

if flights:
    # Séparer par catégorie
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
                <div class="flight-item" style="border-left-color: #22C55E;">
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
            if len(transit) > 5:
                st.caption(f"... et {len(transit) - 5} autres")
        else:
            st.caption("Aucun transit")
    
    # Tableau complet
    with st.expander("📋 Voir tous les vols (tableau)"):
        import pandas as pd
        df = pd.DataFrame(flights)
        
        # Ajouter catégorie
        def get_category(row):
            if row['destination'] in ['BVA', 'LFOB']:
                return '🛬 Arrivée BVA'
            elif row['origin'] in ['BVA', 'LFOB']:
                return '🛫 Départ BVA'
            else:
                return '✈️ Transit'
        
        df['Catégorie'] = df.apply(get_category, axis=1)
        cols_to_show = ['Catégorie', 'callsign', 'airline_icao', 'aircraft_type', 'origin', 'destination', 'altitude', 'ground_speed']
        df_display = df[[c for c in cols_to_show if c in df.columns]].copy()
        df_display.columns = ['Catégorie', 'Callsign', 'Compagnie', 'Type', 'Origine', 'Destination', 'Altitude (ft)', 'Vitesse (kts)']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

else:
    st.info("🔍 Aucun vol détecté dans la zone de surveillance (50 km autour de BVA)")

# =============================================================================
# Footer
# =============================================================================
st.markdown(f"""
<div class="footer">
    Carte : OpenStreetMap / CartoDB Dark Matter • Données : FlightRadar24 & OpenMeteo<br>
    Zone de surveillance : 50 km autour de Paris-Beauvais (BVA) | Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""", unsafe_allow_html=True)