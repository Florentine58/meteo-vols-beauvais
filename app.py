"""
Météo & Vols Beauvais — Dashboard Principal
Application Streamlit pour visualiser la météo et le trafic aérien à Beauvais.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Imports des modules API
from api.weather import get_current_weather, get_hourly_forecast, get_aviation_conditions_forecast, get_weather_code_description
from api.flights import get_flights_in_area, get_airport_info

# Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="Météo & Vols Beauvais",
    page_icon="✈️",
    layout="wide"
)

# =============================================================================
# En-tête
# =============================================================================
st.title("✈️ Météo & Vols Beauvais")
st.markdown("*Dashboard de surveillance météo et trafic aérien — Aéroport Paris-Beauvais (BVA)*")

# Heure de mise à jour
st.caption(f"🕐 Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")

# Bouton de rafraîchissement
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
with st.spinner("Chargement des données en temps réel..."):
    weather = get_current_weather()
    flights = get_flights_in_area()
    forecast = get_aviation_conditions_forecast()
    hourly = get_hourly_forecast(days=1)
    airport = get_airport_info()

# =============================================================================
# Section 1 : Métriques principales
# =============================================================================
st.header("📊 Vue d'ensemble")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if weather:
        icon, desc = get_weather_code_description(weather.get('weather_code', 0))
        st.metric(
            label=f"{icon} Température",
            value=f"{weather['temperature_2m']}°C",
            delta=f"{desc}"
        )
    else:
        st.metric("🌡️ Température", "N/A")

with col2:
    if weather:
        wind = weather['wind_speed_10m']
        delta_color = "inverse" if wind > 30 else "off"
        st.metric(
            label="💨 Vent",
            value=f"{wind} km/h",
            delta="Fort" if wind > 30 else "Modéré" if wind > 15 else "Faible",
            delta_color=delta_color
        )
    else:
        st.metric("💨 Vent", "N/A")

with col3:
    if weather:
        st.metric(
            label="💧 Humidité",
            value=f"{weather['relative_humidity_2m']}%"
        )
    else:
        st.metric("💧 Humidité", "N/A")

with col4:
    st.metric(
        label="✈️ Vols détectés",
        value=len(flights)
    )

with col5:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.metric(
        label="🛫 En vol",
        value=in_flight
    )

st.divider()

# =============================================================================
# Section 2 : Alertes et Score Aviation
# =============================================================================
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🔮 Conditions pour l'aviation")
    
    if forecast:
        # Score du jour
        today = forecast[0]
        score = today['score']
        
        # Affichage du score avec jauge
        if score >= 80:
            st.success(f"### 🟢 Score actuel : {score}/100")
            st.markdown("**Conditions excellentes** pour les opérations aériennes")
        elif score >= 50:
            st.warning(f"### 🟡 Score actuel : {score}/100")
            st.markdown("**Vigilance recommandée** — Conditions acceptables")
        else:
            st.error(f"### 🔴 Score actuel : {score}/100")
            st.markdown("**Conditions difficiles** — Risque de perturbations")
        
        # Alertes du jour
        if today['alerts']:
            st.markdown("**⚠️ Alertes actives :**")
            for alert in today['alerts']:
                st.markdown(f"- {alert}")
        
        # Aperçu des 3 prochains jours
        st.markdown("---")
        st.markdown("**📅 Prévisions 3 jours :**")
        
        cols = st.columns(3)
        for i, day in enumerate(forecast[1:4]):  # Jours 2, 3, 4
            with cols[i]:
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                icon, _ = get_weather_code_description(day['weather_code'])
                
                if day['score'] >= 80:
                    color = "🟢"
                elif day['score'] >= 50:
                    color = "🟡"
                else:
                    color = "🔴"
                
                st.markdown(f"**{date_obj.strftime('%A')[:3]}** {icon}")
                st.markdown(f"{color} {day['score']}/100")
    else:
        st.info("Chargement des prévisions...")

with col_right:
    st.subheader("🛫 Trafic en direct")
    
    if flights:
        # Compter par statut
        in_flight = len([f for f in flights if not f.get('on_ground', False)])
        on_ground = len([f for f in flights if f.get('on_ground', False)])
        
        # Mini graphique donut
        fig = go.Figure(data=[go.Pie(
            labels=['En vol', 'Au sol'],
            values=[in_flight, on_ground],
            hole=.6,
            marker_colors=['#22c55e', '#6b7280']
        )])
        fig.update_layout(
            showlegend=True,
            height=200,
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Liste des derniers vols
        st.markdown("**Derniers vols détectés :**")
        for flight in flights[:5]:
            status = "🛫" if not flight.get('on_ground', False) else "🅿️"
            origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
            dest = flight['destination'] if flight['destination'] != 'N/A' else '???'
            st.caption(f"{status} **{flight['callsign']}** {origin}→{dest}")
    else:
        st.info("Aucun vol détecté actuellement")

st.divider()

# =============================================================================
# Section 3 : Graphiques météo du jour
# =============================================================================
st.subheader("📈 Météo des prochaines 24h")

if hourly:
    col1, col2 = st.columns(2)
    
    # Limiter à 24h
    hours = hourly['time'][:24]
    temps = hourly['temperature_2m'][:24]
    winds = hourly['wind_speed_10m'][:24]
    
    # Formater les heures
    hours_formatted = [h.split('T')[1][:5] for h in hours]
    
    with col1:
        # Graphique température
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=hours_formatted,
            y=temps,
            mode='lines+markers',
            line=dict(color='#ef4444', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)'
        ))
        fig_temp.update_layout(
            title="🌡️ Température (°C)",
            height=250,
            margin=dict(t=40, b=40),
            xaxis_title="",
            yaxis_title="°C"
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        # Graphique vent
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(
            x=hours_formatted,
            y=winds,
            mode='lines+markers',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        # Ligne de seuil vent fort
        fig_wind.add_hline(y=30, line_dash="dash", line_color="red", 
                          annotation_text="Seuil vent fort")
        
        fig_wind.update_layout(
            title="💨 Vent (km/h)",
            height=250,
            margin=dict(t=40, b=40),
            xaxis_title="",
            yaxis_title="km/h"
        )
        st.plotly_chart(fig_wind, use_container_width=True)

else:
    st.info("Chargement des données horaires...")

st.divider()

# =============================================================================
# Section 4 : Informations aéroport
# =============================================================================
st.subheader("ℹ️ Aéroport Paris-Beauvais")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    **{airport['name']}**
    - Code IATA : `{airport['code_iata']}`
    - Code ICAO : `{airport['code_icao']}`
    """)

with col2:
    st.markdown(f"""
    **Localisation**
    - 📍 {airport['city']}, {airport['country']}
    - 🌐 {airport['latitude']}°N, {airport['longitude']}°E
    """)

with col3:
    st.markdown(f"""
    **Compagnies principales**
    """)
    for company in airport['principales_compagnies']:
        st.markdown(f"- ✈️ {company}")

# =============================================================================
# Footer
# =============================================================================
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("📡 Données vols : FlightRadar24")

with col2:
    st.caption("🌤️ Données météo : OpenMeteo")

with col3:
    st.caption("🎓 Projet Mineure Numérique B2 — 2025")