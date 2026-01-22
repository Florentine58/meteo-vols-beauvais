"""
Page Analyse Historique — Corrélation Météo & Aviation
Corrections : sélecteur dates, trafic temps réel, tendances multi-années
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports des modules API
from api.weather import (
    get_current_weather, 
    get_historical_weather, 
    get_long_term_historical_weather, 
    get_aviation_conditions_forecast,
    get_weather_code_description
)
from api.flights import get_flights_in_area, get_airlines_stats

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Analyse Historique",
    page_icon="📊",
    layout="wide"
)

# =============================================================================
# CSS Professionnel
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
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    .stat-value { font-size: 1.75rem; font-weight: 700; color: #FAFAFA; }
    .stat-label { font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.25rem; }
    .stat-green { color: #22C55E; }
    .stat-yellow { color: #EAB308; }
    .stat-red { color: #EF4444; }
    .stat-blue { color: #00D4FF; }
    .stat-orange { color: #F97316; }
    .stat-gray { color: #94A3B8; }
    
    .flight-card {
        background: #1A1F2E;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #00D4FF;
    }
    
    .alert-box { padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0; font-size: 0.85rem; }
    .alert-success { background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22C55E; color: #86EFAC; }
    .alert-warning { background: rgba(234, 179, 8, 0.1); border-left: 3px solid #EAB308; color: #FDE047; }
    .alert-danger { background: rgba(239, 68, 68, 0.1); border-left: 3px solid #EF4444; color: #FCA5A5; }
    .alert-info { background: rgba(0, 212, 255, 0.1); border-left: 3px solid #00D4FF; color: #7DD3FC; }
    
    .methodology-box {
        background: #151B28;
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        margin: 1rem 0;
    }
    
    .footer { text-align: center; padding: 1.5rem; color: #64748B; font-size: 0.75rem; border-top: 1px solid #2D3748; margin-top: 2rem; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    hr { border: none; border-top: 1px solid #2D3748; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Fonction de classification des vols
# =============================================================================
def classify_flight(flight):
    """Classifie un vol : arrivée BVA, départ BVA, ou transit."""
    origin = flight.get('origin', 'N/A')
    destination = flight.get('destination', 'N/A')
    
    if destination in ['BVA', 'LFOB']:
        return 'arrival'
    elif origin in ['BVA', 'LFOB']:
        return 'departure'
    else:
        return 'transit'

# =============================================================================
# En-tête
# =============================================================================
st.markdown("""
<div class="page-header">
    <h1>📊 Analyse Historique & Corrélations</h1>
    <p>Étude de l'impact météorologique sur les opérations aériennes</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Onglets
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🌡️ Évolution Météo",
    "✈️ Trafic Actuel", 
    "📈 Impact Météo/Aviation",
    "🌍 Tendances Climatiques"
])

