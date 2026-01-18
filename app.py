"""
Météo & Vols Beauvais — Dashboard Principal
Version professionnelle avec design aviation
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Imports des modules API
from api.weather import get_current_weather, get_hourly_forecast, get_aviation_conditions_forecast, get_weather_code_description
from api.flights import get_flights_in_area, get_airport_info

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Météo & Vols",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS Personnalisé - Design Aviation Professionnel
# =============================================================================
st.markdown("""
<style>
    /* Import police moderne */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Style global */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* En-tête principal */
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
    
    /* Section card */
    .section-card {
        background: #151B28;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #2D3748;
        margin-bottom: 1rem;
    }
    
    /* Score aviation */
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
    
    /* Status badges */
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
    
    /* Flight list */
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
    
    /* Forecast day card */
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
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #64748B;
        font-size: 0.75rem;
        border-top: 1px solid #2D3748;
        margin-top: 2rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom metrics */
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 600;
    }
    
    /* Dividers */
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
        st.metric("HUMIDITÉ", f"{weather['relative_humidity_2m']}%")
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
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Conditions aéronautiques")
    
    if forecast:
        today = forecast[0]
        score = today['score']
        
        # Couleur selon le score
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
                for alert in today['alerts']:
                    # Nettoyer les emojis
                    alert_clean = alert.replace("🌪️", "•").replace("💨", "•").replace("⚠️", "•").replace("🌧️", "•").replace("🌫️", "•").replace("⛈️", "•").replace("🌨️", "•")
                    st.caption(alert_clean)
            else:
                st.caption("Aucun facteur de risque")
        
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
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Trafic temps réel")
    
    if flights:
        in_flight = len([f for f in flights if not f.get('on_ground', False)])
        on_ground = len([f for f in flights if f.get('on_ground', False)])
        
        # Graphique
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
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# =============================================================================
# Section 3 : Graphiques météo
# =============================================================================
st.markdown("#### Évolution météo — 24 heures")

if hourly:
    col1, col2 = st.columns(2)
    
    hours = hourly['time'][:24]
    temps = hourly['temperature_2m'][:24]
    winds = hourly['wind_speed_10m'][:24]
    hours_fmt = [h.split('T')[1][:5] for h in hours]
    
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
            title=dict(text="Température (°C)", font=dict(size=13, color='#FAFAFA')),
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
            title=dict(text="Vitesse du vent (km/h)", font=dict(size=13, color='#FAFAFA')),
            height=220,
            margin=dict(t=35, b=30, l=40, r=15),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', tickfont=dict(size=10))
        )
        st.plotly_chart(fig_wind, use_container_width=True)

st.divider()

# =============================================================================
# Section 4 : Infos aéroport
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
# Footer
# =============================================================================
st.markdown("""
<div class="footer">
    Sources : OpenMeteo API • FlightRadar24<br>
    Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)