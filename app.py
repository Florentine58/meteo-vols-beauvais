"""
BVA Monitor — Dashboard Principal
Surveillance météo et trafic aérien Paris-Beauvais
Design professionnel aviation
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Imports des modules API
from api.weather import get_current_weather, get_hourly_forecast, get_aviation_conditions_forecast, get_weather_code_description
from api.flights import get_flights_in_area, get_airport_info
from api.air_quality import get_current_air_quality, calculate_aviation_air_impact

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Météo & Vols",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS Professionnel - Design Aviation
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #00D4FF;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .main-header h1 {
        color: #FAFAFA;
        font-weight: 600;
        margin: 0;
        font-size: 1.5rem;
        letter-spacing: -0.5px;
    }
    
    .main-header .subtitle {
        color: #94A3B8;
        margin: 0.25rem 0 0 0;
        font-size: 0.875rem;
    }
    
    .header-badge {
        background: #00D4FF;
        color: #000;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .score-display {
        text-align: center;
        padding: 1rem;
    }
    
    .score-number {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .score-green { color: #22C55E; }
    .score-yellow { color: #EAB308; }
    .score-red { color: #EF4444; }
    
    .score-max {
        color: #94A3B8;
        font-size: 1.25rem;
        font-weight: 400;
    }
    
    .score-status {
        margin-top: 0.5rem;
        font-size: 0.875rem;
        color: #94A3B8;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-good {
        background: rgba(34, 197, 94, 0.15);
        color: #86EFAC;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .status-warning {
        background: rgba(234, 179, 8, 0.15);
        color: #FDE047;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    
    .status-danger {
        background: rgba(239, 68, 68, 0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .flight-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: #1A1F2E;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #00D4FF;
    }
    
    .flight-callsign {
        font-weight: 600;
        color: #FAFAFA;
        font-family: 'Courier New', monospace;
    }
    
    .flight-route {
        color: #94A3B8;
        font-size: 0.85rem;
    }
    
    .flight-status {
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .flight-airborne {
        background: rgba(0, 212, 255, 0.2);
        color: #00D4FF;
    }
    
    .flight-ground {
        background: rgba(148, 163, 184, 0.2);
        color: #94A3B8;
    }
    
    .forecast-day {
        text-align: center;
        padding: 0.75rem 0.25rem;
        background: #1A1F2E;
        border-radius: 8px;
        border: 1px solid #2D3748;
    }
    
    .forecast-day-name {
        font-weight: 600;
        color: #FAFAFA;
        font-size: 0.85rem;
    }
    
    .forecast-day-date {
        color: #64748B;
        font-size: 0.7rem;
    }
    
    .forecast-temp {
        margin: 0.5rem 0;
        font-size: 0.95rem;
    }
    
    .forecast-temp-max {
        color: #FAFAFA;
        font-weight: 600;
    }
    
    .forecast-temp-min {
        color: #64748B;
    }
    
    .forecast-score {
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }
    
    .info-box {
        background: #151B28;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        margin: 0.5rem 0;
    }
    
    .info-box-title {
        font-weight: 600;
        color: #00D4FF;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .info-box-content {
        color: #94A3B8;
        font-size: 0.8rem;
        line-height: 1.5;
    }
    
    .aqi-scale {
        display: flex;
        gap: 0.25rem;
        margin: 0.5rem 0;
    }
    
    .aqi-level {
        flex: 1;
        padding: 0.25rem;
        text-align: center;
        font-size: 0.65rem;
        border-radius: 3px;
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
    
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 600;
    }
    
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
<div class="main-header">
    <div>
        <h1>BVA Monitor — Surveillance Aéroportuaire</h1>
        <p class="subtitle">Paris-Beauvais Tillé • LFOB • Données temps réel</p>
    </div>
    <span class="header-badge">● LIVE</span>
</div>
""", unsafe_allow_html=True)

