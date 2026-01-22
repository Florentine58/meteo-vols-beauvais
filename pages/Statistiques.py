"""
Page Statistiques — Analyse du trafic aérien et qualité de l'air
Design professionnel unifié
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Imports des modules API
from api.flights import get_flights_in_area, get_airport_info, get_airlines_stats, get_aircraft_stats
from api.weather import get_current_weather, get_hourly_forecast
from api.air_quality import get_current_air_quality, get_air_quality_forecast, calculate_aviation_air_impact

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Statistiques",
    page_icon="✈️",
    layout="wide"
)

# =============================================================================
# CSS Professionnel Sobre
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .page-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #00D4FF;
    }
    
    .page-header h1 {
        color: #FAFAFA;
        font-weight: 600;
        margin: 0;
        font-size: 1.35rem;
    }
    
    .page-header p {
        color: #94A3B8;
        margin: 0.25rem 0 0 0;
        font-size: 0.85rem;
    }
    
    .stat-card {
        background: #151B28;
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #FAFAFA;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.25rem;
    }
    
    .stat-green { color: #22C55E; }
    .stat-yellow { color: #EAB308; }
    .stat-red { color: #EF4444; }
    .stat-blue { color: #00D4FF; }
    
    .section-card {
        background: #151B28;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        margin-bottom: 1rem;
    }
    
    .alert-box {
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    
    .alert-success {
        background: rgba(34, 197, 94, 0.1);
        border-left: 3px solid #22C55E;
        color: #86EFAC;
    }
    
    .alert-warning {
        background: rgba(234, 179, 8, 0.1);
        border-left: 3px solid #EAB308;
        color: #FDE047;
    }
    
    .alert-danger {
        background: rgba(239, 68, 68, 0.1);
        border-left: 3px solid #EF4444;
        color: #FCA5A5;
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
    
    hr {
        border: none;
        border-top: 1px solid #2D3748;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# En-tête
# =============================================================================
st.markdown("""
<div class="page-header">
    <h1>Statistiques & Analyses</h1>
    <p>Analyse du trafic aérien et corrélation avec la météo</p>
