"""
Page Carte Historique — Trajectoires des vols BVA et corrélation météo
Style professionnel sobre

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
    layout="wide"
)

# =============================================================================
# CSS Professionnel Sobre
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
    .legend-line { width: 25px; height: 4px; border-radius: 2px; }

    .methodology-box {
        background: #151B28;
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        margin: 1rem 0;
    }
    .methodology-box h4 {
        color: #00D4FF;
        margin-top: 0;
        font-size: 1rem;
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
    <h1>Carte Historique des Trajectoires</h1>
    <p>Paris-Beauvais — Analyse de l'impact météorologique sur les trajectoires d'approche et de départ</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Test de connexion OpenSky
# =============================================================================
conn_status = test_connection()

if conn_status['status'] == 'error':
    st.markdown(f"""
    <div class="alert-box alert-danger">
        Connexion échouée : {conn_status['message']}<br>
        <small>Vérifiez vos credentials OpenSky dans le fichier .env</small>
    </div>
    """, unsafe_allow_html=True)
    st.stop()
elif conn_status['status'] == 'warning':
    st.markdown(f"""
    <div class="alert-box alert-warning">
        {conn_status['message']}<br>
        <small>Les trajectoires détaillées nécessitent une authentification OpenSky</small>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alert-box alert-success">
        {conn_status['message']} — Trajectoires disponibles
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Onglets principaux
# =============================================================================
# Contrôles
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

with c1:
    hours_choice = st.selectbox(
        "Période",
        options=[24, 48, 72, 168],
        format_func=lambda x: f"{x}h" if x < 168 else "7 jours",
        index=1
    )

with c2:
    max_tracks = st.selectbox(
        "Max trajectoires",
        options=[10, 20, 30, 50],
        index=1,
        help="Limite pour économiser les appels OpenSky"
    )

with c3:
    color_mode = st.selectbox(
        "Coloration",
        options=["type", "weather", "time"],
        format_func=lambda x: {"type": "Arrivée/Départ", "weather": "Conditions météo", "time": "Heure du vol"}[x],
        index=0
    )

