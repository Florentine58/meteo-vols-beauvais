"""
Page Analyse Historique — Corrélation météo/vols sur plusieurs années
🆕 Analyse long terme avec données depuis 2011 !
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports des modules API
from api.weather import (
    get_long_term_historical_weather, 
    get_weather_for_period,
    calculate_aviation_score,
    get_weather_code_description
)
from api.opensky import (
    get_historical_flights,
    get_extended_historical_flights,
    test_connection
)

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Analyse Historique",
    page_icon="📈",
    layout="wide"
)

# =============================================================================
# CSS Professionnel
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .page-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #00D4FF;
    }
    
    .page-header h1 {
        color: #FAFAFA;
        font-weight: 600;
        margin: 0;
        font-size: 1.35rem;
    }
    
    .page-header p {
        color: #94A3B8;
        margin: 0.25rem 0 0 0;
        font-size: 0.85rem;
    }
    
    .stat-card {
        background: #151B28;
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #FAFAFA;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.25rem;
    }
    
    .stat-green { color: #22C55E; }
    .stat-yellow { color: #EAB308; }
    .stat-red { color: #EF4444; }
    .stat-blue { color: #00D4FF; }
    
    .insight-box {
        background: linear-gradient(135deg, #1A1F2E 0%, #151B28 100%);
        padding: 1.25rem;
        border-radius: 10px;
        border-left: 4px solid #00D4FF;
        margin: 1rem 0;
    }
    
    .insight-title {
        color: #00D4FF;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .insight-text {
        color: #94A3B8;
        font-size: 0.9rem;
        line-height: 1.6;
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
<div class="page-header">
    <h1>Analyse Historique Long Terme</h1>
    <p>Corrélation météo / trafic aérien sur plusieurs années — Paris-Beauvais (LFOB)</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Onglets
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Évolution Météo", 
    "✈️ Historique Vols", 
    "🔗 Corrélation",
    "🔮 Tendances Climatiques"
])

# =============================================================================
# TAB 1 : Évolution Météo Multi-Années
# =============================================================================
with tab1:
    st.markdown("### Évolution météorologique à Beauvais")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        start_year = st.selectbox("Année de début", range(2015, 2025), index=5)
        end_year = st.selectbox("Année de fin", range(start_year, 2026), index=min(2024 - start_year, 5))
    
    with col2:
        st.info(f"📅 Période sélectionnée : **{start_year} - {end_year}** ({end_year - start_year + 1} années)")
    
    if st.button("Charger les données météo", type="primary"):
        with st.spinner(f"Chargement des données météo de {start_year} à {end_year}..."):
            weather_data = get_long_term_historical_weather(start_year, end_year)
        
        if weather_data and weather_data.get('yearly_stats'):
            st.success(f"✅ {len(weather_data['yearly_stats'])} années de données chargées !")
            
            # Stocker en session
            st.session_state['weather_long_term'] = weather_data
    
    # Afficher les données si disponibles
    if 'weather_long_term' in st.session_state:
        weather_data = st.session_state['weather_long_term']
        yearly = weather_data['yearly_stats']
        
        # Créer DataFrame
        df_yearly = pd.DataFrame([
            {
                "Année": year,
                "Temp. moyenne (°C)": stats['avg_temp'],
                "Vent moyen (km/h)": stats['avg_wind'],
                "Vent max (km/h)": stats['max_wind'],
                "Précipitations (mm)": stats['total_precip'],
                "Jours vent fort": stats['extreme_wind_days'],
                "Jours de pluie": stats['rainy_days'],
                "Jours de brouillard": stats['fog_days'],
                "Jours d'orage": stats['storm_days']
            }
            for year, stats in sorted(yearly.items())
        ])
        
        st.divider()
        
        # Graphique températures
        st.markdown("#### Évolution des températures")
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=df_yearly['Année'],
            y=df_yearly['Temp. moyenne (°C)'],
            mode='lines+markers',
            name='Température moyenne',
            line=dict(color='#00D4FF', width=3),
            marker=dict(size=10)
        ))
        
        # Ligne de tendance
        z = np.polyfit(range(len(df_yearly)), df_yearly['Temp. moyenne (°C)'], 1) if len(df_yearly) > 1 else [0, 0]
        p = np.poly1d(z)
        fig_temp.add_trace(go.Scatter(
            x=df_yearly['Année'],
            y=p(range(len(df_yearly))),
            mode='lines',
            name='Tendance',
            line=dict(color='#EF4444', width=2, dash='dash')
        ))
        
        fig_temp.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='°C'),
            legend=dict(orientation='h', y=1.1, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Stats cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            trend = df_yearly['Temp. moyenne (°C)'].iloc[-1] - df_yearly['Temp. moyenne (°C)'].iloc[0]
            trend_text = f"+{trend:.1f}°C" if trend > 0 else f"{trend:.1f}°C"
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value {'stat-red' if trend > 0 else 'stat-blue'}">{trend_text}</div>
                <div class="stat-label">Évolution température</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_wind_days = df_yearly['Jours vent fort'].sum()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-yellow">{total_wind_days}</div>
                <div class="stat-label">Jours vent &gt;40 km/h</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_precip = df_yearly['Précipitations (mm)'].mean()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{avg_precip:.0f} mm</div>
                <div class="stat-label">Précip. moy. /an</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_storms = df_yearly['Jours d\'orage'].sum()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-red">{total_storms}</div>
                <div class="stat-label">Jours d'orage</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Graphique jours difficiles
        st.markdown("#### Jours météo difficiles pour l'aviation")
        
        fig_difficult = go.Figure()
        fig_difficult.add_trace(go.Bar(
            x=df_yearly['Année'],
            y=df_yearly['Jours vent fort'],
            name='Vent fort',
            marker_color='#8B5CF6'
        ))
        fig_difficult.add_trace(go.Bar(
            x=df_yearly['Année'],
            y=df_yearly['Jours de brouillard'],
            name='Brouillard',
            marker_color='#64748B'
        ))
        fig_difficult.add_trace(go.Bar(
            x=df_yearly['Année'],
            y=df_yearly['Jours d\'orage'],
            name='Orages',
            marker_color='#EF4444'
        ))
        
        fig_difficult.update_layout(
            barmode='group',
            height=300,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Jours'),
            legend=dict(orientation='h', y=1.1, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_difficult, use_container_width=True)
        
        # Tableau détaillé
        with st.expander("📋 Voir les données détaillées"):
            st.dataframe(df_yearly, use_container_width=True, hide_index=True)

# =============================================================================
# TAB 2 : Historique Vols
# =============================================================================
with tab2:
    st.markdown("### Historique des vols — Paris-Beauvais (LFOB)")
    
    # Test connexion OpenSky
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("Tester connexion OpenSky"):
            result = test_connection()
            if result['status'] == 'success':
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    with col2:
        st.info("⚠️ OpenSky limite à 7 jours d'historique par requête (gratuit)")
    
    st.divider()
    
    weeks = st.slider("Nombre de semaines à analyser", 1, 4, 2)
    
    if st.button("Charger l'historique des vols", type="primary"):
        with st.spinner(f"Récupération des {weeks} dernières semaines..."):
            flights_data = get_extended_historical_flights(weeks=weeks)
        
        if flights_data and flights_data['total'] > 0:
            st.success(f"✅ {flights_data['total']} vols récupérés !")
            st.session_state['flights_history'] = flights_data
        else:
            st.warning("Aucun vol trouvé ou erreur de connexion. Vérifiez vos credentials OpenSky.")
    
    # Afficher les données si disponibles
    if 'flights_history' in st.session_state:
        data = st.session_state['flights_history']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-green">{len(data['arrivals'])}</div>
                <div class="stat-label">Arrivées</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-blue">{len(data['departures'])}</div>
                <div class="stat-label">Départs</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{data['total']}</div>
                <div class="stat-label">Total</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Graphique par jour
        if data['by_day']:
            df_days = pd.DataFrame([
                {
                    "Date": day,
                    "Arrivées": counts['arrivals'],
                    "Départs": counts['departures'],
                    "Total": counts['arrivals'] + counts['departures']
                }
                for day, counts in sorted(data['by_day'].items())
            ])
            
            fig_flights = go.Figure()
            fig_flights.add_trace(go.Bar(
                x=df_days['Date'],
                y=df_days['Arrivées'],
                name='Arrivées',
                marker_color='#22C55E'
            ))
            fig_flights.add_trace(go.Bar(
                x=df_days['Date'],
                y=df_days['Départs'],
                name='Départs',
                marker_color='#00D4FF'
            ))
            
            fig_flights.update_layout(
                barmode='stack',
                title="Vols par jour",
                height=350,
                margin=dict(t=50, b=40, l=50, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
                legend=dict(orientation='h', y=1.15, font=dict(color='#94A3B8'))
            )
            st.plotly_chart(fig_flights, use_container_width=True)

# =============================================================================
# TAB 3 : Corrélation Météo / Vols
# =============================================================================
with tab3:
    st.markdown("### Corrélation Météo / Trafic Aérien")
    
    st.markdown("""
    <div class="insight-box">
        <div class="insight-title">Comment ça fonctionne ?</div>
        <div class="insight-text">
            Cette analyse croise les données météorologiques avec le trafic aérien pour identifier 
            les corrélations. Un score aviation est calculé pour chaque jour en fonction du vent, 
            des précipitations et des phénomènes météo (brouillard, orages).
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Vérifier si on a les deux datasets
    has_weather = 'weather_long_term' in st.session_state
    has_flights = 'flights_history' in st.session_state
    
    if not has_weather:
        st.warning("⚠️ Chargez d'abord les données météo (onglet 'Évolution Météo')")
    if not has_flights:
        st.warning("⚠️ Chargez d'abord les données vols (onglet 'Historique Vols')")
    
    if has_weather and has_flights:
        weather_data = st.session_state['weather_long_term']
        flights_data = st.session_state['flights_history']
        
        st.success("✅ Données prêtes pour l'analyse !")
        
        # Analyse sur les jours où on a des données de vols
        daily_weather = weather_data['daily']
        flights_by_day = flights_data['by_day']
        
        # Créer un dataset croisé
        correlation_data = []
        
        for i, date in enumerate(daily_weather['time']):
            if date in flights_by_day:
                wind = daily_weather['wind_speed_10m_max'][i]
                precip = daily_weather['precipitation_sum'][i]
                gusts = daily_weather['wind_gusts_10m_max'][i]
                code = daily_weather['weather_code'][i]
                
                score = calculate_aviation_score(wind, gusts, precip, code)
                
                flights = flights_by_day[date]['arrivals'] + flights_by_day[date]['departures']
                
                correlation_data.append({
                    'date': date,
                    'score': score,
                    'flights': flights,
                    'wind': wind,
                    'precip': precip
                })
        
        if correlation_data:
            df_corr = pd.DataFrame(correlation_data)
            
            st.divider()
            
            # Scatter plot
            st.markdown("#### Score météo vs Nombre de vols")
            
            fig_scatter = px.scatter(
                df_corr,
                x='score',
                y='flights',
                color='wind',
                size='precip' if df_corr['precip'].max() > 0 else None,
                color_continuous_scale='RdYlGn',
                labels={
                    'score': 'Score météo aviation',
                    'flights': 'Nombre de vols',
                    'wind': 'Vent (km/h)',
                    'precip': 'Précip. (mm)'
                }
            )
            
            fig_scatter.update_layout(
                height=400,
                margin=dict(t=20, b=40, l=50, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Calcul de la corrélation
            correlation = df_corr['score'].corr(df_corr['flights'])
            
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">Coefficient de corrélation : {correlation:.3f}</div>
                <div class="insight-text">
                    {'Une corrélation positive suggère que les meilleures conditions météo sont associées à plus de vols.' if correlation > 0 else 'Une corrélation négative suggère une relation inverse entre météo et trafic.'}
                    <br><br>
                    <strong>Interprétation :</strong><br>
                    • |r| < 0.3 : Faible corrélation<br>
                    • 0.3 ≤ |r| < 0.7 : Corrélation modérée<br>
                    • |r| ≥ 0.7 : Forte corrélation
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Pas assez de données communes pour calculer la corrélation.")

# =============================================================================
# TAB 4 : Tendances Climatiques
# =============================================================================
with tab4:
    st.markdown("### Tendances climatiques et impact aviation")
    
    st.markdown("""
    <div class="insight-box">
        <div class="insight-title">Changement climatique et aviation</div>
        <div class="insight-text">
            Cette section analyse l'évolution des conditions météorologiques à Beauvais 
            sur le long terme et leur impact potentiel sur les opérations aériennes.
            Les données OpenMeteo permettent d'analyser jusqu'à 80 ans d'historique !
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if 'weather_long_term' in st.session_state:
        weather_data = st.session_state['weather_long_term']
        yearly = weather_data['yearly_stats']
        
        df_trends = pd.DataFrame([
            {
                "Année": int(year),
                "Temp": stats['avg_temp'],
                "Vent_fort": stats['extreme_wind_days'],
                "Orages": stats['storm_days'],
                "Brouillard": stats['fog_days']
            }
            for year, stats in sorted(yearly.items())
        ])
        
        st.divider()
        
        # Évolution des événements extrêmes
        st.markdown("#### Évolution des phénomènes météo impactant l'aviation")
        
        fig_trends = go.Figure()
        
        fig_trends.add_trace(go.Scatter(
            x=df_trends['Année'],
            y=df_trends['Vent_fort'],
            mode='lines+markers',
            name='Jours vent fort (>40 km/h)',
            line=dict(color='#8B5CF6', width=2)
        ))
        
        fig_trends.add_trace(go.Scatter(
            x=df_trends['Année'],
            y=df_trends['Orages'],
            mode='lines+markers',
            name='Jours d\'orage',
            line=dict(color='#EF4444', width=2)
        ))
        
        fig_trends.add_trace(go.Scatter(
            x=df_trends['Année'],
            y=df_trends['Brouillard'],
            mode='lines+markers',
            name='Jours de brouillard',
            line=dict(color='#64748B', width=2)
        ))
        
        fig_trends.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', title='Nombre de jours'),
            legend=dict(orientation='h', y=1.15, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_trends, use_container_width=True)
        
        # Conclusions
        st.divider()
        st.markdown("#### Conclusions")
        
        # Calculer les tendances
        first_year = df_trends.iloc[0]
        last_year = df_trends.iloc[-1]
        
        temp_change = last_year['Temp'] - first_year['Temp']
        wind_change = last_year['Vent_fort'] - first_year['Vent_fort']
        
        conclusions = []
        
        if temp_change > 0.5:
            conclusions.append(f"🌡️ **Réchauffement** : +{temp_change:.1f}°C sur la période analysée")
        elif temp_change < -0.5:
            conclusions.append(f"🌡️ **Refroidissement** : {temp_change:.1f}°C sur la période analysée")
        
        if wind_change > 5:
            conclusions.append(f"💨 **Augmentation des jours de vent fort** : +{wind_change} jours/an")
        elif wind_change < -5:
            conclusions.append(f"💨 **Diminution des jours de vent fort** : {wind_change} jours/an")
        
        avg_difficult = df_trends['Vent_fort'].mean() + df_trends['Orages'].mean() + df_trends['Brouillard'].mean()
        conclusions.append(f"📊 En moyenne, **{avg_difficult:.0f} jours/an** présentent des conditions difficiles pour l'aviation")
        
        for c in conclusions:
            st.markdown(c)
    
    else:
        st.info("Chargez d'abord les données météo dans l'onglet 'Évolution Météo'")

# =============================================================================
# Footer
# =============================================================================
st.markdown("""
<div class="footer">
    Sources : OpenMeteo Archive (météo depuis 1940) • OpenSky Network (vols)<br>
    Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)