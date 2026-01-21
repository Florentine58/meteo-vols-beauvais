"""
Page Analyse Historique — Corrélation Météo & Vols
Intègre les données météo long terme + AeroDataBox pour les retards
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports des modules API
from api.weather import get_current_weather, get_historical_weather, get_long_term_historical_weather, get_aviation_conditions_forecast
from api.aerodatabox import get_delay_statistics, get_airport_info, test_connection, AIRPORTS

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Analyse",
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
    <h1>📊 Analyse Historique & Corrélations</h1>
    <p>Étude de l'impact météorologique sur les opérations aériennes</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Onglets
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🌡️ Évolution Météo",
    "✈️ Trafic Temps Réel", 
    "📈 Corrélation Météo/Retards",
    "🌍 Tendances Climatiques"
])

# =============================================================================
# TAB 1 : Évolution Météo
# =============================================================================
with tab1:
    st.markdown("### Évolution météorologique à Beauvais")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        period = st.selectbox("Période", [7, 14, 30], format_func=lambda x: f"{x} derniers jours", index=2)
    
    with st.spinner("Chargement des données météo..."):
        history = get_historical_weather(days=period)
    
    if history:
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
                <div class="stat-label">Jours vent fort (>40 km/h)</div>
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
        
        # Graphiques vent et précip
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
    else:
        st.error("Impossible de charger les données météo historiques")

# =============================================================================
# TAB 2 : Trafic Temps Réel (AeroDataBox)
# =============================================================================
with tab2:
    st.markdown("### Trafic aérien en temps réel")
    
    # Sélection de l'aéroport
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        airport_choice = st.selectbox(
            "Aéroport",
            options=["LFOB", "LFPG", "LFPO"],
            format_func=lambda x: f"{AIRPORTS.get(next((k for k, v in AIRPORTS.items() if v['icao'] == x), ''), {}).get('name', x)} ({x})"
        )
    
    with col2:
        hours_choice = st.selectbox("Période", [6, 12, 24], format_func=lambda x: f"Prochaines {x}h", index=1)
    
    with col3:
        if st.button("🔄 Actualiser", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Test connexion
    conn = test_connection()
    if conn['status'] != 'success':
        st.markdown(f'<div class="alert-box alert-danger">❌ {conn["message"]}</div>', unsafe_allow_html=True)
        st.info("Vérifie ta clé API dans le fichier `.env`")
    else:
        with st.spinner("Chargement des vols..."):
            stats = get_delay_statistics(airport_choice, hours_choice)
        
        if stats['summary']['total_flights'] == 0:
            st.markdown(f'<div class="alert-box alert-warning">Aucun vol trouvé pour les prochaines {hours_choice}h. Normal pour les petits aéroports comme Beauvais.</div>', unsafe_allow_html=True)
            st.info("💡 Essaie Paris-CDG (LFPG) pour voir plus de données !")
        else:
            # Métriques
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value stat-blue">{stats['summary']['total_flights']}</div>
                    <div class="stat-label">Vols total</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                delayed = stats['summary']['total_delayed']
                color = "stat-red" if delayed > 10 else "stat-yellow" if delayed > 5 else "stat-green"
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value {color}">{delayed}</div>
                    <div class="stat-label">Retardés (>15 min)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                cancelled = stats['summary']['total_cancelled']
                color = "stat-red" if cancelled > 0 else "stat-green"
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value {color}">{cancelled}</div>
                    <div class="stat-label">Annulés</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                rate = stats['summary'].get('on_time_rate')
                if rate:
                    color = "stat-green" if rate >= 85 else "stat-yellow" if rate >= 70 else "stat-red"
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value {color}">{rate}%</div>
                        <div class="stat-label">Ponctualité</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Liste des vols
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🛫 Départs")
                if stats['departures']['flights']:
                    for flight in stats['departures']['flights'][:8]:
                        delay_str = ""
                        if flight.get('delay_minutes'):
                            if flight['delay_minutes'] > 15:
                                delay_str = f"<span style='color: #EF4444;'>+{flight['delay_minutes']} min</span>"
                            elif flight['delay_minutes'] > 0:
                                delay_str = f"<span style='color: #EAB308;'>+{flight['delay_minutes']} min</span>"
                            else:
                                delay_str = f"<span style='color: #22C55E;'>À l'heure</span>"
                        
                        st.markdown(f"""
                        <div class="flight-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="color: #FAFAFA;">{flight['flight_number']}</strong>
                                    <span style="color: #64748B;"> → {flight['destination']}</span>
                                </div>
                                <div>{delay_str}</div>
                            </div>
                            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                                {flight['scheduled_time'][:16] if flight['scheduled_time'] != 'N/A' else ''} • {flight['airline']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("Aucun départ prévu")
            
            with col2:
                st.markdown("#### 🛬 Arrivées")
                if stats['arrivals']['flights']:
                    for flight in stats['arrivals']['flights'][:8]:
                        delay_str = ""
                        if flight.get('delay_minutes'):
                            if flight['delay_minutes'] > 15:
                                delay_str = f"<span style='color: #EF4444;'>+{flight['delay_minutes']} min</span>"
                            elif flight['delay_minutes'] > 0:
                                delay_str = f"<span style='color: #EAB308;'>+{flight['delay_minutes']} min</span>"
                            else:
                                delay_str = f"<span style='color: #22C55E;'>À l'heure</span>"
                        
                        st.markdown(f"""
                        <div class="flight-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="color: #FAFAFA;">{flight['flight_number']}</strong>
                                    <span style="color: #64748B;"> ← {flight['origin']}</span>
                                </div>
                                <div>{delay_str}</div>
                            </div>
                            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                                {flight['scheduled_time'][:16] if flight['scheduled_time'] != 'N/A' else ''} • {flight['airline']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("Aucune arrivée prévue")

# =============================================================================
# TAB 3 : Corrélation Météo / Retards
# =============================================================================
with tab3:
    st.markdown("### Analyse de corrélation Météo / Aviation")
    
    st.markdown("""
    <div class="alert-box alert-info">
        Cette analyse combine les données météo historiques avec les conditions actuelles pour évaluer 
        l'impact de la météo sur les opérations aériennes.
    </div>
    """, unsafe_allow_html=True)
    
    # Récupérer les données météo actuelles
    weather = get_current_weather()
    forecast = get_aviation_conditions_forecast()
    
    if weather and forecast:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Conditions météo actuelles")
            
            # Score météo actuel
            today_score = forecast[0]['score'] if forecast else 50
            
            if today_score >= 80:
                score_color = "#22C55E"
                score_status = "Excellentes"
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
            
            # Détails météo
            wind = weather['wind_speed_10m']
            humidity = weather['relative_humidity_2m']
            
            if wind > 40:
                st.markdown(f'<div class="alert-box alert-danger">💨 Vent fort : {wind} km/h — Impact majeur sur les vols</div>', unsafe_allow_html=True)
            elif wind > 25:
                st.markdown(f'<div class="alert-box alert-warning">💨 Vent modéré : {wind} km/h — Turbulences possibles</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-box alert-success">💨 Vent faible : {wind} km/h — Conditions favorables</div>', unsafe_allow_html=True)
            
            if humidity > 90:
                st.markdown(f'<div class="alert-box alert-warning">💧 Humidité élevée : {humidity}% — Risque de brouillard</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Prévision impact aviation (7 jours)")
            
            if forecast:
                # Graphique des scores
                df_forecast = pd.DataFrame(forecast)
                
                fig = go.Figure()
                
                # Zones de couleur
                fig.add_hrect(y0=80, y1=100, fillcolor="#22C55E", opacity=0.1, line_width=0)
                fig.add_hrect(y0=50, y1=80, fillcolor="#EAB308", opacity=0.1, line_width=0)
                fig.add_hrect(y0=0, y1=50, fillcolor="#EF4444", opacity=0.1, line_width=0)
                
                # Ligne de score
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
                    height=300, margin=dict(t=20, b=40, l=50, r=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#64748B'),
                    yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', range=[0, 100], title='Score Aviation')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Alertes
                alerts_count = sum(1 for d in forecast if d['score'] < 80)
                if alerts_count > 0:
                    st.markdown(f'<div class="alert-box alert-warning">⚠️ {alerts_count} jour(s) avec vigilance recommandée cette semaine</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert-box alert-success">✅ Semaine favorable pour les opérations</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Analyse de corrélation sur 30 jours
        st.markdown("#### Analyse historique (30 derniers jours)")
        
        history = get_historical_weather(days=30)
        if history:
            df_hist = pd.DataFrame({
                'Date': history['time'],
                'Vent': history['wind_speed_10m_max'],
                'Précip': history['precipitation_sum']
            })
            
            # Calculer un score pour chaque jour
            def calc_score(row):
                score = 100
                if row['Vent'] > 50: score -= 40
                elif row['Vent'] > 35: score -= 25
                elif row['Vent'] > 25: score -= 10
                if row['Précip'] > 20: score -= 25
                elif row['Précip'] > 10: score -= 15
                return max(0, score)
            
            df_hist['Score'] = df_hist.apply(calc_score, axis=1)
            df_hist['Impact'] = df_hist['Score'].apply(lambda x: 'Favorable' if x >= 80 else ('Modéré' if x >= 50 else 'Difficile'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Scatter plot vent vs score
                fig1 = px.scatter(df_hist, x='Vent', y='Score', color='Impact',
                                 color_discrete_map={'Favorable': '#22C55E', 'Modéré': '#EAB308', 'Difficile': '#EF4444'},
                                 title='Corrélation Vent / Score Aviation')
                fig1.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Vent max (km/h)'),
                                  yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Score'))
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Scatter plot précip vs score
                fig2 = px.scatter(df_hist, x='Précip', y='Score', color='Impact',
                                 color_discrete_map={'Favorable': '#22C55E', 'Modéré': '#EAB308', 'Difficile': '#EF4444'},
                                 title='Corrélation Précipitations / Score')
                fig2.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Précip (mm)'),
                                  yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Score'))
                st.plotly_chart(fig2, use_container_width=True)
            
            # Coefficient de corrélation
            corr_vent = np.corrcoef(df_hist['Vent'], df_hist['Score'])[0, 1]
            corr_precip = np.corrcoef(df_hist['Précip'].fillna(0), df_hist['Score'])[0, 1]
            
            st.markdown(f"""
            **Coefficients de corrélation :**
            - Vent ↔ Score : **{corr_vent:.2f}** {'(forte corrélation négative)' if corr_vent < -0.5 else '(corrélation modérée)' if corr_vent < -0.3 else '(corrélation faible)'}
            - Précipitations ↔ Score : **{corr_precip:.2f}**
            
            *Un coefficient négatif indique que plus le vent/précipitations augmentent, plus le score aviation diminue.*
            """)

# =============================================================================
# TAB 4 : Tendances Climatiques
# =============================================================================
with tab4:
    st.markdown("### Évolution climatique multi-annuelle")
    
    st.markdown("""
    <div class="alert-box alert-info">
        Analyse des données météo sur plusieurs années pour identifier les tendances climatiques 
        et leur impact potentiel sur l'aviation.
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection période
    col1, col2 = st.columns([3, 1])
    with col2:
        start_year = st.selectbox("Depuis", [2020, 2015, 2010], index=0)
    
    with st.spinner(f"Chargement des données depuis {start_year}..."):
        try:
            long_term = get_long_term_historical_weather(start_year=start_year, end_year=2024)
        except Exception as e:
            st.error(f"Erreur lors du chargement: {e}")
            long_term = None
    
    if long_term and 'yearly_stats' in long_term:
        yearly = long_term['yearly_stats']
        
        # Créer DataFrame
        df_years = pd.DataFrame([
            {
                'Année': year,
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
        
        # Métriques tendances
        if len(df_years) >= 2:
            temp_trend = df_years['Temp Moy'].iloc[-1] - df_years['Temp Moy'].iloc[0]
            wind_trend = df_years['Jours Vent Fort'].iloc[-1] - df_years['Jours Vent Fort'].iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                color = "stat-red" if temp_trend > 0.5 else "stat-green" if temp_trend < -0.5 else ""
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
                    <div class="stat-value stat-red">{avg_storm:.0f}</div>
                    <div class="stat-label">Moy. jours orage/an</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Convertir les années en int pour les calculs
        df_years['Année'] = df_years['Année'].astype(int)
        
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
        
        # Graphique phénomènes extrêmes
        fig_extreme = go.Figure()
        fig_extreme.add_trace(go.Scatter(x=df_years['Année'], y=df_years['Jours Vent Fort'], mode='lines+markers', name='Vent fort (>40 km/h)', line=dict(color='#8B5CF6', width=2)))
        fig_extreme.add_trace(go.Scatter(x=df_years['Année'], y=df_years['Jours Orage'], mode='lines+markers', name="Jours d'orage", line=dict(color='#EF4444', width=2)))
        fig_extreme.add_trace(go.Scatter(x=df_years['Année'], y=df_years['Jours Brouillard'], mode='lines+markers', name='Jours de brouillard', line=dict(color='#94A3B8', width=2)))
        
        fig_extreme.update_layout(
            title=dict(text="Évolution des phénomènes météo impactant l'aviation", font=dict(size=14, color='#FAFAFA')),
            height=350, margin=dict(t=50, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B', dtick=1),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Nombre de jours'),
            legend=dict(orientation='h', y=1.15, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_extreme, use_container_width=True)
        
        # Tableau récapitulatif
        with st.expander("Voir les données annuelles"):
            st.dataframe(df_years, use_container_width=True, hide_index=True)
        
        # Conclusion
        st.markdown("### Conclusions")
        st.markdown(f"""
        **Analyse sur {2024 - start_year + 1} ans :**
        
        - La température moyenne a évolué de **{temp_trend:+.1f}°C** depuis {start_year}
        - En moyenne **{avg_wind_days:.0f} jours/an** avec des vents forts (>40 km/h) impactant les opérations
        - Les phénomènes de brouillard représentent environ **{avg_fog:.0f} jours/an** de perturbations potentielles
        
        Ces données permettent d'anticiper les périodes à risque et d'optimiser la planification des vols.
        """)
    else:
        st.warning("Impossible de charger les données long terme")

# =============================================================================
# Footer
# =============================================================================
st.markdown("""
<div class="footer">
    Données : OpenMeteo API & AeroDataBox • Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)