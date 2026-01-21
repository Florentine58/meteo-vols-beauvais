"""
Page Carte Historique — Trajectoires des vols BVA et corrélation météo
Visualise comment la météo influence les trajectoires d'approche/départ

Projet Mineure Numérique B2 — 2025
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, timezone
import numpy as np

# Imports des modules API
from api.opensky_v2 import (
    get_beauvais_flights_with_tracks,
    get_historical_flights_by_day,
    get_airport_coords,
    estimate_flight_path,
    test_connection,
    BVA_LAT, BVA_LON, AIRPORT_ICAO
)
from api.weather import get_historical_weather, get_current_weather

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Carte Historique",
    page_icon="🗺️",
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
    .stat-purple { color: #A855F7; }
    .stat-orange { color: #F97316; }
    
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
    
    .legend-line {
        width: 25px;
        height: 4px;
        border-radius: 2px;
    }
    
    .flight-card {
        background: #1A1F2E;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #00D4FF;
    }
    
    .alert-box {
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    .alert-success { background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22C55E; color: #86EFAC; }
    .alert-warning { background: rgba(234, 179, 8, 0.1); border-left: 3px solid #EAB308; color: #FDE047; }
    .alert-danger { background: rgba(239, 68, 68, 0.1); border-left: 3px solid #EF4444; color: #FCA5A5; }
    .alert-info { background: rgba(0, 212, 255, 0.1); border-left: 3px solid #00D4FF; color: #7DD3FC; }
    
    .weather-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .weather-good { background: rgba(34, 197, 94, 0.2); color: #86EFAC; }
    .weather-moderate { background: rgba(234, 179, 8, 0.2); color: #FDE047; }
    .weather-bad { background: rgba(239, 68, 68, 0.2); color: #FCA5A5; }
    
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
    <h1>🗺️ Carte Historique des Trajectoires — Paris-Beauvais</h1>
    <p>Analyse de l'impact météorologique sur les trajectoires d'approche et de départ</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Test de connexion OpenSky
# =============================================================================
conn_status = test_connection()

if conn_status['status'] == 'error':
    st.markdown(f"""
    <div class="alert-box alert-danger">
        ❌ {conn_status['message']}<br>
        <small>Vérifie tes credentials OpenSky dans le fichier .env</small>
    </div>
    """, unsafe_allow_html=True)
    st.stop()
elif conn_status['status'] == 'warning':
    st.markdown(f"""
    <div class="alert-box alert-warning">
        ⚠️ {conn_status['message']}<br>
        <small>Les trajectoires détaillées nécessitent une authentification</small>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alert-box alert-success">
        ✅ {conn_status['message']} — Trajectoires disponibles
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Contrôles
# =============================================================================
col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

with col1:
    hours_choice = st.selectbox(
        "Période",
        options=[24, 48, 72, 168],
        format_func=lambda x: f"{x}h" if x < 168 else "7 jours",
        index=1
    )

with col2:
    max_tracks = st.selectbox(
        "Max trajectoires",
        options=[10, 20, 30, 50],
        index=1,
        help="Limite pour économiser les appels API"
    )

with col3:
    color_mode = st.selectbox(
        "Coloration",
        options=["type", "weather", "time"],
        format_func=lambda x: {"type": "Arrivée/Départ", "weather": "Conditions météo", "time": "Heure du vol"}[x],
        index=0
    )