with c4:
    if st.button("Recharger les données", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Options
o1, o2, o3 = st.columns([1, 1, 2])
with o1:
    show_real = st.checkbox("Trajets réels", value=True)
with o2:
    show_est = st.checkbox("Trajets estimés", value=True)
with o3:
    only_arrivals = st.checkbox("Arrivées uniquement", value=False)

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
@st.cache_data(ttl=600, show_spinner=False)
def load_flight_data(hours, max_tracks):
    return get_beauvais_flights_with_tracks(hours=hours, max_tracks=max_tracks)

@st.cache_data(ttl=3600, show_spinner=False)
def load_weather_data(days):
    return get_historical_weather(days=days)

with st.spinner(f"Récupération des vols BVA ({hours_choice}h) et trajectoires..."):
    flight_data = load_flight_data(hours_choice, max_tracks)
    weather_data = load_weather_data(days=max(7, hours_choice // 24))

# =============================================================================
# Métriques
# =============================================================================
m1, m2, m3, m4, m5 = st.columns(5)

total_flights = flight_data['total_flights']
arrivals_count = len(flight_data['arrivals'])
departures_count = len(flight_data['departures'])
tracks_count = flight_data['tracks_retrieved']
real_pct = (tracks_count / total_flights * 100) if total_flights else 0

with m1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-blue">{total_flights}</div>
        <div class="stat-label">Vols total</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-green">{arrivals_count}</div>
        <div class="stat-label">Arrivées BVA</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-orange">{departures_count}</div>
        <div class="stat-label">Départs BVA</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-purple">{tracks_count}</div>
        <div class="stat-label">Trajectoires réelles</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    if weather_data:
        slice_days = max(1, hours_choice // 24)
        avg_wind = float(np.mean((weather_data.get('wind_speed_10m_max', [])[:slice_days]) or [0]))
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
# Helpers
# =============================================================================
def get_track_color(flight, weather_score=None):
    if color_mode == "type":
        return '#22C55E' if flight.get('is_arrival') else '#F97316'

    if color_mode == "weather":
        if weather_score is None:
            return '#64748B'
        if weather_score >= 80:
            return '#22C55E'
        elif weather_score >= 50:
            return '#EAB308'
        else:
            return '#EF4444'

    # time
    hour = None
    t = flight.get('last_seen') or flight.get('first_seen')
    if t:
        hour = t.hour
    if hour is None:
        return '#64748B'
    if 6 <= hour < 12:
        return '#FCD34D'
    elif 12 <= hour < 18:
        return '#F97316'
    elif 18 <= hour < 22:
        return '#A855F7'
    else:
        return '#3B82F6'

def pick_origin_code(f):
    code = f.get('origin_icao') or f.get('origin')
    if code in (None, "", "N/A"):
        return None
    return code

def pick_dest_code(f):
    code = f.get('destination_icao') or f.get('destination')
    if code in (None, "", "N/A"):
        return None
    return code

def safe_waypoint_coords(waypoints):
    coords = []
    for wp in waypoints or []:
        lat = wp.get('lat')
        lon = wp.get('lon')
        if lat is not None and lon is not None:
            coords.append([lat, lon])
    return coords

# Score météo par jour
weather_scores = {}
if weather_data:
    times = weather_data.get('time', [])[:14]
    winds = weather_data.get('wind_speed_10m_max', [])[:14]
    precs = weather_data.get('precipitation_sum', [])[:14]

    for i, date in enumerate(times):
        wind = winds[i] if i < len(winds) and winds[i] is not None else 0
        precip = precs[i] if i < len(precs) and precs[i] is not None else 0

        score = 100
        if wind > 50:
            score -= 40
        elif wind > 35:
            score -= 25
        elif wind > 25:
            score -= 10

        if precip > 20:
            score -= 25
        elif precip > 10:
            score -= 15

        weather_scores[date] = max(0, int(score))

# =============================================================================
# Carte + trajectoires
# =============================================================================
col_map, col_info = st.columns([3, 1])

# Préparer vols
all_flights = (flight_data['arrivals'] + flight_data['departures'])
if only_arrivals:
    all_flights = [f for f in all_flights if f.get("is_arrival")]

with col_map:
    st.markdown("#### Carte des trajectoires")

    m = folium.Map(
        location=[BVA_LAT, BVA_LON],
        zoom_start=7,
        tiles='CartoDB dark_matter'
    )

    # Layer groups
    layer_real = folium.FeatureGroup(name="Trajets réels (OpenSky)", show=True)
    layer_est = folium.FeatureGroup(name="Trajets estimés", show=True)
    layer_pts = folium.FeatureGroup(name="Points (orig/dest)", show=False)

    # Zone aéroport
    folium.Circle(
        location=[BVA_LAT, BVA_LON],
        radius=15000,
        color='#00D4FF',
        fill=True,
        fillOpacity=0.1,
        weight=2
    ).add_to(m)

    folium.Marker(
        location=[BVA_LAT, BVA_LON],
        popup="Paris-Beauvais (LFOB)",
        tooltip="BVA - Beauvais",
        icon=folium.Icon(color='red', icon='plane', prefix='fa')
    ).add_to(m)

    flights_with_track = 0
    flights_estimated = 0

    for flight in all_flights:
        weather_score = None
        t = flight.get('last_seen') or flight.get('first_seen')
        if t:
            day_str = t.strftime("%Y-%m-%d")
            weather_score = weather_scores.get(day_str, 50)

        color = get_track_color(flight, weather_score)

        # Trajectoire réelle
        if show_real and flight.get('has_track') and flight.get('track'):
            waypoints = flight['track'].get('waypoints', [])
            coords = safe_waypoint_coords(waypoints)

            if len(coords) >= 2:
                origin_display = pick_origin_code(flight) or "N/A"
                dest_display = pick_dest_code(flight) or "N/A"

                folium.PolyLine(
                    coords,
                    color=color,
                    weight=3,
                    opacity=0.85,
                    tooltip=f"{flight.get('callsign','N/A')} | {origin_display} → {dest_display} (réel)"
                ).add_to(layer_real)

                if flight.get('is_arrival'):
                    folium.CircleMarker(
                        location=coords[0],
                        radius=4,
                        color=color,
                        fill=True,
                        fillOpacity=0.85,
                        tooltip=f"Entrée: {flight.get('callsign','N/A')} ({origin_display} → BVA)"
                    ).add_to(layer_pts)
                else:
                    folium.CircleMarker(
                        location=coords[-1],
                        radius=4,
                        color=color,
                        fill=True,
                        fillOpacity=0.85,
                        tooltip=f"Sortie: {flight.get('callsign','N/A')} (BVA → {dest_display})"
                    ).add_to(layer_pts)

                flights_with_track += 1

        # Trajectoire estimée
        if show_est and (not flight.get('has_track') or not flight.get('track')):
            if flight.get('is_arrival'):
                origin_code = pick_origin_code(flight)
                origin_coords = get_airport_coords(origin_code) if origin_code else None

                if origin_coords:
                    estimated = estimate_flight_path(origin_coords, (BVA_LAT, BVA_LON), 20)
                    coords = [[p['lat'], p['lon']] for p in estimated] if estimated else []
                    if len(coords) >= 2:
                        folium.PolyLine(
                            coords,
                            color=color,
                            weight=2,
                            opacity=0.55,
                            dash_array='5, 6',
                            tooltip=f"{flight.get('callsign','N/A')} | {origin_code} → BVA (estimé)"
                        ).add_to(layer_est)

                        folium.CircleMarker(
                            location=[origin_coords[0], origin_coords[1]],
                            radius=5,
                            color=color,
                            fill=True,
                            fillOpacity=0.6,
                            tooltip=f"Origine: {origin_code}"
                        ).add_to(layer_pts)

                        flights_estimated += 1
            else:
                dest_code = pick_dest_code(flight)
                dest_coords = get_airport_coords(dest_code) if dest_code else None

                if dest_coords:
                    estimated = estimate_flight_path((BVA_LAT, BVA_LON), dest_coords, 20)
                    coords = [[p['lat'], p['lon']] for p in estimated] if estimated else []
                    if len(coords) >= 2:
                        folium.PolyLine(
                            coords,
                            color=color,
                            weight=2,
                            opacity=0.55,
                            dash_array='5, 6',
                            tooltip=f"{flight.get('callsign','N/A')} | BVA → {dest_code} (estimé)"
                        ).add_to(layer_est)

                        folium.CircleMarker(
                            location=[dest_coords[0], dest_coords[1]],
                            radius=5,
                            color=color,
                            fill=True,
                            fillOpacity=0.6,
                            tooltip=f"Destination: {dest_code}"
                        ).add_to(layer_pts)

                        flights_estimated += 1

    # Ajouter layers
    layer_real.add_to(m)
    layer_est.add_to(m)
    layer_pts.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(m, width=None, height=560, use_container_width=True, returned_objects=[])

    st.caption(f"Affiché : {flights_with_track} trajectoires réelles + {flights_estimated} estimées")

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
                <div class="legend-line" style="background: #64748B; opacity: 0.6;"></div>
                Pointillés = estimé
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
                Météo difficile (&lt;50)
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
            <b>Début :</b> {flight_data['period']['start'].strftime('%d/%m %H:%M')}<br>
            <b>Fin :</b> {flight_data['period']['end'].strftime('%d/%m %H:%M')}<br>
            <b>Durée :</b> {hours_choice}h
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Analyse Météo / Trajectoires
# =============================================================================
st.markdown("#### Analyse : Impact météo sur les trajectoires")

if weather_data:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Conditions météo de la période")

        days_to_show = min(7, max(1, hours_choice // 24))
        df_weather = pd.DataFrame({
            'Date': weather_data['time'][:days_to_show],
            'Vent Max (km/h)': weather_data['wind_speed_10m_max'][:days_to_show],
            'Précip (mm)': weather_data['precipitation_sum'][:days_to_show],
            'Temp Max (°C)': weather_data['temperature_2m_max'][:days_to_show]
        })

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
        st.markdown("##### Lecture des données")
        st.markdown("""
        <div class="alert-box alert-info">
            <b>Interprétation :</b><br>
            <small>
            Les lignes pleines représentent les trajets réels enregistrés par OpenSky Network.
            Les lignes pointillées sont des estimations (ligne droite) utilisées quand les
            données de trajectoire ne sont pas disponibles.<br><br>
            En mode "Conditions météo", comparez les couleurs des trajectoires avec les
            jours de vent fort pour observer les corrélations.
            </small>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# TAB 2 : Méthodologie
# =============================================================================
with tab_methodologie:
    st.markdown("### Méthodologie des Trajectoires")
    
    st.markdown("""
    <div class="alert-box alert-info">
        Cette section explique comment les trajectoires des avions sont obtenues et affichées, 
        ainsi que les limites des données gratuites disponibles.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Section 1 : Sources de données
    st.markdown("#### 1. Sources de données utilisées")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="methodology-box">
            <h4>FlightRadar24 (Vols en temps réel)</h4>
            <p style="color: #94A3B8; font-size: 0.9rem;">
            <b>Données fournies :</b>
            </p>
            <ul style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.5rem;">
                <li>Position temps réel (latitude, longitude)</li>
                <li>Altitude et vitesse</li>
                <li>Callsign et compagnie</li>
                <li>Origine et destination déclarées</li>
                <li>Type d'avion</li>
            </ul>
            <p style="color: #22C55E; font-weight: 500; margin-top: 0.75rem;">Gratuit et illimité</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="methodology-box">
            <h4>OpenSky Network (Trajectoires)</h4>
            <p style="color: #94A3B8; font-size: 0.9rem;">
            <b>Données fournies :</b>
            </p>
            <ul style="color: #94A3B8; font-size: 0.85rem; margin-top: 0.5rem;">
                <li>Historique des positions (waypoints)</li>
                <li>Trajectoire complète du vol</li>
                <li>Données ADS-B brutes</li>
            </ul>
            <p style="color: #EAB308; font-weight: 500; margin-top: 0.75rem;">
                Nécessite authentification<br>
                <small style="color: #64748B;">Compte gratuit limité à quelques requêtes/jour</small>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Section 2 : Types de trajectoires
    st.markdown("#### 2. Types de trajectoires affichées")
    
    st.markdown("""
    <div class="methodology-box">
        <h4>Deux types de trajectoires sur la carte</h4>
        
        <table style="width: 100%; margin-top: 1rem; color: #94A3B8;">
            <tr style="border-bottom: 1px solid #2D3748;">
                <td style="padding: 0.75rem;"><b style="color: #22C55E;">━━━ Ligne pleine</b></td>
                <td style="padding: 0.75rem;"><b>Trajectoire réelle (OpenSky)</b></td>
                <td style="padding: 0.75rem;">Points GPS historiques enregistrés par les récepteurs ADS-B</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem;"><b style="color: #64748B;">- - - Ligne pointillée</b></td>
                <td style="padding: 0.75rem;"><b>Trajectoire estimée</b></td>
                <td style="padding: 0.75rem;">Ligne droite entre l'aéroport d'origine/destination et BVA</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Section 3 : Algorithme d'estimation
    st.markdown("#### 3. Comment sont estimées les trajectoires ?")
    
    st.markdown("""
    Quand les trajectoires réelles ne sont pas disponibles (compte OpenSky non authentifié ou vol sans données), 
    une estimation simplifiée est utilisée.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Algorithme utilisé :**
        
        ```python
        def estimate_flight_path(origin_coords, dest_coords, num_points=30):
            # Interpolation linéaire entre origine et destination
            points = []
            for i in range(num_points + 1):
                t = i / num_points
                lat = origin_lat + t * (dest_lat - origin_lat)
                lon = origin_lon + t * (dest_lon - origin_lon)
                points.append((lat, lon))
            return points
        ```
        
        **Limites de cette méthode :**
        - Ne prend pas en compte les couloirs aériens réels (SID/STAR)
        - Ignore la courbure terrestre (orthodromie)
        - Ne reflète pas les zones de contrôle aérien
        - Pas de prise en compte du vent ou de la météo
        """)
    
    with col2:
        st.markdown("""
        <div class="methodology-box">
            <h4>Précision</h4>
            <p style="color: #94A3B8;">
            <b>Trajectoire réelle :</b> ~10-50m<br>
            <b>Trajectoire estimée :</b> Indicative uniquement
            </p>
            <hr style="border-top: 1px solid #2D3748;">
            <p style="color: #64748B; font-size: 0.8rem;">
            Les trajectoires estimées servent uniquement à visualiser 
            l'origine/destination probable d'un vol.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Section 4 : Pour aller plus loin
    st.markdown("#### 4. Pour des trajectoires plus précises")
    
    st.markdown("""
    <div class="alert-box alert-warning">
        <b>APIs premium disponibles (hors cadre de ce projet) :</b>
        <ul style="margin-top: 0.5rem; margin-bottom: 0;">
            <li><b>FlightAware</b> — Historique complet et trajectoires détaillées (~$50/mois)</li>
            <li><b>AeroDataBox</b> — Retards, horaires, données aéroports (~$20/mois)</li>
            <li><b>OpenSky Premium</b> — Accès étendu aux données ADS-B</li>
            <li><b>Données AIRAC</b> — Routes officielles (SID/STAR) publiées par les autorités aériennes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Section 5 : Schéma explicatif
    st.markdown("#### 5. Schéma : Vraie trajectoire vs Estimation")
    
    st.code("""
                    ✈️ Vraie trajectoire (courbe, suit les couloirs aériens)
                   /
ORIGINE ○─────────/─────────────────────○ BVA
                 /                      
                /   - - - - - - - - - -   Trajectoire estimée (ligne droite)
               /
              ✈️

La vraie trajectoire suit :
• Les procédures de départ (SID - Standard Instrument Departure)
• Les routes aériennes (Airways)  
• Les procédures d'approche (STAR - Standard Terminal Arrival Route)
• Les instructions du contrôle aérien
    """, language=None)
    
    st.markdown("")
    
    # Conclusion
    st.markdown("""
    <div class="methodology-box">
        <h4>En résumé</h4>
        <p style="color: #FAFAFA;">
        Les trajectoires affichées sur la carte proviennent de deux sources : 
        les <b>données réelles</b> via OpenSky Network (quand disponibles) montrant le chemin exact 
        suivi par l'avion, et des <b>estimations</b> (lignes droites) quand ces données ne sont pas 
        accessibles. Cette limitation est due aux restrictions des APIs gratuites. 
        Pour un projet professionnel, on utiliserait des données AIRAC officielles 
        et des APIs premium comme FlightAware.
        </p>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# Footer
# =============================================================================
st.markdown(f"""
<div class="footer">
    Données : FlightRadar24 (vols) + OpenSky (trajectoires) + OpenMeteo (météo)<br>
    Projet Mineure Numérique B2 — 2025<br>
    <small>Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}</small>
</div>
""", unsafe_allow_html=True)