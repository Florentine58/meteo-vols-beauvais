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

# Configuration de la page
st.set_page_config(
    page_title="Historique & Prévisions",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Historique & Prévisions")
st.markdown("*Analyse des données météo passées et prévisions pour l'aviation*")

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# =============================================================================
# Onglets principaux
# =============================================================================
tab1, tab2, tab3 = st.tabs(["🔮 Prévisions 7 jours", "📊 Historique Météo", "📈 Analyse Corrélation"])

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
            'Rafales (km/h)': history['wind_gusts_10m_max'],
            'Code Météo': history['weather_code']
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
            line=dict(color='#ef4444', width=2)
        ))
        
        fig_temp.add_trace(go.Scatter(
            x=df_history['Date'],
            y=df_history['Temp Min (°C)'],
            mode='lines',
            name='Min',
            line=dict(color='#3b82f6', width=2),
            fill='tonexty',
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
            fig_wind.add_hline(y=30, line_dash="dash", line_color="red",
                              annotation_text="Seuil perturbations")
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
# TAB 3 : Analyse de corrélation météo/aviation
# =============================================================================
with tab3:
    st.header("📈 Analyse de corrélation Météo ↔ Aviation")
    st.markdown("*Étude de l'impact des conditions météo sur les opérations aériennes*")
    
    st.info("""
    **📊 Cette analyse montre la relation entre les conditions météo et leur impact potentiel sur l'aviation.**
    
    Les données de retards de vols réels ne sont pas disponibles gratuitement. Cependant, nous pouvons 
    analyser les conditions météo passées et identifier les jours où des perturbations étaient probables.
    """)
    
    # Charger l'historique météo
    with st.spinner("Analyse des données..."):
        history = get_historical_weather(days=30)
    
    if history:
        # Créer un DataFrame avec analyse d'impact
        df_analysis = pd.DataFrame({
            'Date': history['time'],
            'Temp Moyenne': history['temperature_2m_mean'],
            'Vent Max': history['wind_speed_10m_max'],
            'Rafales': history['wind_gusts_10m_max'],
            'Précipitations': history['precipitation_sum'],
            'Code Météo': history['weather_code']
        })
        
        # Calculer un score d'impact pour chaque jour
        def calculate_impact_score(row):
            score = 100
            
            # Impact du vent
            if row['Vent Max'] > 50:
                score -= 40
            elif row['Vent Max'] > 35:
                score -= 25
            elif row['Vent Max'] > 25:
                score -= 10
            
            # Impact des rafales
            if row['Rafales'] and row['Rafales'] > 60:
                score -= 20
            elif row['Rafales'] and row['Rafales'] > 45:
                score -= 10
            
            # Impact des précipitations
            if row['Précipitations'] > 20:
                score -= 25
            elif row['Précipitations'] > 10:
                score -= 15
            elif row['Précipitations'] > 5:
                score -= 5
            
            # Impact du code météo (brouillard, orage, neige)
            code = row['Code Météo']
            if code in [45, 48]:  # Brouillard
                score -= 30
            elif code in [95, 96, 99]:  # Orage
                score -= 35
            elif code in [71, 73, 75, 77]:  # Neige
                score -= 30
            
            return max(0, min(100, score))
        
        df_analysis['Score Aviation'] = df_analysis.apply(calculate_impact_score, axis=1)
        
        # Classification des jours
        df_analysis['Impact'] = df_analysis['Score Aviation'].apply(
            lambda x: '🟢 Favorable' if x >= 80 else ('🟡 Modéré' if x >= 50 else '🔴 Difficile')
        )
        
        # Statistiques
        st.subheader("📊 Résumé des 30 derniers jours")
        
        favorable = len(df_analysis[df_analysis['Score Aviation'] >= 80])
        moderate = len(df_analysis[(df_analysis['Score Aviation'] >= 50) & (df_analysis['Score Aviation'] < 80)])
        difficult = len(df_analysis[df_analysis['Score Aviation'] < 50])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🟢 Jours favorables", favorable, f"{favorable/30*100:.0f}%")
        
        with col2:
            st.metric("🟡 Jours modérés", moderate, f"{moderate/30*100:.0f}%")
        
        with col3:
            st.metric("🔴 Jours difficiles", difficult, f"{difficult/30*100:.0f}%")
        
        with col4:
            avg_score = df_analysis['Score Aviation'].mean()
            st.metric("📊 Score moyen", f"{avg_score:.0f}/100")
        
        st.divider()
        
        # Graphique principal : Score aviation + Vent
        st.subheader("📈 Corrélation Vent ↔ Score Aviation")
        
        fig_corr = go.Figure()
        
        # Zones de couleur pour le score
        fig_corr.add_hrect(y0=80, y1=100, fillcolor="green", opacity=0.1, line_width=0)
        fig_corr.add_hrect(y0=50, y1=80, fillcolor="yellow", opacity=0.1, line_width=0)
        fig_corr.add_hrect(y0=0, y1=50, fillcolor="red", opacity=0.1, line_width=0)
        
        # Score aviation
        fig_corr.add_trace(go.Scatter(
            x=df_analysis['Date'],
            y=df_analysis['Score Aviation'],
            mode='lines+markers',
            name='Score Aviation',
            line=dict(color='#2563eb', width=2),
            yaxis='y'
        ))
        
        # Vent max (axe secondaire)
        fig_corr.add_trace(go.Bar(
            x=df_analysis['Date'],
            y=df_analysis['Vent Max'],
            name='Vent Max (km/h)',
            marker_color='rgba(239, 68, 68, 0.5)',
            yaxis='y2'
        ))
        
        fig_corr.update_layout(
            title="Relation entre le vent et le score des conditions aéronautiques",
            yaxis=dict(title='Score Aviation (0-100)', range=[0, 100]),
            yaxis2=dict(title='Vent Max (km/h)', overlaying='y', side='right', range=[0, 80]),
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        st.caption("📌 **Observation** : On constate que les jours avec un vent supérieur à 30 km/h correspondent généralement à un score aviation plus faible.")
        
        # Graphique de dispersion
        st.subheader("🔍 Analyse multifactorielle")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter plot Vent vs Score
            fig_scatter1 = px.scatter(
                df_analysis,
                x='Vent Max',
                y='Score Aviation',
                color='Impact',
                title="Vent vs Score Aviation",
                color_discrete_map={
                    '🟢 Favorable': '#22c55e',
                    '🟡 Modéré': '#eab308',
                    '🔴 Difficile': '#ef4444'
                }
            )
            fig_scatter1.update_layout(height=350)
            st.plotly_chart(fig_scatter1, use_container_width=True)
        
        with col2:
            # Scatter plot Précipitations vs Score
            fig_scatter2 = px.scatter(
                df_analysis,
                x='Précipitations',
                y='Score Aviation',
                color='Impact',
                title="Précipitations vs Score Aviation",
                color_discrete_map={
                    '🟢 Favorable': '#22c55e',
                    '🟡 Modéré': '#eab308',
                    '🔴 Difficile': '#ef4444'
                }
            )
            fig_scatter2.update_layout(height=350)
            st.plotly_chart(fig_scatter2, use_container_width=True)
        
        # Conclusions
        st.subheader("📝 Conclusions de l'analyse")
        
        # Calculer quelques stats
        windy_days = len(df_analysis[df_analysis['Vent Max'] > 30])
        rainy_days = len(df_analysis[df_analysis['Précipitations'] > 5])
        
        st.markdown(f"""
        **Sur les 30 derniers jours à Beauvais :**
        
        - **{favorable} jours ({favorable/30*100:.0f}%)** avaient des conditions favorables pour l'aviation
        - **{difficult} jours ({difficult/30*100:.0f}%)** présentaient des conditions difficiles
        - **{windy_days} jours** avec vent > 30 km/h (risque de turbulences)
        - **{rainy_days} jours** avec précipitations significatives (> 5mm)
        
        **Impact estimé :**
        - Les jours avec vent fort (>30 km/h) sont susceptibles de causer des retards de 15-30 min
        - Les jours avec brouillard ou orage peuvent entraîner des annulations
        - Score moyen de la période : **{avg_score:.0f}/100**
        """)
        
        # Tableau détaillé
        with st.expander("📋 Voir l'analyse jour par jour"):
            display_df = df_analysis[['Date', 'Vent Max', 'Précipitations', 'Score Aviation', 'Impact']].copy()
            display_df.columns = ['Date', 'Vent Max (km/h)', 'Précipitations (mm)', 'Score', 'Impact']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    else:
        st.error("❌ Impossible de charger les données pour l'analyse")

# Footer
st.divider()
st.caption("Données météo : OpenMeteo | Analyse : Projet Mineure Numérique B2")