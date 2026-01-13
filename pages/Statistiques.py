"""
Page Statistiques — Graphiques et analyses du trafic aérien
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import direct depuis la racine du projet
from api.flights import get_flights_in_area, get_airport_info, get_airlines_stats, get_aircraft_stats
from api.weather import get_current_weather, get_hourly_forecast

# Configuration de la page
st.set_page_config(
    page_title="Statistiques",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Statistiques & Analyses")
st.markdown("*Analyse du trafic aérien et corrélation avec la météo*")

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.rerun()

st.divider()

# =============================================================================
# Récupération des données
# =============================================================================
with st.spinner("Chargement des données..."):
    flights = get_flights_in_area()
    weather = get_current_weather()
    forecast = get_hourly_forecast(days=1)

# =============================================================================
# SECTION 1 : Résumé global
# =============================================================================
st.header("📈 Vue d'ensemble")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("✈️ Vols détectés", len(flights))

with col2:
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    st.metric("🛫 En vol", in_flight)

with col3:
    on_ground = len([f for f in flights if f.get('on_ground', False)])
    st.metric("🅿️ Au sol", on_ground)

with col4:
    if weather:
        st.metric("🌡️ Température", f"{weather['temperature_2m']}°C")

st.divider()

# =============================================================================
# SECTION 2 : Statistiques des compagnies aériennes
# =============================================================================
st.header("🏢 Compagnies aériennes")

if flights:
    airlines_stats = get_airlines_stats(flights)
    
    if airlines_stats:
        # Convertir en DataFrame pour le graphique
        df_airlines = pd.DataFrame([
            {"Compagnie": k, "Vols": v} 
            for k, v in sorted(airlines_stats.items(), key=lambda x: x[1], reverse=True)
        ])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Graphique en barres
            fig_airlines = px.bar(
                df_airlines,
                x="Compagnie",
                y="Vols",
                color="Vols",
                color_continuous_scale="Viridis",
                title="Nombre de vols par compagnie"
            )
            fig_airlines.update_layout(height=400)
            st.plotly_chart(fig_airlines, use_container_width=True)
        
        with col2:
            # Graphique camembert
            fig_pie = px.pie(
                df_airlines,
                values="Vols",
                names="Compagnie",
                title="Répartition du trafic"
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher les statistiques des compagnies.")
else:
    st.info("Aucun vol détecté pour analyser les compagnies.")

st.divider()

# =============================================================================
# SECTION 3 : Types d'avions
# =============================================================================
st.header("🛩️ Types d'avions")

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
            color_continuous_scale="Plasma",
            title="Nombre de vols par type d'avion"
        )
        fig_aircraft.update_layout(height=350)
        st.plotly_chart(fig_aircraft, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher les types d'avions.")
else:
    st.info("Aucun vol détecté pour analyser les types d'avions.")

st.divider()

# =============================================================================
# SECTION 4 : Altitudes et vitesses
# =============================================================================
st.header("📏 Altitudes et vitesses")

if flights:
    # Filtrer les avions en vol uniquement
    flying = [f for f in flights if not f.get('on_ground', False) and f['altitude'] > 0]
    
    if flying:
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des altitudes
            altitudes = [f['altitude'] for f in flying]
            fig_alt = go.Figure()
            fig_alt.add_trace(go.Histogram(
                x=altitudes,
                nbinsx=20,
                marker_color='#4ECDC4'
            ))
            fig_alt.update_layout(
                title="Distribution des altitudes (ft)",
                xaxis_title="Altitude (pieds)",
                yaxis_title="Nombre d'avions",
                height=350
            )
            st.plotly_chart(fig_alt, use_container_width=True)
            
            # Stats
            avg_alt = sum(altitudes) / len(altitudes)
            st.info(f"**Altitude moyenne :** {avg_alt:.0f} ft ({avg_alt * 0.3048:.0f} m)")
        
        with col2:
            # Distribution des vitesses
            speeds = [f['ground_speed'] for f in flying]
            fig_speed = go.Figure()
            fig_speed.add_trace(go.Histogram(
                x=speeds,
                nbinsx=20,
                marker_color='#FF6B6B'
            ))
            fig_speed.update_layout(
                title="Distribution des vitesses (kts)",
                xaxis_title="Vitesse (noeuds)",
                yaxis_title="Nombre d'avions",
                height=350
            )
            st.plotly_chart(fig_speed, use_container_width=True)
            
            # Stats
            avg_speed = sum(speeds) / len(speeds)
            st.info(f"**Vitesse moyenne :** {avg_speed:.0f} kts ({avg_speed * 1.852:.0f} km/h)")
    else:
        st.info("Aucun avion en vol détecté pour analyser les altitudes et vitesses.")
else:
    st.info("Aucun vol détecté.")

st.divider()

# =============================================================================
# SECTION 5 : Corrélation météo / trafic
# =============================================================================
st.header("🌤️ ↔️ ✈️ Corrélation Météo / Trafic")

if weather and flights:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Conditions météo actuelles")
        
        # Évaluation des conditions pour le vol
        conditions_score = 100  # Score parfait
        
        wind_speed = weather['wind_speed_10m']
        if wind_speed > 40:
            conditions_score -= 40
            st.error(f"❌ **Vent fort** : {wind_speed} km/h — Impact majeur sur le trafic")
        elif wind_speed > 25:
            conditions_score -= 20
            st.warning(f"⚠️ **Vent modéré** : {wind_speed} km/h — Turbulences possibles")
        else:
            st.success(f"✅ **Vent faible** : {wind_speed} km/h — Conditions favorables")
        
        # Humidité
        humidity = weather['relative_humidity_2m']
        if humidity > 90:
            conditions_score -= 15
            st.warning(f"⚠️ **Humidité très élevée** : {humidity}% — Risque de brouillard")
        else:
            st.success(f"✅ **Humidité normale** : {humidity}%")
        
        st.divider()
        
        # Score global
        if conditions_score >= 80:
            st.success(f"### 🟢 Score météo : {conditions_score}/100")
            st.markdown("Conditions excellentes pour les opérations aériennes")
        elif conditions_score >= 50:
            st.warning(f"### 🟡 Score météo : {conditions_score}/100")
            st.markdown("Conditions acceptables, vigilance recommandée")
        else:
            st.error(f"### 🔴 Score météo : {conditions_score}/100")
            st.markdown("Conditions difficiles, retards possibles")
    
    with col2:
        st.markdown("### Analyse du trafic")
        
        st.metric("Vols dans la zone", len(flights))
        
        in_flight = len([f for f in flights if not f.get('on_ground', False)])
        st.metric("Avions en vol", in_flight)
        
        # Analyse
        if len(flights) > 10:
            st.success("📈 **Trafic dense** — Activité importante sur l'aéroport")
        elif len(flights) > 5:
            st.info("📊 **Trafic modéré** — Activité normale")
        elif len(flights) > 0:
            st.warning("📉 **Trafic faible** — Activité réduite")
        else:
            st.error("❌ **Aucun trafic** — Peut être lié aux conditions météo")
        
        # Interprétation
        st.divider()
        if wind_speed > 30 and len(flights) < 5:
            st.markdown("💡 **Observation** : Le vent fort pourrait expliquer le faible trafic.")
        elif conditions_score >= 80 and len(flights) > 5:
            st.markdown("💡 **Observation** : Les bonnes conditions météo favorisent un trafic normal.")
else:
    st.info("Données insuffisantes pour l'analyse de corrélation.")

# =============================================================================
# SECTION 6 : Tableau récapitulatif
# =============================================================================
st.divider()
st.header("📋 Données brutes")

with st.expander("Voir le tableau des vols"):
    if flights:
        df_flights = pd.DataFrame(flights)
        # Sélectionner les colonnes pertinentes
        columns_to_show = ['callsign', 'airline_icao', 'aircraft_type', 'origin', 'destination', 'altitude', 'ground_speed', 'on_ground']
        df_display = df_flights[[c for c in columns_to_show if c in df_flights.columns]]
        df_display.columns = ['Callsign', 'Compagnie', 'Avion', 'Origine', 'Destination', 'Altitude (ft)', 'Vitesse (kts)', 'Au sol']
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée à afficher.")

# Footer
st.divider()
st.caption("Analyse générée avec Plotly — Données FlightRadar24 & OpenMeteo")