# Barre d'info
col_time, col_spacer, col_refresh = st.columns([2, 4, 1])
with col_time:
    st.caption(f"Mise à jour : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
with col_refresh:
    if st.button("Actualiser", type="secondary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
with st.spinner("Chargement..."):
    weather = get_current_weather()
    flights = get_flights_in_area()
    forecast = get_aviation_conditions_forecast()
    hourly = get_hourly_forecast(days=1)
    airport = get_airport_info()
    air_quality = get_current_air_quality()

# =============================================================================
# Section 1 : Métriques principales
# =============================================================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if weather:
        st.metric("TEMPÉRATURE", f"{weather['temperature_2m']}°C")
    else:
        st.metric("TEMPÉRATURE", "N/A")

with col2:
    if weather:
        wind = weather['wind_speed_10m']
        delta_txt = "Élevé" if wind > 30 else None
        st.metric("VENT", f"{wind} km/h", delta=delta_txt, delta_color="inverse")
    else:
        st.metric("VENT", "N/A")

with col3:
    if weather:
        humidity = weather['relative_humidity_2m']
        delta_txt = "Risque brouillard" if humidity > 90 else None
        st.metric("HUMIDITÉ", f"{humidity}%", delta=delta_txt, delta_color="inverse")
    else:
        st.metric("HUMIDITÉ", "N/A")

with col4:
    st.metric("VOLS DÉTECTÉS", len(flights))

with col5:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.metric("EN VOL", in_flight)

st.divider()

# =============================================================================
# Section 2 : Score Aviation + Trafic
# =============================================================================
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("#### Conditions aéronautiques")
    
    if forecast:
        today = forecast[0]
        score = today['score']
        
        if score >= 80:
            score_class = "score-green"
            status_class = "status-good"
            status_text = "Conditions optimales"
        elif score >= 50:
            score_class = "score-yellow"
            status_class = "status-warning"
            status_text = "Vigilance recommandée"
        else:
            score_class = "score-red"
            status_class = "status-danger"
            status_text = "Conditions défavorables"
        
        col_score, col_info = st.columns([1, 2])
        
        with col_score:
            st.markdown(f"""
            <div class="score-display">
                <span class="score-number {score_class}">{score}</span>
                <span class="score-max">/100</span>
                <div class="score-status">Score actuel</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info:
            st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)
            
            st.markdown("")
            
            if today['alerts']:
                st.markdown("**Facteurs identifiés**")
                for alert in today['alerts'][:3]:
                    st.caption(f"• {alert}")
            else:
                st.caption("Aucun facteur de risque")
            
            # Explication du score
            with st.expander("ℹ️ Comment est calculé ce score ?"):
                st.markdown("""
                **Score Aviation (0-100)** évalue les conditions de vol :
                
                | Facteur | Impact sur le score |
                |---------|---------------------|
                | Vent > 50 km/h | -40 points |
                | Vent 35-50 km/h | -25 points |
                | Vent 25-35 km/h | -10 points |
                | Rafales > 60 km/h | -20 points |
                | Précipitations > 20mm | -25 points |
                | Brouillard | -30 points |
                | Orage | -35 points |
                | Neige | -30 points |
                
                **Interprétation :**
                - 🟢 80-100 : Conditions optimales
                - 🟡 50-79 : Vigilance recommandée
                - 🔴 0-49 : Conditions difficiles
                """)
        
        # Prévisions 7 jours
        st.markdown("---")
        st.markdown("**Prévisions 7 jours**")
        
        cols = st.columns(7)
        for i, day in enumerate(forecast[:7]):
            with cols[i]:
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                icon, _ = get_weather_code_description(day['weather_code'])
                
                if day['score'] >= 80:
                    indicator = "●"
                    ind_color = "#22C55E"
                elif day['score'] >= 50:
                    indicator = "●"
                    ind_color = "#EAB308"
                else:
                    indicator = "●"
                    ind_color = "#EF4444"
                
                st.markdown(f"""
                <div class="forecast-day">
                    <div class="forecast-day-name">{date_obj.strftime('%a')}</div>
                    <div class="forecast-day-date">{date_obj.strftime('%d/%m')}</div>
                    <div style="font-size: 1.25rem; margin: 0.4rem 0;">{icon}</div>
                    <div class="forecast-temp">
                        <span class="forecast-temp-max">{day['temp_max']:.0f}°</span>
                        <span class="forecast-temp-min">/{day['temp_min']:.0f}°</span>
                    </div>
                    <div class="forecast-score" style="color: {ind_color};">{indicator} {day['score']}</div>
                </div>
                """, unsafe_allow_html=True)

with col_right:
    st.markdown("#### Trafic temps réel")
    
    if flights:
        in_flight = len([f for f in flights if not f.get('on_ground', False)])
        on_ground = len([f for f in flights if f.get('on_ground', False)])
        
        # Graphique donut
        fig = go.Figure(data=[go.Pie(
            labels=['En vol', 'Au sol'],
            values=[in_flight, on_ground],
            hole=.7,
            marker_colors=['#00D4FF', '#374151'],
            textinfo='none'
        )])
        
        fig.add_annotation(
            text=f"<b>{len(flights)}</b><br><span style='font-size:11px'>vols</span>",
            x=0.5, y=0.5,
            font_size=18,
            font_color='#FAFAFA',
            showarrow=False
        )
        
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(color='#94A3B8', size=11)
            ),
            height=180,
            margin=dict(t=10, b=30, l=10, r=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Liste des vols
        st.markdown("**Activité récente**")
        for flight in flights[:5]:
            is_flying = not flight.get('on_ground', False)
            status_class = "flight-airborne" if is_flying else "flight-ground"
            status_text = "EN VOL" if is_flying else "AU SOL"
            origin = flight['origin'] if flight['origin'] != 'N/A' else '---'
            dest = flight['destination'] if flight['destination'] != 'N/A' else '---'
            
            st.markdown(f"""
            <div class="flight-row">
                <div>
                    <span class="flight-callsign">{flight['callsign']}</span>
                    <span class="flight-route"> • {origin} → {dest}</span>
                </div>
                <span class="flight-status {status_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun vol détecté")

st.divider()

# =============================================================================
# Section 3 : Qualité de l'air et impact environnemental
# =============================================================================
st.markdown("#### Qualité de l'air & Impact environnemental")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🌬️ Qualité de l'air")
    
    if air_quality:
        aqi = air_quality.get('european_aqi', 0)
        level = air_quality.get('aqi_level', 'Inconnu')
        
        # Affichage AQI avec couleur
        if aqi <= 20:
            aqi_color = "#22C55E"
        elif aqi <= 40:
            aqi_color = "#84CC16"
        elif aqi <= 60:
            aqi_color = "#EAB308"
        elif aqi <= 80:
            aqi_color = "#F97316"
        else:
            aqi_color = "#EF4444"
        
        col_aqi, col_details = st.columns([1, 2])
        
        with col_aqi:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #151B28; border-radius: 8px;">
                <div style="font-size: 2.5rem; font-weight: 700; color: {aqi_color};">{aqi}</div>
                <div style="font-size: 0.8rem; color: #94A3B8;">AQI Européen</div>
                <div style="font-size: 0.9rem; color: {aqi_color}; font-weight: 600; margin-top: 0.25rem;">{level}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_details:
            pm25 = air_quality.get('pm2_5', 0)
            pm10 = air_quality.get('pm10', 0)
            no2 = air_quality.get('nitrogen_dioxide', 0)
            o3 = air_quality.get('ozone', 0)
            
            st.markdown(f"""
            | Polluant | Valeur | Seuil OMS |
            |----------|--------|-----------|
            | PM2.5 | **{pm25:.1f}** µg/m³ | < 15 µg/m³ |
            | PM10 | **{pm10:.1f}** µg/m³ | < 45 µg/m³ |
            | NO₂ | **{no2:.1f}** µg/m³ | < 25 µg/m³ |
            | O₃ | **{o3:.1f}** µg/m³ | < 100 µg/m³ |
            """)
        
        # Échelle AQI
        st.markdown("""
        <div class="aqi-scale">
            <div class="aqi-level" style="background: #22C55E; color: #000;">0-20<br>Excellent</div>
            <div class="aqi-level" style="background: #84CC16; color: #000;">21-40<br>Bon</div>
            <div class="aqi-level" style="background: #EAB308; color: #000;">41-60<br>Modéré</div>
            <div class="aqi-level" style="background: #F97316; color: #000;">61-80<br>Médiocre</div>
            <div class="aqi-level" style="background: #EF4444; color: #FFF;">81-100<br>Mauvais</div>
            <div class="aqi-level" style="background: #7C2D12; color: #FFF;">>100<br>Très mauvais</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Explication
        with st.expander("ℹ️ Comment est mesuré l'AQI ?"):
            st.markdown("""
            **L'Indice de Qualité de l'Air Européen (AQI)** est calculé à partir de 5 polluants :
            
            - **PM2.5** : Particules fines < 2.5 µm (pénètrent dans les poumons)
            - **PM10** : Particules < 10 µm (irritation respiratoire)
            - **NO₂** : Dioxyde d'azote (émissions véhicules/avions)
            - **O₃** : Ozone (formation par réaction chimique)
            - **SO₂** : Dioxyde de soufre (combustion)
            
            L'AQI final = valeur du polluant le plus élevé.
            
            *Source : Agence Européenne pour l'Environnement (EEA)*
            """)
    else:
        st.info("Données qualité de l'air non disponibles")

with col2:
    st.markdown("##### ✈️ Impact environnemental estimé")
    
    # Calcul de l'impact
    wind_speed = weather['wind_speed_10m'] if weather else 10
    impact = calculate_aviation_air_impact(len(flights), wind_speed)
    
    col_impact, col_emissions = st.columns([1, 2])
    
    with col_impact:
        impact_score = impact['impact_score']
        impact_color = impact['impact_color']
        impact_level = impact['impact_level']
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #151B28; border-radius: 8px;">
            <div style="font-size: 2.5rem; font-weight: 700; color: {impact_color};">{impact_score}</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">Score Impact</div>
            <div style="font-size: 0.9rem; color: {impact_color}; font-weight: 600; margin-top: 0.25rem;">{impact_level}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_emissions:
        st.markdown(f"""
        | Émission | Estimation |
        |----------|------------|
        | CO₂ | **{impact['co2_tonnes']:.1f}** tonnes |
        | NOx | **{impact['nox_kg']:.1f}** kg |
        | Particules | **{impact['pm_kg']:.1f}** kg |
        | Dispersion | **{impact['dispersion']}** |
        """)
        
        st.caption(f"Basé sur {len(flights)} vols • Vent {wind_speed:.0f} km/h")
    
    # Explication
    with st.expander("ℹ️ Comment est calculé l'impact ?"):
        st.markdown(f"""
        **Méthode de calcul (simplifiée) :**
        
        Chaque cycle LTO (Landing/Take-Off) d'un avion émet environ :
        - **2.5 tonnes de CO₂**
        - **8.5 kg de NOx** (oxydes d'azote)
        - **0.3 kg de particules fines**
        
        *Sources : ICAO, EUROCONTROL*
        
        **Facteur de dispersion :**
        
        Le vent influence la concentration des polluants :
        | Vent | Dispersion | Facteur |
        |------|------------|---------|
        | > 30 km/h | Très bonne | ×0.3 |
        | 20-30 km/h | Bonne | ×0.5 |
        | 10-20 km/h | Moyenne | ×0.7 |
        | < 10 km/h | Faible | ×1.0 |
        
        **Actuellement :** Vent de **{wind_speed:.0f} km/h** → Dispersion **{impact['dispersion']}**
        
        ⚠️ *Ces valeurs sont des estimations à but éducatif.*
        """)

st.divider()

# =============================================================================
# Section 4 : Graphiques météo COMPLETS (Temp, Vent, Pluie, Humidité)
# =============================================================================
st.markdown("#### Évolution météo — 24 heures")

if hourly:
    hours = hourly['time'][:24]
    temps = hourly['temperature_2m'][:24]
    winds = hourly['wind_speed_10m'][:24]
    precips = hourly['precipitation'][:24]
    hours_fmt = [h.split('T')[1][:5] for h in hours]
    
    # Ligne 1 : Température et Vent
    col1, col2 = st.columns(2)
    
    with col1:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=hours_fmt, y=temps,
            mode='lines',
            line=dict(color='#00D4FF', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 255, 0.08)',
            hovertemplate='%{y}°C<extra></extra>'
        ))
        fig_temp.update_layout(
            title=dict(text="🌡️ Température (°C)", font=dict(size=13, color='#FAFAFA')),
            height=220,
            margin=dict(t=35, b=30, l=40, r=15),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', tickfont=dict(size=10))
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(
            x=hours_fmt, y=winds,
            mode='lines',
            line=dict(color='#8B5CF6', width=2),
            fill='tozeroy',
            fillcolor='rgba(139, 92, 246, 0.08)',
            hovertemplate='%{y} km/h<extra></extra>'
        ))
        fig_wind.add_hline(y=30, line_dash="dash", line_color="#EF4444", line_width=1,
                          annotation_text="Seuil", annotation_font_color="#EF4444", annotation_font_size=10)
        fig_wind.update_layout(
            title=dict(text="💨 Vitesse du vent (km/h)", font=dict(size=13, color='#FAFAFA')),
            height=220,
            margin=dict(t=35, b=30, l=40, r=15),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', tickfont=dict(size=10))
        )
        st.plotly_chart(fig_wind, use_container_width=True)
    
    # Ligne 2 : Précipitations et Humidité
    col3, col4 = st.columns(2)
    
    with col3:
        fig_precip = go.Figure()
        fig_precip.add_trace(go.Bar(
            x=hours_fmt, y=precips,
            marker_color='#3B82F6',
            hovertemplate='%{y} mm<extra></extra>'
        ))
        fig_precip.update_layout(
            title=dict(text="🌧️ Précipitations (mm)", font=dict(size=13, color='#FAFAFA')),
            height=220,
            margin=dict(t=35, b=30, l=40, r=15),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', tickfont=dict(size=10))
        )
        st.plotly_chart(fig_precip, use_container_width=True)
    
    with col4:
        # Pour l'humidité, on utilise les données actuelles répétées (ou on ajoute dans l'API)
        # En attendant, on affiche un résumé météo complet
        if weather:
            humidity = weather['relative_humidity_2m']
            wind_dir = weather['wind_direction_10m']
            
            # Convertir la direction en texte
            directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
            dir_index = int((wind_dir + 22.5) / 45) % 8
            wind_dir_text = directions[dir_index]
            
            st.markdown(f"""
            <div style="background: #151B28; padding: 1.25rem; border-radius: 8px; height: 195px;">
                <div style="font-size: 0.85rem; font-weight: 600; color: #FAFAFA; margin-bottom: 1rem;">
                    💧 Conditions actuelles
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <div style="font-size: 1.75rem; font-weight: 700; color: {'#EAB308' if humidity > 80 else '#22C55E'};">{humidity}%</div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;">Humidité</div>
                    </div>
                    <div>
                        <div style="font-size: 1.75rem; font-weight: 700; color: #94A3B8;">{wind_dir_text}</div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;">Direction vent</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid #2D3748;">
                    <div style="font-size: 0.8rem; color: #94A3B8;">
                        {'⚠️ Humidité élevée - Risque de brouillard' if humidity > 90 else '✅ Visibilité normale' if humidity < 80 else '⚡ Humidité modérée'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Données non disponibles")

st.divider()

# =============================================================================
# Section 5 : Infos aéroport
# =============================================================================
st.markdown("#### Informations aéroport")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**{airport['name']}**")
    st.caption(f"IATA: {airport['code_iata']} • ICAO: {airport['code_icao']}")
    st.caption(f"Altitude: {airport['altitude']} m")

with col2:
    st.markdown("**Localisation**")
    st.caption(f"{airport['city']}, {airport['country']}")
    st.caption(f"{airport['latitude']}°N, {airport['longitude']}°E")

with col3:
    st.markdown("**Compagnies**")
    st.caption(" • ".join(airport['principales_compagnies']))

# =============================================================================
# Section Explicative du Code
# =============================================================================
st.divider()
with st.expander("📘 Comprendre le code de cette page"):
    st.markdown("""
    ### Architecture du Dashboard Principal (app.py)

    Ce fichier constitue la **page d'accueil** de l'application BVA Monitor. Il intègre toutes les données
    essentielles sur un seul écran pour une vision globale rapide.

    #### 📦 Structure du code

    **1. Configuration et Imports (lignes 1-23)**
    ```python
    import streamlit as st
    import plotly.graph_objects as go
    from api.weather import get_current_weather, ...
    from api.flights import get_flights_in_area, ...
    from api.air_quality import get_current_air_quality, ...
    ```
    - Import des bibliothèques : Streamlit pour l'interface, Plotly pour les graphiques
    - Import des modules API personnalisés pour récupérer les données

    **2. CSS Personnalisé (lignes 24-270)**
    - Style professionnel avec dégradés, cartes, badges
    - Animations (pulse sur le badge LIVE)
    - Design responsive et moderne

    **3. Chargement des Données (lignes 299-305)**
    ```python
    weather = get_current_weather()
    flights = get_flights_in_area()
    forecast = get_aviation_conditions_forecast()
    hourly = get_hourly_forecast(days=1)
    airport = get_airport_info()
    air_quality = get_current_air_quality()
    ```
    - Appels aux différentes APIs en parallèle
    - Cache Streamlit pour optimiser les performances

    #### 🔧 Sections Principales

    **Section 1 : Métriques Principales (lignes 308-340)**
    - Affichage des valeurs clés : température, vent, humidité, nombre de vols
    - Utilisation de `st.metric()` pour un affichage standardisé

    **Section 2 : Score Aviation + Trafic (lignes 343-507)**
    - **Score Aviation (0-100)** : Calcule la qualité des conditions de vol
      - Algorithme dans `api/weather.py:get_aviation_conditions_forecast()`
      - Pénalités selon le vent, précipitations, phénomènes météo
    - **Graphique Donut** : Visualisation vols en l'air vs au sol (Plotly)
    - **Prévisions 7 jours** : Grille compacte avec scores quotidiens

    **Section 3 : Qualité de l'Air & Impact (lignes 510-652)**
    - **AQI Européen** : Indice de qualité de l'air (0-100+)
      - Calcul dans `api/air_quality.py:get_current_air_quality()`
      - Basé sur PM2.5, PM10, NO₂, O₃, SO₂
    - **Impact Aviation** : Estimation des émissions du trafic aérien
      - CO₂, NOx, particules par vol
      - Facteur de dispersion selon le vent

    **Section 4 : Graphiques Météo (lignes 656-771)**
    - Utilisation de Plotly pour les graphiques interactifs
    - 4 graphiques : Température, Vent, Précipitations, Conditions actuelles
    - Données horaires sur 24h

    #### 🎯 Points Techniques Importants

    **Cache et Performance**
    ```python
    with st.spinner("Chargement..."):
        weather = get_current_weather()  # Mis en cache 5 min
    ```
    - Les fonctions API utilisent `@st.cache_data` pour limiter les appels
    - Bouton "Actualiser" vide le cache : `st.cache_data.clear()`

    **Gestion des Valeurs Manquantes**
    ```python
    if weather:
        st.metric("TEMPÉRATURE", f"{weather['temperature_2m']}°C")
    else:
        st.metric("TEMPÉRATURE", "N/A")
    ```
    - Vérifications systématiques pour éviter les erreurs

    **Couleurs Dynamiques**
    ```python
    if score >= 80:
        score_class = "score-green"
    elif score >= 50:
        score_class = "score-yellow"
    else:
        score_class = "score-red"
    ```
    - Classes CSS appliquées dynamiquement selon les valeurs

    #### 📊 Sources de Données

    | API | Données | Fréquence |
    |-----|---------|-----------|
    | **OpenMeteo** | Météo, qualité air | Temps réel |
    | **FlightRadar24** | Positions avions | 30s |
    | **Calculé** | Score aviation, impact | À la demande |

    #### 🚀 Optimisations Possibles

    1. **WebSockets** pour les vols en temps réel (actualisation auto)
    2. **Base de données** pour historiser les scores aviation
    3. **Machine Learning** pour prédire les retards selon la météo
    4. **Alertes email** si conditions critiques détectées

    *Ce dashboard est le point d'entrée de l'application et donne une vue d'ensemble complète
    de la situation à Paris-Beauvais.*
    """)

# =============================================================================
# Footer
# =============================================================================
st.markdown("""
<div class="footer">
    <b>Sources des données :</b><br>
    Météo & Qualité de l'air : <a href="https://open-meteo.com" style="color: #00D4FF;">OpenMeteo API</a> (gratuit)<br>
    Trafic aérien : <a href="https://www.flightradar24.com" style="color: #00D4FF;">FlightRadar24</a> (usage éducatif)<br>
    <br>
    Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)