</div>
""", unsafe_allow_html=True)

if st.button("Actualiser", type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
with st.spinner("Chargement des données..."):
    flights = get_flights_in_area()
    weather = get_current_weather()
    air_quality = get_current_air_quality()

# =============================================================================
# SECTION 1 : Vue d'ensemble
# =============================================================================
st.markdown("### Vue d'ensemble")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-blue">{len(flights)}</div>
        <div class="stat-label">Vols détectés</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-green">{in_flight}</div>
        <div class="stat-label">En vol</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    on_ground = len([f for f in flights if f.get('on_ground', False)])
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{on_ground}</div>
        <div class="stat-label">Au sol</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if weather:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{weather['temperature_2m']}°C</div>
            <div class="stat-label">Température</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">N/A</div>
            <div class="stat-label">Température</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# SECTION 2 : Statistiques des compagnies aériennes
# =============================================================================
st.markdown("### Compagnies aériennes")

if flights:
    airlines_stats = get_airlines_stats(flights)
    
    if airlines_stats:
        df_airlines = pd.DataFrame([
            {"Compagnie": k, "Vols": v} 
            for k, v in sorted(airlines_stats.items(), key=lambda x: x[1], reverse=True)
        ])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_airlines = px.bar(
                df_airlines,
                x="Compagnie",
                y="Vols",
                color="Vols",
                color_continuous_scale=[[0, '#1e3a5f'], [1, '#00D4FF']],
                title="Nombre de vols par compagnie"
            )
            fig_airlines.update_layout(
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
                title=dict(font=dict(color='#FAFAFA', size=14)),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_airlines, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(
                df_airlines,
                values="Vols",
                names="Compagnie",
                title="Répartition du trafic",
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_pie.update_layout(
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                title=dict(font=dict(color='#FAFAFA', size=14)),
                legend=dict(font=dict(color='#94A3B8'))
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher les statistiques des compagnies.")
else:
    st.info("Aucun vol détecté pour analyser les compagnies.")

st.divider()

# =============================================================================
# SECTION 3 : Types d'avions
# =============================================================================
st.markdown("### Types d'avions")

if flights:
    aircraft_stats = get_aircraft_stats(flights)
    
    if aircraft_stats:
        df_aircraft = pd.DataFrame([
            {"Type": k, "Nombre": v}
            for k, v in sorted(aircraft_stats.items(), key=lambda x: x[1], reverse=True)
        ])
        
        fig_aircraft = px.bar(
            df_aircraft,
            x="Type",
            y="Nombre",
            color="Nombre",
            color_continuous_scale=[[0, '#1e3a5f'], [1, '#8B5CF6']],
            title="Nombre de vols par type d'avion"
        )
        fig_aircraft.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
            title=dict(font=dict(color='#FAFAFA', size=14)),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_aircraft, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher les types d'avions.")
else:
    st.info("Aucun vol détecté pour analyser les types d'avions.")

st.divider()

# =============================================================================
# SECTION 4 : Altitudes et vitesses
# =============================================================================
st.markdown("### Altitudes et vitesses")

if flights:
    flying = [f for f in flights if not f.get('on_ground', False) and f['altitude'] > 0]
    
    if flying:
        col1, col2 = st.columns(2)
        
        with col1:
            altitudes = [f['altitude'] for f in flying]
            fig_alt = go.Figure()
            fig_alt.add_trace(go.Histogram(
                x=altitudes,
                nbinsx=20,
                marker_color='#00D4FF'
            ))
            fig_alt.update_layout(
                title=dict(text="Distribution des altitudes (ft)", font=dict(size=13, color='#FAFAFA')),
                xaxis_title="Altitude (pieds)",
                yaxis_title="Nombre d'avions",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_alt, use_container_width=True)
            
            avg_alt = sum(altitudes) / len(altitudes)
            st.caption(f"**Altitude moyenne :** {avg_alt:.0f} ft ({avg_alt * 0.3048:.0f} m)")
        
        with col2:
            speeds = [f['ground_speed'] for f in flying]
            fig_speed = go.Figure()
            fig_speed.add_trace(go.Histogram(
                x=speeds,
                nbinsx=20,
                marker_color='#8B5CF6'
            ))
            fig_speed.update_layout(
                title=dict(text="Distribution des vitesses (kts)", font=dict(size=13, color='#FAFAFA')),
                xaxis_title="Vitesse (noeuds)",
                yaxis_title="Nombre d'avions",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_speed, use_container_width=True)
            
            avg_speed = sum(speeds) / len(speeds)
            st.caption(f"**Vitesse moyenne :** {avg_speed:.0f} kts ({avg_speed * 1.852:.0f} km/h)")
    else:
        st.info("Aucun avion en vol détecté pour analyser les altitudes et vitesses.")
else:
    st.info("Aucun vol détecté.")

st.divider()

# =============================================================================
# SECTION 5 : Corrélation météo / trafic
# =============================================================================
st.markdown("### Corrélation Météo / Trafic")

if weather and flights:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Conditions météo actuelles")
        
        conditions_score = 100
        
        wind_speed = weather['wind_speed_10m']
        if wind_speed > 40:
            conditions_score -= 40
            st.markdown(f'<div class="alert-box alert-danger">Vent fort : {wind_speed} km/h — Impact majeur</div>', unsafe_allow_html=True)
        elif wind_speed > 25:
            conditions_score -= 20
            st.markdown(f'<div class="alert-box alert-warning">Vent modéré : {wind_speed} km/h — Turbulences possibles</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-box alert-success">Vent faible : {wind_speed} km/h — Conditions favorables</div>', unsafe_allow_html=True)
        
        humidity = weather['relative_humidity_2m']
        if humidity > 90:
            conditions_score -= 15
            st.markdown(f'<div class="alert-box alert-warning">Humidité très élevée : {humidity}% — Risque de brouillard</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-box alert-success">Humidité normale : {humidity}%</div>', unsafe_allow_html=True)
        
        st.markdown("")
        
        if conditions_score >= 80:
            score_color = "stat-green"
            score_status = "Conditions excellentes"
        elif conditions_score >= 50:
            score_color = "stat-yellow"
            score_status = "Vigilance recommandée"
        else:
            score_color = "stat-red"
            score_status = "Conditions difficiles"
        
        st.markdown(f"""
        <div class="stat-card" style="margin-top: 1rem;">
            <div class="stat-value {score_color}">{conditions_score}/100</div>
            <div class="stat-label">{score_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Analyse du trafic")
        
        st.markdown(f"""
        <div class="stat-card" style="margin-bottom: 1rem;">
            <div class="stat-value stat-blue">{len(flights)}</div>
            <div class="stat-label">Vols dans la zone</div>
        </div>
        """, unsafe_allow_html=True)
        
        if len(flights) > 10:
            st.markdown('<div class="alert-box alert-success">Trafic dense — Activité importante</div>', unsafe_allow_html=True)
        elif len(flights) > 5:
            st.markdown('<div class="alert-box alert-warning">Trafic modéré — Activité normale</div>', unsafe_allow_html=True)
        elif len(flights) > 0:
            st.markdown('<div class="alert-box alert-danger">Trafic faible — Activité réduite</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-danger">Aucun trafic — Peut être lié aux conditions météo</div>', unsafe_allow_html=True)
        
        st.markdown("")
        if wind_speed > 30 and len(flights) < 5:
            st.caption("Le vent fort pourrait expliquer le faible trafic.")
        elif conditions_score >= 80 and len(flights) > 5:
            st.caption("Les bonnes conditions météo favorisent un trafic normal.")
else:
    st.info("Données insuffisantes pour l'analyse de corrélation.")

# =============================================================================
# SECTION 6 : Tableau récapitulatif
# =============================================================================
st.divider()
st.markdown("### Données brutes")

with st.expander("Voir le tableau des vols"):
    if flights:
        df_flights = pd.DataFrame(flights)
        columns_to_show = ['callsign', 'airline_icao', 'aircraft_type', 'origin', 'destination', 'altitude', 'ground_speed', 'on_ground']
        df_display = df_flights[[c for c in columns_to_show if c in df_flights.columns]]
        df_display.columns = ['Callsign', 'Compagnie', 'Avion', 'Origine', 'Destination', 'Altitude (ft)', 'Vitesse (kts)', 'Au sol']
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée à afficher.")

# =============================================================================
# Section Explicative du Code
# =============================================================================
st.divider()
with st.expander("Comprendre le code de cette page"):
    st.markdown("""
    ### Architecture de la Page Statistiques (Statistiques.py)

    Cette page effectue une **analyse statistique du trafic aérien** et établit des corrélations
    avec les conditions météorologiques. Elle utilise des visualisations Plotly avancées.

    #### Structure du code

    **1. Imports Spécialisés (lignes 1-15)**
    ```python
    import plotly.express as px  # Graphiques rapides
    import plotly.graph_objects as go  # Graphiques personnalisés
    import pandas as pd  # Manipulation de données
    ```
    - **Plotly Express** : API haut niveau pour graphiques rapides
    - **Plotly Graph Objects** : Contrôle fin des graphiques
    - **Pandas** : Traitement et analyse de données

    #### Section 1 : Vue d'Ensemble (lignes 163-208)

    **Métriques Principales**
    - Nombre total de vols détectés dans la zone 50 km
    - Vols en vol vs au sol
    - Température actuelle
    - Affichage avec cartes stylisées en HTML

    #### Section 2 : Statistiques Compagnies (lignes 211-266)

    **Fonction get_airlines_stats()**
    ```python
    # Dans api/flights.py
    def get_airlines_stats(flights):
        stats = {}
        for flight in flights:
            airline = flight.get('airline_icao', 'N/A')
            if airline not in stats:
                stats[airline] = 0
            stats[airline] += 1
        return stats
    ```
    - Compte le nombre de vols par compagnie
    - Retourne un dictionnaire `{compagnie: nombre_vols}`

    **Graphique en Barres Plotly Express**
    ```python
    fig_airlines = px.bar(
        df_airlines,
        x="Compagnie",
        y="Vols",
        color="Vols",
        color_continuous_scale=[[0, '#1e3a5f'], [1, '#00D4FF']]
    )
    ```
    - **Gradient de couleur** : Plus le nombre de vols est élevé, plus la barre est cyan
    - **Interaction** : Hover pour voir les détails

    **Graphique Camembert (Pie Chart)**
    ```python
    fig_pie = px.pie(
        df_airlines,
        values="Vols",
        names="Compagnie",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    ```
    - **Répartition visuelle** du trafic par compagnie
    - **Blues_r** : Palette de bleus inversée (plus foncé = plus important)

    #### Section 3 : Types d'Avions (lignes 269-305)

    **Distribution des Types**
    ```python
    aircraft_stats = get_aircraft_stats(flights)
    # Retourne ex: {'B738': 5, 'A320': 3, 'E190': 2, ...}

    df_aircraft = pd.DataFrame([
        {"Type": k, "Nombre": v}
        for k, v in sorted(aircraft_stats.items(),
                          key=lambda x: x[1], reverse=True)
    ])
    ```
    - **Tri décroissant** : Types les plus fréquents en premier
    - **DataFrame Pandas** : Structure de données tabulaire

    **Codes ICAO des Avions**
    | Code | Modèle | Fabricant |
    |------|--------|-----------|
    | B738 | Boeing 737-800 | Boeing |
    | A320 | Airbus A320 | Airbus |
    | E190 | Embraer 190 | Embraer |
    | AT76 | ATR 72-600 | ATR |

    #### Section 4 : Altitudes et Vitesses (lignes 308-368)

    **Histogrammes Plotly**
    ```python
    fig_alt = go.Figure()
    fig_alt.add_trace(go.Histogram(
        x=altitudes,
        nbinsx=20,  # 20 barres
        marker_color='#00D4FF'
    ))
    ```
    - **Histogramme** : Distribution statistique des altitudes
    - **nbinsx** : Nombre de "buckets" pour regrouper les données
    - Permet de voir les altitudes de croisière fréquentes

    **Calculs Statistiques**
    ```python
    avg_alt = sum(altitudes) / len(altitudes)
    avg_speed = sum(speeds) / len(speeds)
    ```
    - Moyenne simple
    - Conversion ft → m : `altitude_m = altitude_ft * 0.3048`
    - Conversion kts → km/h : `vitesse_kmh = vitesse_kts * 1.852`

    #### Section 5 : Corrélation Météo/Trafic (lignes 371-446)

    **Algorithme de Scoring**
    ```python
    conditions_score = 100

    wind_speed = weather['wind_speed_10m']
    if wind_speed > 40:
        conditions_score -= 40  # Impact majeur
    elif wind_speed > 25:
        conditions_score -= 20  # Turbulences

    humidity = weather['relative_humidity_2m']
    if humidity > 90:
        conditions_score -= 15  # Risque brouillard
    ```
    - Score commence à 100 (parfait)
    - Pénalités selon les conditions
    - Résultat : 80-100 (excellent), 50-79 (vigilance), 0-49 (difficile)

    **Analyse Trafic**
    ```python
    if len(flights) > 10:
        st.markdown('Trafic dense — Activité importante')
    elif len(flights) > 5:
        st.markdown('Trafic modéré — Activité normale')
    else:
        st.markdown('Trafic faible — Activité réduite')
    ```
    - Seuils empiriques basés sur l'observation
    - Beauvais n'est pas un hub international (trafic < Paris-CDG)

    **Corrélation Météo/Trafic**
    ```python
    if wind_speed > 30 and len(flights) < 5:
        st.caption("Le vent fort pourrait expliquer le faible trafic.")
    ```
    - Hypothèse : conditions difficiles → moins de vols
    - **Limitation** : Les données en temps réel ne permettent pas de voir les annulations

    #### Points Techniques

    **Pandas List Comprehension**
    ```python
    df_airlines = pd.DataFrame([
        {"Compagnie": k, "Vols": v}
        for k, v in sorted(airlines_stats.items(),
                          key=lambda x: x[1], reverse=True)
    ])
    ```
    - **List comprehension** : Création rapide de liste Python
    - **sorted()** : Tri par valeur (nombre de vols)
    - **lambda** : Fonction anonyme pour extraire la valeur de tri

    **Plotly Layout Personnalisé**
    ```python
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',  # Fond transparent
        plot_bgcolor='rgba(0,0,0,0)',   # Zone graphique transparente
        xaxis=dict(showgrid=False, color='#64748B'),
        yaxis=dict(showgrid=True, gridcolor='#1E293B')
    )
    ```
    - **RGBA** : Rouge, Vert, Bleu, Alpha (transparence)
    - **Grille Y** : Aide à la lecture des valeurs
    - **Pas de grille X** : Plus épuré visuellement

    #### Données Affichées

    **Tableau DataFrame**
    ```python
    df_display = df_flights[['callsign', 'airline_icao', ...]]
    df_display.columns = ['Callsign', 'Compagnie', ...]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    ```
    - **Colonnes filtrées** : Sélection des colonnes pertinentes
    - **Renommage** : Noms lisibles en français
    - **hide_index** : Masquer l'index Pandas

    #### Améliorations Possibles

    1. **Statistiques temporelles** : Évolution du trafic sur la journée/semaine
    2. **Comparaison historique** : Comparer avec le même jour l'année précédente
    3. **Heatmap horaire** : Densité du trafic par heure de la journée
    4. **Analyse routes** : Quelles sont les routes les plus fréquentes ?
    5. **Machine Learning** : Prédiction du nombre de vols selon la météo

    *Cette page permet d'identifier les patterns de trafic et l'influence
    des conditions météorologiques sur les opérations aériennes.*
    """)

# Footer
st.markdown("""
<div class="footer">
    Analyse générée avec Plotly — Données FlightRadar24 & OpenMeteo
</div>
""", unsafe_allow_html=True)