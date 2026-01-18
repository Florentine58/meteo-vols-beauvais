"""
Page Historique & Prévisions — Analyse des données passées et futures
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Imports des modules API
from api.weather import get_historical_weather, get_aviation_conditions_forecast, get_weather_code_description
from api.opensky import get_historical_flights_in_area, get_daily_flight_counts

# Configuration de la page
st.set_page_config(
    page_title="Historique & Prévisions",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Historique & Prévisions")
st.markdown("*Analyse des données passées et prévisions météo pour l'aviation*")

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# =============================================================================
# Onglets principaux
# =============================================================================
tab1, tab2, tab3 = st.tabs(["🌤️ Prévisions 7 jours", "📊 Historique Météo", "✈️ Historique Vols"])

# =============================================================================
# TAB 1 : Prévisions 7 jours avec alertes aviation
# =============================================================================
with tab1:
    st.header("🔮 Prévisions météo et impact aviation")
    st.markdown("*Analyse des 7 prochains jours pour anticiper les perturbations*")
    
    with st.spinner("Chargement des prévisions..."):
        forecast = get_aviation_conditions_forecast()
    
    if forecast:
        # Afficher les alertes importantes en premier
        alerts_today = [day for day in forecast if day['level'] == 'red']
        alerts_warning = [day for day in forecast if day['level'] == 'yellow']
        
        if alerts_today:
            st.error(f"🚨 **{len(alerts_today)} jour(s) avec conditions difficiles cette semaine !**")
        elif alerts_warning:
            st.warning(f"⚠️ **{len(alerts_warning)} jour(s) nécessitant une vigilance**")
        else:
            st.success("✅ **Conditions favorables pour toute la semaine !**")
        
        st.divider()
        
        # Grille des 7 jours
        cols = st.columns(7)
        
        for i, day in enumerate(forecast):
            with cols[i]:
                # Couleur de fond selon le score
                if day['level'] == 'green':
                    st.markdown(f"### 🟢")
                elif day['level'] == 'yellow':
                    st.markdown(f"### 🟡")
                else:
                    st.markdown(f"### 🔴")
                
                # Date
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                st.markdown(f"**{date_obj.strftime('%a')}**")
                st.caption(date_obj.strftime('%d/%m'))
                
                # Icône météo
                icon, desc = get_weather_code_description(day['weather_code'])
                st.markdown(f"## {icon}")
                
                # Températures
                st.markdown(f"**{day['temp_max']:.0f}°** / {day['temp_min']:.0f}°")
                
                # Vent
                st.caption(f"💨 {day['wind_max']:.0f} km/h")
                
                # Score
                st.metric("Score", f"{day['score']}/100")
        
        st.divider()
        
        # Détails des alertes par jour
        st.subheader("📋 Détails des prévisions")
        
        for day in forecast:
            with st.expander(f"{day['date_formatted']} — {day['status']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Conditions météo**")
                    icon, desc = get_weather_code_description(day['weather_code'])
                    st.markdown(f"- {icon} {desc}")
                    st.markdown(f"- 🌡️ Températures : {day['temp_min']:.0f}°C à {day['temp_max']:.0f}°C")
                    st.markdown(f"- 💨 Vent max : {day['wind_max']:.0f} km/h")
                    if day['wind_gusts']:
                        st.markdown(f"- 🌪️ Rafales : {day['wind_gusts']:.0f} km/h")
                    st.markdown(f"- 🌧️ Précipitations : {day['precipitation']:.1f} mm")
                
                with col2:
                    st.markdown("**Impact aviation**")
                    st.markdown(f"**Score : {day['score']}/100**")
                    
                    if day['alerts']:
                        st.markdown("**Alertes :**")
                        for alert in day['alerts']:
                            st.markdown(f"- {alert}")
                    else:
                        st.success("Aucune alerte — Conditions optimales")
        
        # Graphique des scores sur 7 jours
        st.subheader("📈 Évolution du score aviation")
        
        df_forecast = pd.DataFrame(forecast)
        
        fig_score = go.Figure()
        
        # Zones de couleur
        fig_score.add_hrect(y0=80, y1=100, fillcolor="green", opacity=0.1, line_width=0)
        fig_score.add_hrect(y0=50, y1=80, fillcolor="yellow", opacity=0.1, line_width=0)
        fig_score.add_hrect(y0=0, y1=50, fillcolor="red", opacity=0.1, line_width=0)
        
        # Courbe des scores
        fig_score.add_trace(go.Scatter(
            x=df_forecast['date_formatted'],
            y=df_forecast['score'],
            mode='lines+markers',
            name='Score aviation',
            line=dict(color='#2563eb', width=3),
            marker=dict(size=12)
        ))
        
        fig_score.update_layout(
            title="Score des conditions aéronautiques sur 7 jours",
            yaxis_title="Score (0-100)",
            yaxis_range=[0, 100],
            height=350
        )
        
        st.plotly_chart(fig_score, use_container_width=True)
        
    else:
        st.error("❌ Impossible de charger les prévisions météo")

# =============================================================================
# TAB 2 : Historique Météo (30 jours)
# =============================================================================
with tab2:
    st.header("📊 Historique météo — 30 derniers jours")
    
    # Sélection de la période
    period = st.selectbox(
        "Période d'analyse",
        options=[7, 14, 30],
        format_func=lambda x: f"{x} derniers jours",
        index=2
    )
    
    with st.spinner(f"Chargement de l'historique météo ({period} jours)..."):
        history = get_historical_weather(days=period)
    
    if history:
        # Convertir en DataFrame
        df_history = pd.DataFrame({
            'Date': history['time'],
            'Temp Max (°C)': history['temperature_2m_max'],
            'Temp Min (°C)': history['temperature_2m_min'],
            'Temp Moyenne (°C)': history['temperature_2m_mean'],
            'Précipitations (mm)': history['precipitation_sum'],
            'Vent Max (km/h)': history['wind_speed_10m_max'],
            'Rafales (km/h)': history['wind_gusts_10m_max']
        })
        
        # Statistiques résumées
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_temp = df_history['Temp Moyenne (°C)'].mean()
            st.metric("🌡️ Temp moyenne", f"{avg_temp:.1f}°C")
        
        with col2:
            total_precip = df_history['Précipitations (mm)'].sum()
            st.metric("🌧️ Total précipitations", f"{total_precip:.1f} mm")
        
        with col3:
            max_wind = df_history['Vent Max (km/h)'].max()
            st.metric("💨 Vent max", f"{max_wind:.0f} km/h")
        
        with col4:
            rainy_days = len(df_history[df_history['Précipitations (mm)'] > 1])
            st.metric("☔ Jours de pluie", rainy_days)
        
        st.divider()
        
        # Graphique des températures
        fig_temp = go.Figure()
        
        fig_temp.add_trace(go.Scatter(
            x=df_history['Date'],
            y=df_history['Temp Max (°C)'],
            mode='lines',
            name='Max',
            line=dict(color='#ef4444', width=2),
            fill='tonexty'
        ))
        
        fig_temp.add_trace(go.Scatter(
            x=df_history['Date'],
            y=df_history['Temp Min (°C)'],
            mode='lines',
            name='Min',
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        fig_temp.update_layout(
            title="🌡️ Évolution des températures",
            yaxis_title="Température (°C)",
            height=350
        )
        
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Graphique vent et précipitations
        col1, col2 = st.columns(2)
        
        with col1:
            fig_wind = px.bar(
                df_history,
                x='Date',
                y='Vent Max (km/h)',
                title="💨 Vent maximum quotidien",
                color='Vent Max (km/h)',
                color_continuous_scale='Blues'
            )
            fig_wind.update_layout(height=300)
            st.plotly_chart(fig_wind, use_container_width=True)
        
        with col2:
            fig_precip = px.bar(
                df_history,
                x='Date',
                y='Précipitations (mm)',
                title="🌧️ Précipitations quotidiennes",
                color='Précipitations (mm)',
                color_continuous_scale='Teal'
            )
            fig_precip.update_layout(height=300)
            st.plotly_chart(fig_precip, use_container_width=True)
        
        # Tableau des données
        with st.expander("📋 Voir le tableau complet"):
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        
    else:
        st.error("❌ Impossible de charger l'historique météo")

# =============================================================================
# TAB 3 : Historique Vols (OpenSky)
# =============================================================================
with tab3:
    st.header("✈️ Historique des vols — Aéroport de Beauvais")
    st.markdown("*Données fournies par OpenSky Network*")
    
    st.info("⏳ **Note** : L'API OpenSky peut prendre quelques secondes à répondre. Les données sont disponibles jusqu'à 30 jours en arrière.")
    
    # Sélection de la période
    col1, col2 = st.columns(2)
    
    with col1:
        days_back = st.slider("Nombre de jours", min_value=1, max_value=7, value=7)
    
    with col2:
        st.markdown("")
        load_data = st.button("📥 Charger les données OpenSky")
    
    if load_data:
        with st.spinner(f"Chargement des vols des {days_back} derniers jours..."):
            end = datetime.now()
            begin = end - timedelta(days=days_back)
            flights_data = get_historical_flights_in_area(begin, end)
        
        if flights_data and flights_data['total'] > 0:
            st.success(f"✅ **{flights_data['total']} vols** trouvés sur la période")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🛬 Arrivées", len(flights_data['arrivals']))
            
            with col2:
                st.metric("🛫 Départs", len(flights_data['departures']))
            
            with col3:
                avg_per_day = flights_data['total'] / days_back
                st.metric("📊 Moyenne/jour", f"{avg_per_day:.1f}")
            
            st.divider()
            
            # Afficher les arrivées
            if flights_data['arrivals']:
                st.subheader("🛬 Dernières arrivées")
                
                arrivals_df = pd.DataFrame(flights_data['arrivals'])
                arrivals_df['arrival_time'] = arrivals_df['arrival_time'].dt.strftime('%d/%m %H:%M')
                
                st.dataframe(
                    arrivals_df[['callsign', 'origin', 'arrival_time']].head(20),
                    column_config={
                        'callsign': 'Callsign',
                        'origin': 'Origine',
                        'arrival_time': 'Heure arrivée'
                    },
                    use_container_width=True,
                    hide_index=True
                )
            
            # Afficher les départs
            if flights_data['departures']:
                st.subheader("🛫 Derniers départs")
                
                departures_df = pd.DataFrame(flights_data['departures'])
                departures_df['departure_time'] = departures_df['departure_time'].dt.strftime('%d/%m %H:%M')
                
                st.dataframe(
                    departures_df[['callsign', 'destination', 'departure_time']].head(20),
                    column_config={
                        'callsign': 'Callsign',
                        'destination': 'Destination',
                        'departure_time': 'Heure départ'
                    },
                    use_container_width=True,
                    hide_index=True
                )
        
        else:
            st.warning("⚠️ Aucun vol trouvé pour cette période. L'aéroport de Beauvais peut avoir peu de trafic certains jours.")
    
    else:
        st.markdown("👆 Clique sur **Charger les données** pour récupérer l'historique des vols.")
        st.caption("L'API OpenSky est gratuite mais peut être lente. Sois patient !")

# Footer
st.divider()
st.caption("Données météo : OpenMeteo | Données vols : OpenSky Network")