# =============================================================================
# TAB 1 : Évolution Météo (CORRIGÉ - sélecteur de dates flexible)
# =============================================================================
with tab1:
    st.markdown("### Évolution météorologique à Beauvais")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        period_choice = st.selectbox(
            "Période d'analyse",
            options=["7 jours", "14 jours", "30 jours", "90 jours", "Personnalisé"],
            index=2
        )
    
    # Calcul de la période
    if period_choice == "Personnalisé":
        with col2:
            # Date de fin = hier (données disponibles)
            max_date = datetime.now().date() - timedelta(days=1)
            min_date = max_date - timedelta(days=730)  # Max 2 an en arrière
            
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input(
                    "Date début",
                    value=max_date - timedelta(days=30),
                    min_value=min_date,
                    max_value=max_date
                )
            with col_end:
                end_date = st.date_input(
                    "Date fin",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Calculer le nombre de jours
            days = (end_date - start_date).days
            if days <= 0:
                st.error("La date de fin doit être après la date de début")
                days = 30
            elif days > 90:
                st.warning("Période limitée à 90 jours pour les données détaillées")
                days = 90
    else:
        days = int(period_choice.split()[0])
    
    with col3:
        if st.button("🔄 Actualiser", key="refresh_meteo"):
            st.rerun()
    
    # Chargement des données
    with st.spinner("Chargement des données météo..."):
        history = get_historical_weather(days=days)
    
    if history and history.get('time'):
        df = pd.DataFrame({
            'Date': history['time'],
            'Temp Max': history['temperature_2m_max'],
            'Temp Min': history['temperature_2m_min'],
            'Temp Moy': history['temperature_2m_mean'],
            'Précip': history['precipitation_sum'],
            'Vent Max': history['wind_speed_10m_max'],
            'Rafales': history['wind_gusts_10m_max']
        })
        
        # Stats rapides
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_temp = df['Temp Moy'].mean()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-blue">{avg_temp:.1f}°C</div>
                <div class="stat-label">Température moyenne</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_precip = df['Précip'].sum()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{total_precip:.1f} mm</div>
                <div class="stat-label">Précipitations totales</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            max_wind = df['Vent Max'].max()
            color = "stat-red" if max_wind > 50 else "stat-yellow" if max_wind > 35 else ""
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value {color}">{max_wind:.0f} km/h</div>
                <div class="stat-label">Vent maximum</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            windy_days = len(df[df['Vent Max'] > 40])
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-yellow">{windy_days}</div>
                <div class="stat-label">Jours vent fort (&gt;40)</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Graphique températures
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=df['Date'], y=df['Temp Max'], mode='lines', name='Max', line=dict(color='#EF4444', width=2)))
        fig_temp.add_trace(go.Scatter(x=df['Date'], y=df['Temp Min'], mode='lines', name='Min', line=dict(color='#3B82F6', width=2), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.1)'))
        fig_temp.update_layout(
            title=dict(text="Températures", font=dict(size=14, color='#FAFAFA')),
            height=300, margin=dict(t=40, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
            legend=dict(orientation='h', y=1.1, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Vent et précip
        col1, col2 = st.columns(2)
        
        with col1:
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Bar(x=df['Date'], y=df['Vent Max'], marker_color='#8B5CF6', name='Vent'))
            fig_wind.add_hline(y=40, line_dash="dash", line_color="#EF4444", annotation_text="Seuil critique")
            fig_wind.update_layout(
                title=dict(text="Vent maximum (km/h)", font=dict(size=13, color='#FAFAFA')),
                height=250, margin=dict(t=40, b=30, l=40, r=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_wind, use_container_width=True)
        
        with col2:
            fig_precip = go.Figure()
            fig_precip.add_trace(go.Bar(x=df['Date'], y=df['Précip'], marker_color='#00D4FF', name='Précip'))
            fig_precip.update_layout(
                title=dict(text="Précipitations (mm)", font=dict(size=13, color='#FAFAFA')),
                height=250, margin=dict(t=40, b=30, l=40, r=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_precip, use_container_width=True)
        
        with st.expander("📋 Voir les données brutes"):
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("Impossible de charger les données météo historiques")

# =============================================================================
# TAB 2 : Trafic Actuel (CORRIGÉ - utilise FlightRadar24)
# =============================================================================
with tab2:
    st.markdown("### Trafic aérien en temps réel")
    
    st.markdown("""
    <div class="alert-box alert-info">
        <b>💡 Note :</b> Cette page utilise FlightRadar24 (gratuit) pour afficher les vols actuels. 
        Les données de retards précis nécessiteraient une API premium (AeroDataBox, FlightAware).
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Actualiser", key="refresh_traffic", type="primary"):
            st.rerun()
    
    # Chargement des vols
    with st.spinner("Chargement des vols..."):
        flights = get_flights_in_area()
    
    if flights:
        # Classifier les vols
        arrivals_bva = []
        departures_bva = []
        transit_flights = []
        
        for flight in flights:
            cat = classify_flight(flight)
            if cat == 'arrival':
                arrivals_bva.append(flight)
            elif cat == 'departure':
                departures_bva.append(flight)
            else:
                transit_flights.append(flight)
        
        in_flight = len([f for f in flights if not f.get('on_ground', False)])
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-blue">{len(flights)}</div>
                <div class="stat-label">Vols dans la zone</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_bva = len(arrivals_bva) + len(departures_bva)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-green">{total_bva}</div>
                <div class="stat-label">Vols BVA</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{in_flight}</div>
                <div class="stat-label">En vol</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-gray">{len(transit_flights)}</div>
                <div class="stat-label">Transit</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Liste des vols BVA
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🟢 Arrivées BVA ({len(arrivals_bva)})")
            if arrivals_bva:
                for flight in arrivals_bva[:6]:
                    status = "Au sol" if flight.get('on_ground') else f"{flight['altitude']} ft"
                    origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
                    
                    st.markdown(f"""
                    <div class="flight-card" style="border-left-color: #22C55E;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong style="color: #22C55E;">{flight['callsign']}</strong>
                            <span style="color: #64748B; font-size: 0.8rem;">{status}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #94A3B8;">{origin} → BVA • {flight['aircraft_type']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Aucune arrivée en cours")
        
        with col2:
            st.markdown(f"#### 🟠 Départs BVA ({len(departures_bva)})")
            if departures_bva:
                for flight in departures_bva[:6]:
                    status = "Au sol" if flight.get('on_ground') else f"{flight['altitude']} ft"
                    dest = flight['destination'] if flight['destination'] != 'N/A' else '???'
                    
                    st.markdown(f"""
                    <div class="flight-card" style="border-left-color: #F97316;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong style="color: #F97316;">{flight['callsign']}</strong>
                            <span style="color: #64748B; font-size: 0.8rem;">{status}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #94A3B8;">BVA → {dest} • {flight['aircraft_type']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Aucun départ en cours")
        
        st.divider()
        
        # Statistiques compagnies
        st.markdown("#### Compagnies aériennes dans la zone")
        
        airlines_stats = get_airlines_stats(flights)
        if airlines_stats:
            sorted_airlines = sorted(airlines_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            
            df_airlines = pd.DataFrame(sorted_airlines, columns=['Compagnie', 'Vols'])
            
            fig = px.bar(
                df_airlines,
                x='Compagnie',
                y='Vols',
                color='Vols',
                color_continuous_scale=[[0, '#1e3a5f'], [1, '#00D4FF']]
            )
            fig.update_layout(
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🔍 Aucun vol détecté dans la zone actuellement")

# =============================================================================
# TAB 3 : Impact Météo/Aviation (RENOMMÉ - pas de données retards)
# =============================================================================
with tab3:
    st.markdown("### Impact Météo sur les Opérations Aériennes")
    
    st.markdown("""
    <div class="alert-box alert-info">
        <b>💡 Méthodologie :</b> Cette analyse évalue l'impact potentiel des conditions météo sur les opérations 
        en calculant un <b>score aviation (0-100)</b> basé sur le vent, les précipitations et les phénomènes météo.
        <br><small>Note : Les retards réels nécessiteraient une API premium non disponible.</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Explication du score
    with st.expander("📖 Comment est calculé le score aviation ?"):
        st.markdown("""
        <div class="methodology-box">
            <h4 style="color: #00D4FF; margin-top: 0;">Algorithme du Score Aviation</h4>
            
            Le score part de **100** et diminue selon les conditions :
            
            | Facteur | Condition | Impact |
            |---------|-----------|--------|
            | **Vent** | > 50 km/h | -40 pts |
            | | 35-50 km/h | -25 pts |
            | | 25-35 km/h | -10 pts |
            | **Rafales** | > 60 km/h | -20 pts |
            | | 45-60 km/h | -10 pts |
            | **Précipitations** | > 20 mm | -25 pts |
            | | 10-20 mm | -15 pts |
            | | 5-10 mm | -5 pts |
            | **Brouillard** | Codes 45, 48 | -30 pts |
            | **Orage** | Codes 95, 96, 99 | -35 pts |
            | **Neige** | Codes 71-77 | -30 pts |
            
            **Interprétation :**
            - 🟢 **80-100** : Conditions favorables
            - 🟡 **50-79** : Vigilance recommandée
            - 🔴 **0-49** : Conditions difficiles
        </div>
        """, unsafe_allow_html=True)
    
    # Données actuelles
    weather = get_current_weather()
    forecast = get_aviation_conditions_forecast()
    
    if weather and forecast:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Conditions actuelles")
            
            today_score = forecast[0]['score'] if forecast else 50
            
            if today_score >= 80:
                score_color = "#22C55E"
                score_status = "Favorables"
            elif today_score >= 50:
                score_color = "#EAB308"
                score_status = "Modérées"
            else:
                score_color = "#EF4444"
                score_status = "Difficiles"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; background: #151B28; border-radius: 10px; border: 1px solid #2D3748;">
                <div style="font-size: 4rem; font-weight: 700; color: {score_color};">{today_score}</div>
                <div style="font-size: 1.2rem; color: #94A3B8;">/100</div>
                <div style="margin-top: 1rem; color: {score_color}; font-weight: 600;">Conditions {score_status}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            
            # Alertes
            wind = weather['wind_speed_10m']
            humidity = weather['relative_humidity_2m']
            
            if wind > 40:
                st.markdown(f'<div class="alert-box alert-danger">💨 Vent fort : {wind} km/h — Impact majeur</div>', unsafe_allow_html=True)
            elif wind > 25:
                st.markdown(f'<div class="alert-box alert-warning">💨 Vent modéré : {wind} km/h — Turbulences possibles</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-box alert-success">💨 Vent faible : {wind} km/h — Favorable</div>', unsafe_allow_html=True)
            
            if humidity > 90:
                st.markdown(f'<div class="alert-box alert-warning">💧 Humidité : {humidity}% — Risque de brouillard</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Prévisions 7 jours")
            
            df_forecast = pd.DataFrame(forecast)
            
            fig = go.Figure()
            
            # Zones colorées
            fig.add_hrect(y0=80, y1=100, fillcolor="#22C55E", opacity=0.1, line_width=0)
            fig.add_hrect(y0=50, y1=80, fillcolor="#EAB308", opacity=0.1, line_width=0)
            fig.add_hrect(y0=0, y1=50, fillcolor="#EF4444", opacity=0.1, line_width=0)
            
            colors = ['#22C55E' if s >= 80 else '#EAB308' if s >= 50 else '#EF4444' for s in df_forecast['score']]
            
            fig.add_trace(go.Scatter(
                x=df_forecast['date_formatted'],
                y=df_forecast['score'],
                mode='lines+markers',
                line=dict(color='#00D4FF', width=3),
                marker=dict(size=12, color=colors, line=dict(color='#FAFAFA', width=2)),
                hovertemplate='%{y}/100<extra></extra>'
            ))
            
            fig.update_layout(
                height=350, margin=dict(t=20, b=40, l=50, r=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', range=[0, 100], title='Score')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            alerts_count = sum(1 for d in forecast if d['score'] < 80)
            if alerts_count > 0:
                st.markdown(f'<div class="alert-box alert-warning">⚠️ {alerts_count} jour(s) avec vigilance cette semaine</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-box alert-success">✅ Semaine favorable</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Analyse historique 30 jours
        st.markdown("#### Analyse des 30 derniers jours")
        
        history = get_historical_weather(days=30)
        if history and history.get('time'):
            df_hist = pd.DataFrame({
                'Date': history['time'],
                'Vent': history['wind_speed_10m_max'],
                'Précip': history['precipitation_sum']
            })
            
            # Calculer score pour chaque jour
            def calc_score(row):
                score = 100
                if row['Vent'] and row['Vent'] > 50: score -= 40
                elif row['Vent'] and row['Vent'] > 35: score -= 25
                elif row['Vent'] and row['Vent'] > 25: score -= 10
                if row['Précip'] and row['Précip'] > 20: score -= 25
                elif row['Précip'] and row['Précip'] > 10: score -= 15
                return max(0, score)
            
            df_hist['Score'] = df_hist.apply(calc_score, axis=1)
            df_hist['Impact'] = df_hist['Score'].apply(lambda x: 'Favorable' if x >= 80 else ('Modéré' if x >= 50 else 'Difficile'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.scatter(df_hist, x='Vent', y='Score', color='Impact',
                                 color_discrete_map={'Favorable': '#22C55E', 'Modéré': '#EAB308', 'Difficile': '#EF4444'},
                                 title='Corrélation Vent / Score')
                fig1.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Vent (km/h)'),
                                  yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Score'))
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.scatter(df_hist, x='Précip', y='Score', color='Impact',
                                 color_discrete_map={'Favorable': '#22C55E', 'Modéré': '#EAB308', 'Difficile': '#EF4444'},
                                 title='Corrélation Précipitations / Score')
                fig2.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Précip (mm)'),
                                  yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Score'))
                st.plotly_chart(fig2, use_container_width=True)
            
            # Corrélations
            df_clean = df_hist.dropna()
            if len(df_clean) > 5:
                corr_vent = np.corrcoef(df_clean['Vent'], df_clean['Score'])[0, 1]
                corr_precip = np.corrcoef(df_clean['Précip'].fillna(0), df_clean['Score'])[0, 1]
                
                favorable = len(df_hist[df_hist['Score'] >= 80])
                difficult = len(df_hist[df_hist['Score'] < 50])
                
                st.markdown(f"""
                **Résumé des 30 derniers jours :**
                - **{favorable} jours** favorables (score ≥ 80)
                - **{difficult} jours** difficiles (score < 50)
                - Corrélation Vent ↔ Score : **{corr_vent:.2f}** (négative = plus de vent = score plus bas)
                - Corrélation Précip ↔ Score : **{corr_precip:.2f}**
                """)

# =============================================================================
# TAB 4 : Tendances Climatiques (CORRIGÉ - plus d'années)
# =============================================================================
with tab4:
    st.markdown("### Évolution climatique multi-annuelle")
    
    st.markdown("""
    <div class="alert-box alert-info">
        <b>💡 Source :</b> OpenMeteo Archive fournit des données météo depuis 1940.
        Cette analyse permet d'identifier les tendances à long terme.
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection période (CORRIGÉ - plus de choix)
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_year = st.selectbox(
            "Année de début",
            options=[2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2010, 2005, 2000, 1995, 1990],
            index=5,  # 2019 par défaut
            key="start_year"
        )
    
    with col2:
        # Options pour l'année de fin (toujours >= année de début)
        end_options = [y for y in [2026,2025,2024, 2023, 2022, 2021, 2020] if y >= start_year]
        end_year = st.selectbox(
            "Année de fin",
            options=end_options,
            index=0,  # 2024 par défaut
            key="end_year"
        )
    
    with col3:
        if st.button("📊 Analyser", type="primary"):
            st.session_state['analyze_climate'] = True
    
    # Vérification
    if end_year < start_year:
        st.error("L'année de fin doit être supérieure ou égale à l'année de début")
    else:
        with st.spinner(f"Chargement des données de {start_year} à {end_year}..."):
            try:
                long_term = get_long_term_historical_weather(start_year=start_year, end_year=end_year)
            except Exception as e:
                st.error(f"Erreur : {e}")
                long_term = None
        
        if long_term and 'yearly_stats' in long_term:
            yearly = long_term['yearly_stats']
            
            # DataFrame
            df_years = pd.DataFrame([
                {
                    'Année': int(year),
                    'Temp Moy': stats['avg_temp'],
                    'Vent Moy': stats['avg_wind'],
                    'Vent Max': stats['max_wind'],
                    'Jours Vent Fort': stats['extreme_wind_days'],
                    'Jours Pluie': stats['rainy_days'],
                    'Jours Brouillard': stats['fog_days'],
                    'Jours Orage': stats['storm_days']
                }
                for year, stats in sorted(yearly.items())
            ])
            
            if len(df_years) >= 2:
                # Métriques tendances
                temp_trend = df_years['Temp Moy'].iloc[-1] - df_years['Temp Moy'].iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    color = "stat-red" if temp_trend > 0.5 else "stat-blue" if temp_trend < -0.5 else ""
                    sign = "+" if temp_trend > 0 else ""
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value {color}">{sign}{temp_trend:.1f}°C</div>
                        <div class="stat-label">Évolution température</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    avg_wind_days = df_years['Jours Vent Fort'].mean()
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value stat-yellow">{avg_wind_days:.0f}</div>
                        <div class="stat-label">Moy. jours vent fort/an</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    avg_fog = df_years['Jours Brouillard'].mean()
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">{avg_fog:.0f}</div>
                        <div class="stat-label">Moy. jours brouillard/an</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    avg_storm = df_years['Jours Orage'].mean()
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value stat-orange">{avg_storm:.0f}</div>
                        <div class="stat-label">Moy. jours orage/an</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("")
                
                # Graphique évolution température
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=df_years['Année'], y=df_years['Temp Moy'],
                    mode='lines+markers',
                    line=dict(color='#EF4444', width=3),
                    marker=dict(size=10),
                    name='Température moyenne'
                ))
                
                # Ligne de tendance
                z = np.polyfit(df_years['Année'].values, df_years['Temp Moy'].values, 1)
                p = np.poly1d(z)
                fig_temp.add_trace(go.Scatter(
                    x=df_years['Année'], y=p(df_years['Année'].values),
                    mode='lines',
                    line=dict(color='#EF4444', width=1, dash='dash'),
                    name='Tendance'
                ))
                
                fig_temp.update_layout(
                    title=dict(text="Évolution de la température moyenne annuelle", font=dict(size=14, color='#FAFAFA')),
                    height=300, margin=dict(t=50, b=40, l=50, r=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#64748B', dtick=1),
                    yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='°C'),
                    legend=dict(orientation='h', y=1.1, font=dict(color='#94A3B8'))
                )
                st.plotly_chart(fig_temp, use_container_width=True)
                
                # Graphique phénomènes
                fig_extreme = go.Figure()
                fig_extreme.add_trace(go.Scatter(x=df_years['Année'], y=df_years['Jours Vent Fort'], mode='lines+markers', name='Vent fort (>40 km/h)', line=dict(color='#8B5CF6', width=2)))
                fig_extreme.add_trace(go.Scatter(x=df_years['Année'], y=df_years['Jours Orage'], mode='lines+markers', name="Jours d'orage", line=dict(color='#EF4444', width=2)))
                fig_extreme.add_trace(go.Scatter(x=df_years['Année'], y=df_years['Jours Brouillard'], mode='lines+markers', name='Jours de brouillard', line=dict(color='#94A3B8', width=2)))
                
                fig_extreme.update_layout(
                    title=dict(text="Évolution des phénomènes impactant l'aviation", font=dict(size=14, color='#FAFAFA')),
                    height=350,
                    margin=dict(t=75, b=40, l=50, r=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#64748B', dtick=1),
                    yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Nombre de jours'),
                    legend=dict(
                        orientation='h',
                        yanchor='top', y=1.0,
                        xanchor='left', x=0,
                        font=dict(color='#94A3B8')
                    )
                )

                st.plotly_chart(fig_extreme, use_container_width=True)
                
                # Données brutes
                with st.expander("📋 Voir les données annuelles"):
                    st.dataframe(df_years, use_container_width=True, hide_index=True)
                
                # Conclusions
                st.markdown("### Conclusions")
                st.markdown(f"""
                **Analyse sur {end_year - start_year + 1} ans ({start_year} - {end_year}) :**
                
                - La température moyenne a évolué de **{temp_trend:+.1f}°C**
                - En moyenne **{avg_wind_days:.0f} jours/an** avec des vents forts (>40 km/h)
                - Les phénomènes de brouillard représentent environ **{avg_fog:.0f} jours/an**
                - Les orages comptent pour **{avg_storm:.0f} jours/an** en moyenne
                
                Ces tendances sont importantes pour la planification des opérations aériennes.
                """)
            else:
                st.warning("Pas assez de données pour l'analyse")
        else:
            st.warning("Impossible de charger les données long terme")

# =============================================================================
# Footer
# =============================================================================
st.markdown("""
<div class="footer">
    Données : OpenMeteo API & FlightRadar24 • Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)