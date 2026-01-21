"""
Page Météo — Affiche les données météorologiques de Beauvais
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import direct depuis la racine du projet
from api.weather import get_current_weather, get_hourly_forecast, BEAUVAIS_LAT, BEAUVAIS_LON

# Configuration de la page
st.set_page_config(
    page_title="Météo Beauvais",
    layout="wide"
)

st.title("🌤️ Météo Beauvais")
st.markdown(f"*Données météorologiques en temps réel — Coordonnées : {BEAUVAIS_LAT}, {BEAUVAIS_LON}*")

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.rerun()

st.divider()


# SECTION 1 : Météo actuelle

st.header("Conditions actuelles")

weather = get_current_weather()

if weather:
    # Métriques principales sur une ligne
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ Température",
            value=f"{weather['temperature_2m']}°C"
        )
    
    with col2:
        st.metric(
            label="💧 Humidité",
            value=f"{weather['relative_humidity_2m']}%"
        )
    
    with col3:
        st.metric(
            label="💨 Vent",
            value=f"{weather['wind_speed_10m']} km/h"
        )
    
    with col4:
        st.metric(
            label="🧭 Direction",
            value=f"{weather['wind_direction_10m']}°"
        )
    
    # Interprétation de la direction du vent
    def get_wind_direction_text(degrees):
        directions = [
            (0, "Nord"), (45, "Nord-Est"), (90, "Est"), (135, "Sud-Est"),
            (180, "Sud"), (225, "Sud-Ouest"), (270, "Ouest"), (315, "Nord-Ouest"), (360, "Nord")
        ]
        for i in range(len(directions) - 1):
            if directions[i][0] <= degrees < directions[i+1][0]:
                return directions[i][1]
        return "Nord"
    
    wind_text = get_wind_direction_text(weather['wind_direction_10m'])
    st.info(f"Le vent souffle actuellement vers le **{wind_text}** à **{weather['wind_speed_10m']} km/h**")
    
    # Code météo (interprétation)
    weather_codes = {
        0: "☀️ Ciel dégagé",
        1: "🌤️ Peu nuageux",
        2: "⛅ Partiellement nuageux",
        3: "☁️ Couvert",
        45: "🌫️ Brouillard",
        48: "🌫️ Brouillard givrant",
        51: "🌧️ Bruine légère",
        53: "🌧️ Bruine modérée",
        55: "🌧️ Bruine dense",
        61: "🌧️ Pluie légère",
        63: "🌧️ Pluie modérée",
        65: "🌧️ Pluie forte",
        71: "🌨️ Neige légère",
        73: "🌨️ Neige modérée",
        75: "🌨️ Neige forte",
        95: "⛈️ Orage"
    }
    
    weather_code = weather.get('weather_code', 0)
    weather_description = weather_codes.get(weather_code, "❓ Inconnu")
    st.subheader(f"Conditions : {weather_description}")

else:
    st.error("❌ Impossible de récupérer les données météo actuelles.")

st.divider()


# SECTION 2 : Prévisions horaires

st.header("Prévisions sur 24 heures")

forecast = get_hourly_forecast(days=1)

if forecast:
    # Créer un graphique avec Plotly
    hours = forecast['time'][:24]  # Limiter à 24h
    temperatures = forecast['temperature_2m'][:24]
    wind_speeds = forecast['wind_speed_10m'][:24]
    
    # Formater les heures pour l'affichage
    hours_formatted = [h.split('T')[1][:5] for h in hours]  # Extraire HH:MM
    
    # Graphique température
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=hours_formatted,
        y=temperatures,
        mode='lines+markers',
        name='Température',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=8)
    ))
    fig_temp.update_layout(
        title="🌡️ Température (°C)",
        xaxis_title="Heure",
        yaxis_title="°C",
        height=300,
        template="plotly_white"
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # Graphique vent
    fig_wind = go.Figure()
    fig_wind.add_trace(go.Scatter(
        x=hours_formatted,
        y=wind_speeds,
        mode='lines+markers',
        name='Vent',
        line=dict(color='#4ECDC4', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(78, 205, 196, 0.2)'
    ))
    fig_wind.update_layout(
        title="💨 Vitesse du vent (km/h)",
        xaxis_title="Heure",
        yaxis_title="km/h",
        height=300,
        template="plotly_white"
    )
    st.plotly_chart(fig_wind, use_container_width=True)
    
    # Tableau des prévisions
    with st.expander("📋 Voir le tableau des prévisions"):
        import pandas as pd
        df = pd.DataFrame({
            'Heure': hours_formatted,
            'Température (°C)': temperatures,
            'Vent (km/h)': wind_speeds,
            'Précipitations (mm)': forecast['precipitation'][:24]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.error("❌ Impossible de récupérer les prévisions météo.")

st.divider()


# SECTION 3 : Impact sur l'aviation

st.header("Impact sur l'aviation")

if weather:
    # Analyse des conditions pour l'aviation
    conditions = []
    
    # Vent
    wind_speed = weather['wind_speed_10m']
    if wind_speed < 20:
        conditions.append((" Vent faible", "Conditions favorables pour les opérations aériennes"))
    elif wind_speed < 40:
        conditions.append((" Vent modéré", "Légères turbulences possibles à l'atterrissage"))
    else:
        conditions.append((" Vent fort", "Risque de retards ou déroutements"))
    
    # Visibilité (si disponible dans les prévisions)
    if forecast and 'visibility' in forecast:
        visibility = forecast['visibility'][0] / 1000  # Convertir en km
        if visibility > 10:
            conditions.append((" Bonne visibilité", f"{visibility:.0f} km — Conditions VFR"))
        elif visibility > 5:
            conditions.append(("Visibilité moyenne", f"{visibility:.0f} km — Approches ILS possibles"))
        else:
            conditions.append((" Mauvaise visibilité", f"{visibility:.0f} km — Risque de retards"))
    
    # Afficher les conditions
    for status, description in conditions:
        st.markdown(f"**{status}** — {description}")

# Footer
st.divider()
st.caption("Données fournies par OpenMeteo API — Mise à jour en temps réel")