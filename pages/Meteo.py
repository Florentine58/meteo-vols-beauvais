"""
Page Météo — Données météorologiques complètes de Beauvais
Prévisions, historique et impact aviation
Style professionnel sobre

Projet Mineure Numérique B2 — 2025
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from api.weather import (
    get_current_weather, 
    get_hourly_forecast, 
    get_historical_weather,
    get_weather_code_description,
    get_aviation_conditions_forecast,
    BEAUVAIS_LAT, 
    BEAUVAIS_LON
)

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Météo",
    page_icon="✈️",
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
    
    .weather-main {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
    }
    
    .weather-temp {
        font-size: 4rem;
        font-weight: 700;
        color: #FAFAFA;
        line-height: 1;
    }
    
    .weather-desc {
        font-size: 1.25rem;
        color: #94A3B8;
        margin-top: 0.5rem;
    }
    
    .weather-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .stat-card {
        background: #151B28;
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    .stat-value { font-size: 1.5rem; font-weight: 700; color: #FAFAFA; }
    .stat-label { font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.25rem; }
    .stat-green { color: #22C55E; }
    .stat-yellow { color: #EAB308; }
    .stat-red { color: #EF4444; }
    .stat-blue { color: #00D4FF; }
    
    .forecast-card {
        background: #1A1F2E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    
    .alert-box { padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0; font-size: 0.85rem; }
    .alert-success { background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22C55E; color: #86EFAC; }
    .alert-warning { background: rgba(234, 179, 8, 0.1); border-left: 3px solid #EAB308; color: #FDE047; }
    .alert-danger { background: rgba(239, 68, 68, 0.1); border-left: 3px solid #EF4444; color: #FCA5A5; }
    .alert-info { background: rgba(0, 212, 255, 0.1); border-left: 3px solid #00D4FF; color: #7DD3FC; }
    
    .footer { text-align: center; padding: 1.5rem; color: #64748B; font-size: 0.75rem; border-top: 1px solid #2D3748; margin-top: 2rem; }
    
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
    <h1>Météo Beauvais</h1>
    <p>Données météorologiques en temps réel et prévisions — Station de Beauvais-Tillé</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col1:
    st.caption(f"Coordonnées : {BEAUVAIS_LAT}°N, {BEAUVAIS_LON}°E | Dernière mise à jour : {datetime.now().strftime('%H:%M')}")
with col2:
    if st.button("Actualiser", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
with st.spinner("Chargement des données météo..."):
    weather = get_current_weather()
    hourly = get_hourly_forecast(days=1)
    aviation_forecast = get_aviation_conditions_forecast()

# =============================================================================
# SECTION 1 : Météo actuelle
# =============================================================================
if weather:
    col_main, col_details = st.columns([2, 3])
    
    with col_main:
        icon, desc = get_weather_code_description(weather.get('weather_code', 0))
        
        st.markdown(f"""
        <div class="weather-main">
            <div class="weather-icon">{icon}</div>
            <div class="weather-temp">{weather['temperature_2m']}°C</div>
            <div class="weather-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_details:
        c1, c2, c3 = st.columns(3)
        
        with c1:
            wind = weather['wind_speed_10m']
            color = "stat-red" if wind > 40 else "stat-yellow" if wind > 25 else "stat-green"
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value {color}">{wind}</div>
                <div class="stat-label">Vent (km/h)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            humidity = weather['relative_humidity_2m']
            color = "stat-yellow" if humidity > 85 else ""
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value {color}">{humidity}%</div>
                <div class="stat-label">Humidité</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            wind_dir = weather['wind_direction_10m']
            directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
            dir_idx = int((wind_dir + 22.5) / 45) % 8
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{directions[dir_idx]}</div>
                <div class="stat-label">Direction ({wind_dir}°)</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("**Impact Aviation**")
        
        alerts = []
        if wind > 40:
            alerts.append(("danger", f"Vent fort ({wind} km/h) — Risque de retards/déroutements"))
        elif wind > 25:
            alerts.append(("warning", f"Vent modéré ({wind} km/h) — Turbulences possibles"))
        
        if humidity > 90:
            alerts.append(("warning", f"Humidité très élevée ({humidity}%) — Risque de brouillard"))
        
        if weather.get('weather_code', 0) in [45, 48]:
            alerts.append(("danger", "Brouillard détecté — Impact majeur sur les vols"))
        elif weather.get('weather_code', 0) in [95, 96, 99]:
            alerts.append(("danger", "Orage en cours — Opérations suspendues"))
        elif weather.get('weather_code', 0) in [71, 73, 75]:
            alerts.append(("danger", "Neige — Piste potentiellement impactée"))
        
        if not alerts:
            st.markdown('<div class="alert-box alert-success">Conditions favorables pour l\'aviation</div>', unsafe_allow_html=True)
        else:
            for level, msg in alerts:
                st.markdown(f'<div class="alert-box alert-{level}">{msg}</div>', unsafe_allow_html=True)