with col4:
    if st.button("🔄 Charger les trajectoires", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
@st.cache_data(ttl=600, show_spinner=False)
def load_flight_data(hours, max_tracks):
    """Charge les vols BVA avec trajectoires (cache 10 min)"""
    return get_beauvais_flights_with_tracks(hours=hours, max_tracks=max_tracks)

@st.cache_data(ttl=3600, show_spinner=False)
def load_weather_data(days):
    """Charge l'historique météo (cache 1h)"""
    return get_historical_weather(days=days)


with st.spinner(f"📡 Récupération des vols BVA ({hours_choice}h) et trajectoires..."):
    flight_data = load_flight_data(hours_choice, max_tracks)
    weather_data = load_weather_data(days=max(7, hours_choice // 24))

# =============================================================================
# Métriques
# =============================================================================
col1, col2, col3, col4, col5 = st.columns(5)

total_flights = flight_data['total_flights']
arrivals_count = len(flight_data['arrivals'])
departures_count = len(flight_data['departures'])
tracks_count = flight_data['tracks_retrieved']

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-blue">{total_flights}</div>
        <div class="stat-label">Vols total</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-green">{arrivals_count}</div>
        <div class="stat-label">Arrivées BVA</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-orange">{departures_count}</div>
        <div class="stat-label">Départs BVA</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-purple">{tracks_count}</div>
        <div class="stat-label">Trajectoires</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    # Météo moyenne de la période
    if weather_data:
        avg_wind = np.mean(weather_data['wind_speed_10m_max'][:hours_choice//24] or [0])
        color = "stat-red" if avg_wind > 40 else "stat-yellow" if avg_wind > 25 else "stat-green"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value {color}">{avg_wind:.0f}</div>
            <div class="stat-label">Vent moy (km/h)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">N/A</div>
            <div class="stat-label">Vent moy</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Carte avec trajectoires
# =============================================================================
col_map, col_info = st.columns([3, 1])

with col_map:
    st.markdown("### 🗺️ Carte des trajectoires")
    
    # Créer la carte
    m = folium.Map(
        location=[BVA_LAT, BVA_LON],
        zoom_start=7,
        tiles='CartoDB dark_matter'
    )
    
    # Zone aéroport
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=15000,  # 15 km
        color='#00D4FF',
        fill=True,
        fillOpacity=0.1,
        weight=2
    ).add_to(m)
    
    # Marqueur aéroport
    folium.Marker(
        location=[BVA_LAT, BVA_LON],
        popup="✈️ Paris-Beauvais (LFOB)",
        tooltip="🛫 BVA - Beauvais",
        icon=folium.Icon(color='red', icon='plane', prefix='fa')
    ).add_to(m)
    
    # Fonction pour obtenir la couleur selon le mode
    def get_track_color(flight, weather_score=None):
        if color_mode == "type":
            return '#22C55E' if flight.get('is_arrival') else '#F97316'
        elif color_mode == "weather":
            if weather_score is None:
                return '#64748B'
            if weather_score >= 80:
                return '#22C55E'
            elif weather_score >= 50:
                return '#EAB308'
            else:
                return '#EF4444'
        else:  # time
            hour = None
            if flight.get('last_seen'):
                hour = flight['last_seen'].hour
            elif flight.get('first_seen'):
                hour = flight['first_seen'].hour
            
            if hour is None:
                return '#64748B'
            # Nuit = bleu, jour = jaune
            if 6 <= hour < 12:
                return '#FCD34D'  # Matin - jaune
            elif 12 <= hour < 18:
                return '#F97316'  # Après-midi - orange
            elif 18 <= hour < 22:
                return '#A855F7'  # Soir - violet
            else:
                return '#3B82F6'  # Nuit - bleu
    
    # Calculer un score météo simple pour chaque jour
    weather_scores = {}
    if weather_data:
        for i, date in enumerate(weather_data['time'][:14]):
            wind = weather_data['wind_speed_10m_max'][i] or 0
            precip = weather_data['precipitation_sum'][i] or 0
            score = 100
            if wind > 50: score -= 40
            elif wind > 35: score -= 25
            elif wind > 25: score -= 10
            if precip > 20: score -= 25
            elif precip > 10: score -= 15
            weather_scores[date] = max(0, score)
    
    # Tracer les trajectoires
    all_flights = flight_data['arrivals'] + flight_data['departures']
    flights_with_track = 0
    flights_estimated = 0
    
    for flight in all_flights:
        # Déterminer le score météo du jour du vol
        weather_score = None
        flight_date = flight.get('last_seen') or flight.get('first_seen')
        if flight_date:
            day_str = flight_date.strftime("%Y-%m-%d")
            weather_score = weather_scores.get(day_str, 50)
        
        color = get_track_color(flight, weather_score)
        
        # Trajectoire réelle disponible ?
        if flight.get('has_track') and flight.get('track'):
            waypoints = flight['track']['waypoints']
            coords = [[wp['lat'], wp['lon']] for wp in waypoints if wp.get('lat') and wp.get('lon')]
            
            if len(coords) >= 2:
                # Tracer la vraie trajectoire
                folium.PolyLine(
                    coords,
                    color=color,
                    weight=3,
                    opacity=0.8,
                    tooltip=f"✈️ {flight['callsign']} | {flight['origin']} → {flight['destination']} (réel)"
                ).add_to(m)
                
                # Marqueur au point de départ/arrivée
                if flight.get('is_arrival'):
                    folium.CircleMarker(
                        location=coords[0],
                        radius=4,
                        color=color,
                        fill=True,
                        fillOpacity=0.8,
                        tooltip=f"Entrée: {flight['callsign']} depuis {flight['origin']}"
                    ).add_to(m)
                else:
                    folium.CircleMarker(
                        location=coords[-1],
                        radius=4,
                        color=color,
                        fill=True,
                        fillOpacity=0.8,
                        tooltip=f"Sortie: {flight['callsign']} vers {flight['destination']}"
                    ).add_to(m)
                
                flights_with_track += 1
        else:
            # Trajectoire estimée (ligne droite) — TOUJOURS tracer si on a les coordonnées
            if flight.get('is_arrival'):
                origin_coords = get_airport_coords(flight.get('origin'))
                if origin_coords:
                    estimated = estimate_flight_path(origin_coords, (BVA_LAT, BVA_LON), 20)
                    if estimated:
                        coords = [[p['lat'], p['lon']] for p in estimated]
                        folium.PolyLine(
                            coords,
                            color=color,
                            weight=2,
                            opacity=0.5,
                            dash_array='5, 5',
                            tooltip=f"✈️ {flight['callsign']} | {flight['origin']} → BVA (estimé)"
                        ).add_to(m)
                        
                        # Marqueur origine
                        folium.CircleMarker(
                            location=[origin_coords[0], origin_coords[1]],
                            radius=5,
                            color=color,
                            fill=True,
                            fillOpacity=0.6,
                            tooltip=f"Origine: {flight['origin']}"
                        ).add_to(m)
                        
                        flights_estimated += 1
            else:
                dest_coords = get_airport_coords(flight.get('destination'))
                if dest_coords:
                    estimated = estimate_flight_path((BVA_LAT, BVA_LON), dest_coords, 20)
                    if estimated:
                        coords = [[p['lat'], p['lon']] for p in estimated]
                        folium.PolyLine(
                            coords,
                            color=color,
                            weight=2,
                            opacity=0.5,
                            dash_array='5, 5',
                            tooltip=f"✈️ {flight['callsign']} | BVA → {flight['destination']} (estimé)"
                        ).add_to(m)
                        
                        # Marqueur destination
                        folium.CircleMarker(
                            location=[dest_coords[0], dest_coords[1]],
                            radius=5,
                            color=color,
                            fill=True,
                            fillOpacity=0.6,
                            tooltip=f"Destination: {flight['destination']}"
                        ).add_to(m)
                        
                        flights_estimated += 1
    
    # Afficher la carte
    st_folium(m, width=None, height=550, use_container_width=True, returned_objects=[])
    
    st.caption(f"📊 {flights_with_track} trajectoires réelles + {flights_estimated} estimées")

with col_info:
    st.markdown("#### Légende")
    
    if color_mode == "type":
        st.markdown("""
        <div class="legend-box">
            <div class="legend-item">
                <div class="legend-line" style="background: #22C55E;"></div>
                Arrivées à BVA
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #F97316;"></div>
                Départs de BVA
            </div>
            <hr style="border-top: 1px solid #2D3748; margin: 0.5rem 0;">
            <div class="legend-item">
                <div class="legend-line" style="background: #64748B; opacity: 0.5;"></div>
                Trajectoire estimée
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif color_mode == "weather":
        st.markdown("""
        <div class="legend-box">
            <div class="legend-item">
                <div class="legend-line" style="background: #22C55E;"></div>
                Météo favorable (80+)
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #EAB308;"></div>
                Météo modérée (50-79)
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #EF4444;"></div>
                Météo difficile (<50)
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="legend-box">
            <div class="legend-item">
                <div class="legend-line" style="background: #FCD34D;"></div>
                Matin (6h-12h)
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #F97316;"></div>
                Après-midi (12h-18h)
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #A855F7;"></div>
                Soir (18h-22h)
            </div>
            <div class="legend-item">
                <div class="legend-line" style="background: #3B82F6;"></div>
                Nuit (22h-6h)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown("#### Période analysée")
    st.markdown(f"""
    <div class="legend-box">
        <div style="font-size: 0.85rem; color: #94A3B8;">
            <b>Début:</b> {flight_data['period']['start'].strftime('%d/%m %H:%M')}<br>
            <b>Fin:</b> {flight_data['period']['end'].strftime('%d/%m %H:%M')}<br>
            <b>Durée:</b> {hours_choice}h
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown("#### Top destinations")
    
    # Calculer les destinations les plus fréquentes
    destinations = {}
    for f in flight_data['departures']:
        dest = f.get('destination', 'N/A')
        if dest != 'N/A':
            destinations[dest] = destinations.get(dest, 0) + 1
    
    if destinations:
        sorted_dest = sorted(destinations.items(), key=lambda x: x[1], reverse=True)[:5]
        for dest, count in sorted_dest:
            st.caption(f"🛫 {dest}: {count} vol(s)")
    
    st.markdown("")
    st.markdown("#### Top origines")
    
    origins = {}
    for f in flight_data['arrivals']:
        orig = f.get('origin', 'N/A')
        if orig != 'N/A':
            origins[orig] = origins.get(orig, 0) + 1
    
    if origins:
        sorted_orig = sorted(origins.items(), key=lambda x: x[1], reverse=True)[:5]
        for orig, count in sorted_orig:
            st.caption(f"🛬 {orig}: {count} vol(s)")

st.divider()

# =============================================================================
# Analyse Météo / Trajectoires
# =============================================================================
st.markdown("### 📊 Analyse : Impact météo sur les trajectoires")

if weather_data and flight_data['tracks_retrieved'] > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Conditions météo de la période")
        
        # Créer un DataFrame avec météo et vols par jour
        days_to_show = min(7, hours_choice // 24)
        
        df_weather = pd.DataFrame({
            'Date': weather_data['time'][:days_to_show],
            'Vent Max (km/h)': weather_data['wind_speed_10m_max'][:days_to_show],
            'Précip (mm)': weather_data['precipitation_sum'][:days_to_show],
            'Temp Max (°C)': weather_data['temperature_2m_max'][:days_to_show]
        })
        
        # Graphique
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_weather['Date'],
            y=df_weather['Vent Max (km/h)'],
            name='Vent Max',
            marker_color='#8B5CF6'
        ))
        
        fig.add_hline(y=40, line_dash="dash", line_color="#EF4444", 
                     annotation_text="Seuil critique (40 km/h)")
        fig.add_hline(y=25, line_dash="dot", line_color="#EAB308",
                     annotation_text="Seuil vigilance (25 km/h)")
        
        fig.update_layout(
            title=dict(text="Vent maximum par jour", font=dict(size=13, color='#FAFAFA')),
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='km/h'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Observation des trajectoires")
        
        st.markdown("""
        <div class="alert-box alert-info">
            <b>💡 Comment interpréter la carte :</b><br>
            <small>
            • Les trajectoires <b>réelles</b> (lignes pleines) montrent le chemin exact des avions<br>
            • Par <b>vent fort</b>, les approches peuvent être plus longues ou décalées<br>
            • Les trajectoires <b>estimées</b> (pointillés) sont des lignes directes quand les données réelles ne sont pas disponibles
            </small>
        </div>
        """, unsafe_allow_html=True)
        
        # Analyser les trajectoires par conditions météo
        flights_good_weather = 0
        flights_bad_weather = 0
        
        for flight in all_flights:
            if flight.get('last_seen'):
                day_str = flight['last_seen'].strftime("%Y-%m-%d")
                score = weather_scores.get(day_str, 50)
                if score >= 70:
                    flights_good_weather += 1
                else:
                    flights_bad_weather += 1
        
        st.markdown(f"""
        **Répartition des vols :**
        - 🟢 **{flights_good_weather}** vols par bonne météo
        - 🔴 **{flights_bad_weather}** vols par météo dégradée
        """)
        
        # Conclusions
        if flights_bad_weather > 0:
            st.markdown("""
            <div class="alert-box alert-warning">
                ⚠️ Des vols ont eu lieu par conditions dégradées. 
                Compare les trajectoires colorées par météo pour voir les différences d'approche.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-box alert-success">
                ✅ Tous les vols de la période ont eu lieu par conditions favorables.
            </div>
            """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Liste des vols avec détails
# =============================================================================
st.markdown("### ✈️ Détail des vols analysés")

tab1, tab2 = st.tabs(["🛬 Arrivées", "🛫 Départs"])

with tab1:
    if flight_data['arrivals']:
        for flight in flight_data['arrivals'][:15]:
            has_track = "✅" if flight.get('has_track') else "⬜"
            
            # Gérer les différents formats de date
            flight_time = flight.get('last_seen') or flight.get('first_seen')
            time_str = flight_time.strftime('%d/%m %H:%M') if flight_time else 'N/A'
            
            # Score météo du jour
            weather_badge = ""
            if flight_time:
                day_str = flight_time.strftime("%Y-%m-%d")
                score = weather_scores.get(day_str, 50)
                if score >= 80:
                    weather_badge = '<span class="weather-badge weather-good">Météo OK</span>'
                elif score >= 50:
                    weather_badge = '<span class="weather-badge weather-moderate">Météo modérée</span>'
                else:
                    weather_badge = '<span class="weather-badge weather-bad">Météo difficile</span>'
            
            # Infos supplémentaires
            airline = flight.get('airline', '')
            aircraft = flight.get('aircraft_type', '')
            extra_info = f"{airline}" if airline and airline != 'N/A' else ""
            if aircraft and aircraft != 'N/A':
                extra_info += f" • {aircraft}" if extra_info else aircraft
            
            st.markdown(f"""
            <div class="flight-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #22C55E;">{has_track} {flight['callsign']}</strong>
                        <span style="color: #64748B;"> depuis {flight['origin']}</span>
                    </div>
                    <div>{weather_badge}</div>
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                    {time_str} {' • ' + extra_info if extra_info else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucune arrivée trouvée pour cette période")

with tab2:
    if flight_data['departures']:
        for flight in flight_data['departures'][:15]:
            has_track = "✅" if flight.get('has_track') else "⬜"
            
            flight_time = flight.get('first_seen') or flight.get('last_seen')
            time_str = flight_time.strftime('%d/%m %H:%M') if flight_time else 'N/A'
            
            weather_badge = ""
            if flight_time:
                day_str = flight_time.strftime("%Y-%m-%d")
                score = weather_scores.get(day_str, 50)
                if score >= 80:
                    weather_badge = '<span class="weather-badge weather-good">Météo OK</span>'
                elif score >= 50:
                    weather_badge = '<span class="weather-badge weather-moderate">Météo modérée</span>'
                else:
                    weather_badge = '<span class="weather-badge weather-bad">Météo difficile</span>'
            
            airline = flight.get('airline', '')
            aircraft = flight.get('aircraft_type', '')
            extra_info = f"{airline}" if airline and airline != 'N/A' else ""
            if aircraft and aircraft != 'N/A':
                extra_info += f" • {aircraft}" if extra_info else aircraft
            
            st.markdown(f"""
            <div class="flight-card" style="border-left-color: #F97316;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #F97316;">{has_track} {flight['callsign']}</strong>
                        <span style="color: #64748B;"> vers {flight['destination']}</span>
                    </div>
                    <div>{weather_badge}</div>
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                    {time_str} {' • ' + extra_info if extra_info else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun départ trouvé pour cette période")

# =============================================================================
# Footer
# =============================================================================
st.markdown(f"""
<div class="footer">
    Données : OpenSky Network (trajectoires) & OpenMeteo (météo)<br>
    Projet Mineure Numérique B2 — 2025<br>
    <small>Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}</small>
</div>
""", unsafe_allow_html=True)