else:
    st.error("Impossible de récupérer les données météo actuelles.")

st.divider()

# =============================================================================
# SECTION 2 : Prévisions 7 jours
# =============================================================================
st.markdown("### Prévisions 7 jours")

if aviation_forecast:
    cols = st.columns(7)
    
    for i, day in enumerate(aviation_forecast[:7]):
        with cols[i]:
            date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            icon, desc = get_weather_code_description(day['weather_code'])
            
            if day['score'] >= 80:
                border_color = "#22C55E"
                score_color = "#22C55E"
            elif day['score'] >= 50:
                border_color = "#EAB308"
                score_color = "#EAB308"
            else:
                border_color = "#EF4444"
                score_color = "#EF4444"
            
            st.markdown(f"""
            <div class="forecast-card" style="border-top: 3px solid {border_color};">
                <div style="font-weight: 600; color: #FAFAFA;">{date_obj.strftime('%a')}</div>
                <div style="font-size: 0.75rem; color: #64748B;">{date_obj.strftime('%d/%m')}</div>
                <div style="font-size: 2rem; margin: 0.5rem 0;">{icon}</div>
                <div style="font-size: 0.8rem; color: #94A3B8;">{desc[:15]}...</div>
                <div style="margin: 0.5rem 0;">
                    <span style="font-weight: 600; color: #FAFAFA;">{day['temp_max']:.0f}°</span>
                    <span style="color: #64748B;"> / {day['temp_min']:.0f}°</span>
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">
                    Vent {day['wind_max']:.0f} km/h
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">
                    Précip {day['precipitation']:.1f} mm
                </div>
                <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid #2D3748;">
                    <span style="font-size: 0.8rem; font-weight: 600; color: {score_color};">
                        Score {day['score']}/100
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("")
    st.caption("**Score Aviation :** 80-100 Optimal | 50-79 Vigilance | 0-49 Difficile")

st.divider()

# =============================================================================
# SECTION 3 : Évolution sur 24h
# =============================================================================
st.markdown("### Évolution sur 24 heures")

if hourly:
    hours = hourly['time'][:24]
    temps = hourly['temperature_2m'][:24]
    winds = hourly['wind_speed_10m'][:24]
    precips = hourly['precipitation'][:24]
    hours_fmt = [h.split('T')[1][:5] for h in hours]
    
    tab1, tab2, tab3 = st.tabs(["Température", "Vent", "Précipitations"])
    
    with tab1:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=hours_fmt, y=temps,
            mode='lines+markers',
            line=dict(color='#00D4FF', width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 255, 0.1)',
            hovertemplate='%{x}<br>%{y}°C<extra></extra>'
        ))
        fig_temp.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', title='Heure'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Température (°C)')
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Minimum", f"{min(temps):.1f}°C")
        c2.metric("Maximum", f"{max(temps):.1f}°C")
        c3.metric("Amplitude", f"{max(temps) - min(temps):.1f}°C")
    
    with tab2:
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(
            x=hours_fmt, y=winds,
            mode='lines+markers',
            line=dict(color='#8B5CF6', width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(139, 92, 246, 0.1)',
            hovertemplate='%{x}<br>%{y} km/h<extra></extra>'
        ))
        fig_wind.add_hline(y=25, line_dash="dash", line_color="#EAB308", annotation_text="Turbulences (25)")
        fig_wind.add_hline(y=40, line_dash="dash", line_color="#EF4444", annotation_text="Critique (40)")
        
        fig_wind.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', title='Heure'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Vent (km/h)')
        )
        st.plotly_chart(fig_wind, use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Minimum", f"{min(winds):.0f} km/h")
        c2.metric("Maximum", f"{max(winds):.0f} km/h")
        hours_above_25 = sum(1 for w in winds if w > 25)
        c3.metric("Heures > 25 km/h", f"{hours_above_25}h")
    
    with tab3:
        fig_precip = go.Figure()
        fig_precip.add_trace(go.Bar(
            x=hours_fmt, y=precips,
            marker_color='#3B82F6',
            hovertemplate='%{x}<br>%{y} mm<extra></extra>'
        ))
        fig_precip.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', title='Heure'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Précipitations (mm)')
        )
        st.plotly_chart(fig_precip, use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        total_precip = sum(precips)
        c1.metric("Total", f"{total_precip:.1f} mm")
        c2.metric("Max/heure", f"{max(precips):.1f} mm")
        rainy_hours = sum(1 for p in precips if p > 0.1)
        c3.metric("Heures de pluie", f"{rainy_hours}h")

st.divider()

# =============================================================================
# SECTION 4 : Seuils Aviation
# =============================================================================
st.markdown("### Seuils Météo pour l'Aviation")

st.markdown("""
<div class="alert-box alert-info">
    Ces seuils sont utilisés pour calculer le score aviation. Ils sont basés sur les recommandations ICAO 
    et les pratiques des compagnies low-cost opérant à Beauvais.
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Vent")
    st.markdown("""
    | Seuil | Valeur | Impact |
    |-------|--------|--------|
    | Favorable | < 25 km/h | Opérations normales |
    | Modéré | 25-40 km/h | Turbulences possibles |
    | Fort | > 40 km/h | Risque de retards |
    | Critique | > 50 km/h | Opérations suspendues |
    
    **Rafales :** Seuil critique à **60 km/h** pour les atterrissages.
    
    **Vent de travers :** Limite à **35 kts (65 km/h)** pour les B737/A320.
    """)

with col2:
    st.markdown("#### Visibilité & Phénomènes")
    st.markdown("""
    | Phénomène | Impact sur le score |
    |-----------|---------------------|
    | Brouillard | **-30 points** |
    | Neige | **-30 points** |
    | Orage | **-35 points** |
    | Pluie forte (>20mm) | **-25 points** |
    | Pluie modérée (10-20mm) | **-15 points** |
    
    **Humidité :** > 90% = risque de brouillard
    
    **Catégories ILS :**
    - CAT I : Visibilité > 800m
    - CAT II : Visibilité > 350m  
    - CAT III : Visibilité < 200m
    """)

st.divider()

# =============================================================================
# SECTION 5 : Historique récent
# =============================================================================
st.markdown("### Historique récent")

with st.spinner("Chargement de l'historique..."):
    history = get_historical_weather(days=7)

if history:
    df = pd.DataFrame({
        'Date': history['time'],
        'Temp Max (°C)': history['temperature_2m_max'],
        'Temp Min (°C)': history['temperature_2m_min'],
        'Précip (mm)': history['precipitation_sum'],
        'Vent Max (km/h)': history['wind_speed_10m_max']
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(x=df['Date'], y=df['Temp Max (°C)'], mode='lines+markers', name='Max', line=dict(color='#EF4444', width=2)))
        fig_hist.add_trace(go.Scatter(x=df['Date'], y=df['Temp Min (°C)'], mode='lines+markers', name='Min', line=dict(color='#3B82F6', width=2), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.1)'))
        fig_hist.update_layout(
            title=dict(text="Températures (7 derniers jours)", font=dict(size=13, color='#FAFAFA')),
            height=280,
            margin=dict(t=40, b=30, l=40, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
            legend=dict(orientation='h', y=1.1, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        fig_wind_hist = go.Figure()
        fig_wind_hist.add_trace(go.Bar(x=df['Date'], y=df['Vent Max (km/h)'], marker_color='#8B5CF6'))
        fig_wind_hist.add_hline(y=40, line_dash="dash", line_color="#EF4444")
        fig_wind_hist.update_layout(
            title=dict(text="Vent maximum (7 derniers jours)", font=dict(size=13, color='#FAFAFA')),
            height=280,
            margin=dict(t=40, b=30, l=40, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
        )
        st.plotly_chart(fig_wind_hist, use_container_width=True)
    
    with st.expander("Voir les données détaillées"):
        st.dataframe(df, use_container_width=True, hide_index=True)

# =============================================================================
# Section Explicative du Code
# =============================================================================
st.divider()
with st.expander("Comprendre le code de cette page"):
    st.markdown("""
    ### Architecture de la Page Météo (Meteo.py)

    Cette page fournit une **analyse météorologique complète** de Paris-Beauvais avec focus sur l'impact
    sur l'aviation. Elle combine données en temps réel, prévisions et historique.

    #### Structure du code

    **1. Imports et Configuration (lignes 1-29)**
    ```python
    import plotly.graph_objects as go
    from api.weather import (
        get_current_weather,
        get_hourly_forecast,
        get_historical_weather,
        get_aviation_conditions_forecast
    )
    ```
    - Import des fonctions météo du module API personnalisé
    - Plotly pour les visualisations interactives

    #### Section 1 : Météo Actuelle (lignes 140-217)

    **Affichage Principal**
    ```python
    icon, desc = get_weather_code_description(weather['weather_code'])

    st.markdown(f\"\"\"
    <div class="weather-main">
        <div class="weather-icon">{icon}</div>
        <div class="weather-temp">{weather['temperature_2m']}°C</div>
        <div class="weather-desc">{desc}</div>
    </div>
    \"\"\")
    ```
    - **Icône météo** : Emoji selon le code WMO (World Meteorological Organization)
    - **Grande température** : Affichage central avec style personnalisé
    - **Description** : Texte lisible (ex: "Partiellement nuageux")

    **Codes Météo WMO**
    | Code | Description | Icône |
    |------|-------------|-------|
    | 0 | Ciel dégagé | ☀️ |
    | 1-3 | Nuageux | ⛅ 🌥️ ☁️ |
    | 45, 48 | Brouillard | 🌫️ |
    | 51-67 | Pluie | 🌧️ 🌦️ |
    | 71-77 | Neige | ❄️ 🌨️ |
    | 95-99 | Orage | ⛈️ |

    **Alertes Aviation (lignes 192-213)**
    ```python
    alerts = []
    if wind > 40:
        alerts.append(("danger", "Vent fort — Risque de retards"))
    if humidity > 90:
        alerts.append(("warning", "Humidité élevée — Risque de brouillard"))
    if weather_code in [95, 96, 99]:
        alerts.append(("danger", "Orage — Opérations suspendues"))
    ```
    - **Système d'alertes** basé sur les seuils aéronautiques
    - **Classification** : success / warning / danger

    #### Section 2 : Prévisions 7 Jours (lignes 220-269)

    **Grille Compacte**
    ```python
    cols = st.columns(7)
    for i, day in enumerate(aviation_forecast[:7]):
        with cols[i]:
            # Carte pour chaque jour
            # Couleur selon le score aviation
            if day['score'] >= 80:
                border_color = "#22C55E"
            # ...
    ```
    - **7 colonnes** : Une par jour de la semaine
    - **Couleurs conditionnelles** : Vert/Jaune/Rouge selon le score
    - **Données compactes** : Temp max/min, vent, précipitations, score

    #### Section 3 : Évolution 24h (lignes 273-365)

    **Onglets (Tabs)**
    ```python
    tab1, tab2, tab3 = st.tabs(["Température", "Vent", "Précipitations"])

    with tab1:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=hours_fmt, y=temps,
            mode='lines+markers',
            line=dict(color='#00D4FF', width=3),
            fill='tozeroy',  # Remplissage sous la courbe
            fillcolor='rgba(0, 212, 255, 0.1)'
        ))
    ```
    - **st.tabs()** : Interface à onglets pour organiser les graphiques
    - **Plotly Scatter** : Courbes de température avec remplissage
    - **Métriques** : Min, Max, Amplitude calculées dynamiquement

    **Graphique Vent avec Seuils**
    ```python
    fig_wind.add_hline(y=25, line_dash="dash",
                      line_color="#EAB308",
                      annotation_text="Turbulences (25)")
    fig_wind.add_hline(y=40, line_dash="dash",
                      line_color="#EF4444",
                      annotation_text="Critique (40)")
    ```
    - **Lignes de référence** : Visualisation des seuils critiques
    - **Annotations** : Labels explicatifs sur les seuils

    #### Section 4 : Seuils Aviation (lignes 368-414)

    **Tableau des Limites Opérationnelles**
    ```python
    st.markdown(\"\"\"
    | Seuil | Valeur | Impact |
    |-------|--------|--------|
    | Favorable | < 25 km/h | Opérations normales |
    | Modéré | 25-40 km/h | Turbulences possibles |
    | Fort | > 40 km/h | Risque de retards |
    \"\"\")
    ```
    - **Standards ICAO** : Organisation de l'aviation civile internationale
    - **Spécificités B737/A320** : Avions couramment utilisés à Beauvais
    - **Catégories ILS** : Instrument Landing System (atterrissage par mauvaise visibilité)

    #### Section 5 : Historique (lignes 417-469)

    **Graphiques Comparatifs**
    ```python
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=df['Date'], y=df['Temp Max'],
        mode='lines+markers',
        name='Max',
        line=dict(color='#EF4444', width=2)
    ))
    fig_hist.add_trace(go.Scatter(
        x=df['Date'], y=df['Temp Min'],
        fill='tonexty',  # Remplir entre les deux courbes
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    ```
    - **Données 7 jours** : Températures min/max, vent, précipitations
    - **Courbe remplie** : Zone entre min et max colorée
    - **DataFrame** : Affichage tabulaire avec `st.dataframe()`

    #### Points Techniques

    **Formatage des Heures**
    ```python
    hours_fmt = [h.split('T')[1][:5] for h in hours]
    # "2025-01-22T14:00" => "14:00"
    ```
    - **ISO 8601** : Format standard des timestamps
    - **Extraction** : Découpe de la chaîne pour n'afficher que l'heure

    **Conversion Direction Vent**
    ```python
    directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    dir_idx = int((wind_dir + 22.5) / 45) % 8
    direction_text = directions[dir_idx]
    ```
    - **Conversion degrés → points cardinaux**
    - 360° divisé en 8 secteurs de 45°

    #### API OpenMeteo

    **Points de Terminaison Utilisés**
    | Endpoint | Données | Fréquence |
    |----------|---------|-----------|
    | `/weather` | Météo actuelle | Temps réel (mise à jour toutes les heures) |
    | `/forecast` | Prévisions 7j | 4 fois/jour |
    | `/historical` | Archive | Journalier depuis 1940 |

    #### Améliorations Possibles

    1. **Comparaison annuelle** : Comparer avec le même jour l'année précédente
    2. **Alertes personnalisées** : Email si conditions critiques prévues
    3. **Export PDF** : Rapport météo pour les opérations
    4. **API radar** : Afficher les images radar de pluie
    5. **Prédictions ML** : Modèle prédictif pour anticiper les conditions

    *Cette page est essentielle pour la planification des vols et l'évaluation
    des risques météorologiques.*
    """)

# =============================================================================
# Footer
# =============================================================================
st.markdown(f"""
<div class="footer">
    Données : OpenMeteo API — Mise à jour temps réel<br>
    Station : Beauvais-Tillé ({BEAUVAIS_LAT}°N, {BEAUVAIS_LON}°E)<br>
    Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)