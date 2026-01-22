"""
Page Historique & Prévisions — Analyse corrélation météo/aviation
Inclut explication méthodologie des trajectoires
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports des modules API
from api.weather import (
    get_historical_weather, 
    get_aviation_conditions_forecast, 
    get_weather_code_description,
    get_long_term_historical_weather
)

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Historique",
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
    
    .forecast-card {
        background: #1A1F2E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        text-align: center;
        transition: transform 0.2s;
    }
    
    .forecast-card:hover {
        transform: translateY(-2px);
    }
    
    .alert-box {
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    
    .alert-success {
        background: rgba(34, 197, 94, 0.1);
        border-left: 3px solid #22C55E;
        color: #86EFAC;
    }
    
    .alert-warning {
        background: rgba(234, 179, 8, 0.1);
        border-left: 3px solid #EAB308;
        color: #FDE047;
    }
    
    .alert-danger {
        background: rgba(239, 68, 68, 0.1);
        border-left: 3px solid #EF4444;
        color: #FCA5A5;
    }
    
    .alert-info {
        background: rgba(0, 212, 255, 0.1);
        border-left: 3px solid #00D4FF;
        color: #7DD3FC;
    }
    
    .methodology-box {
        background: #151B28;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #2D3748;
        margin: 1rem 0;
    }
    
    .methodology-box h4 {
        color: #00D4FF;
        margin-top: 0;
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
    <h1>📈 Historique & Prévisions</h1>
    <p>Analyse des données météo et impact sur les opérations aériennes</p>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Actualiser", type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# =============================================================================
# Onglets
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📅 Prévisions 7 jours", "🌡️ Historique Météo", "📊 Analyse Corrélation", "🛫 Méthodologie Trajectoires"])

# =============================================================================
# TAB 1 : Prévisions 7 jours
# =============================================================================
with tab1:
    st.markdown("### Prévisions météo et impact aviation")
    
    with st.spinner("Chargement..."):
        forecast = get_aviation_conditions_forecast()
    
    if forecast:
        # Résumé alertes
        alerts_red = len([d for d in forecast if d['level'] == 'red'])
        alerts_yellow = len([d for d in forecast if d['level'] == 'yellow'])
        
        if alerts_red > 0:
            st.markdown(f'<div class="alert-box alert-danger">⚠️ {alerts_red} jour(s) avec conditions difficiles prévus cette semaine</div>', unsafe_allow_html=True)
        elif alerts_yellow > 0:
            st.markdown(f'<div class="alert-box alert-warning">⚠️ {alerts_yellow} jour(s) nécessitant une vigilance</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-success">✅ Conditions favorables pour toute la semaine</div>', unsafe_allow_html=True)
        
        st.markdown("")
        
        # Grille 7 jours
        cols = st.columns(7)
        for i, day in enumerate(forecast[:7]):
            with cols[i]:
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                icon, desc = get_weather_code_description(day['weather_code'])
                
                if day['score'] >= 80:
                    ind_color = "#22C55E"
                    bg_border = "border-top: 3px solid #22C55E;"
                elif day['score'] >= 50:
                    ind_color = "#EAB308"
                    bg_border = "border-top: 3px solid #EAB308;"
                else:
                    ind_color = "#EF4444"
                    bg_border = "border-top: 3px solid #EF4444;"
                
                st.markdown(f"""
                <div class="forecast-card" style="{bg_border}">
                    <div style="font-weight: 600; color: #FAFAFA;">{date_obj.strftime('%A')[:3]}</div>
                    <div style="font-size: 0.75rem; color: #64748B;">{date_obj.strftime('%d/%m')}</div>
                    <div style="font-size: 1.5rem; margin: 0.5rem 0;">{icon}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">{desc}</div>
                    <div style="margin: 0.5rem 0;">
                        <span style="font-weight: 600; color: #FAFAFA;">{day['temp_max']:.0f}°</span>
                        <span style="color: #64748B;">/ {day['temp_min']:.0f}°</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B;">Vent: {day['wind_max']:.0f} km/h</div>
                    <div style="margin-top: 0.5rem; font-weight: 600; color: {ind_color};">
                        ● {day['score']}/100
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Graphique évolution score
        st.markdown("### Évolution du score aviation")
        
        df_forecast = pd.DataFrame(forecast)
        
        fig = go.Figure()
        
        # Zones colorées
        fig.add_hrect(y0=80, y1=100, fillcolor="#22C55E", opacity=0.1, line_width=0)
        fig.add_hrect(y0=50, y1=80, fillcolor="#EAB308", opacity=0.1, line_width=0)
        fig.add_hrect(y0=0, y1=50, fillcolor="#EF4444", opacity=0.1, line_width=0)
        
        fig.add_trace(go.Scatter(
            x=df_forecast['date_formatted'],
            y=df_forecast['score'],
            mode='lines+markers',
            line=dict(color='#00D4FF', width=3),
            marker=dict(size=10, color='#00D4FF'),
            hovertemplate='%{y}/100<extra></extra>'
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B', range=[0, 100], title='Score')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Détails
        with st.expander("📋 Voir le détail des prévisions"):
            for day in forecast:
                st.markdown(f"**{day['date_formatted']}** — Score: {day['score']}/100")
                if day['alerts']:
                    for alert in day['alerts']:
                        st.caption(f"  • {alert}")
                else:
                    st.caption("  Aucune alerte")
                st.markdown("")

# =============================================================================
# TAB 2 : Historique Météo
# =============================================================================
with tab2:
    st.markdown("### Historique météo")
    
    period = st.selectbox("Période", [7, 14, 30], format_func=lambda x: f"{x} derniers jours", index=2)
    
    with st.spinner("Chargement..."):
        history = get_historical_weather(days=period)
    
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
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-blue">{df['Temp Moy'].mean():.1f}°C</div>
                <div class="stat-label">Température moyenne</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{df['Précip'].sum():.1f} mm</div>
                <div class="stat-label">Précipitations totales</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{df['Vent Max'].max():.0f} km/h</div>
                <div class="stat-label">Vent maximum</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            rainy = len(df[df['Précip'] > 1])
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{rainy}</div>
                <div class="stat-label">Jours de pluie</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Graphique températures
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=df['Date'], y=df['Temp Max'], mode='lines', name='Max', line=dict(color='#EF4444', width=2)))
        fig_temp.add_trace(go.Scatter(x=df['Date'], y=df['Temp Min'], mode='lines', name='Min', line=dict(color='#3B82F6', width=2), fill='tonexty', fillcolor='rgba(59, 130, 246, 0.1)'))
        fig_temp.update_layout(
            title=dict(text="Températures", font=dict(size=14, color='#FAFAFA')),
            height=280,
            margin=dict(t=40, b=40, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
            legend=dict(orientation='h', y=1.1, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Vent et précipitations
        col1, col2 = st.columns(2)
        
        with col1:
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Bar(x=df['Date'], y=df['Vent Max'], marker_color='#8B5CF6'))
            fig_wind.add_hline(y=30, line_dash="dash", line_color="#EF4444")
            fig_wind.update_layout(
                title=dict(text="Vent maximum (km/h)", font=dict(size=13, color='#FAFAFA')),
                height=250,
                margin=dict(t=40, b=30, l=40, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_wind, use_container_width=True)
        
        with col2:
            fig_precip = go.Figure()
            fig_precip.add_trace(go.Bar(x=df['Date'], y=df['Précip'], marker_color='#00D4FF'))
            fig_precip.update_layout(
                title=dict(text="Précipitations (mm)", font=dict(size=13, color='#FAFAFA')),
                height=250,
                margin=dict(t=40, b=30, l=40, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, color='#64748B'),
                yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B')
            )
            st.plotly_chart(fig_precip, use_container_width=True)
        
        with st.expander("📋 Voir les données brutes"):
            st.dataframe(df, use_container_width=True, hide_index=True)

# =============================================================================
# TAB 3 : Analyse Corrélation
# =============================================================================
with tab3:
    st.markdown("### Analyse de corrélation Météo / Aviation")
    
    st.caption("Cette analyse étudie l'impact des conditions météo sur les opérations aériennes en calculant un score quotidien basé sur le vent, les précipitations et les phénomènes météo.")
    
    with st.spinner("Analyse en cours..."):
        history = get_historical_weather(days=30)
    
    if history and history.get('time'):
        df = pd.DataFrame({
            'Date': history['time'],
            'Vent Max': history['wind_speed_10m_max'],
            'Rafales': history['wind_gusts_10m_max'],
            'Précip': history['precipitation_sum'],
            'Code': history['weather_code']
        })
        
        # Calcul du score
        def calc_score(row):
            score = 100
            if row['Vent Max'] and row['Vent Max'] > 50: score -= 40
            elif row['Vent Max'] and row['Vent Max'] > 35: score -= 25
            elif row['Vent Max'] and row['Vent Max'] > 25: score -= 10
            
            if row['Rafales'] and row['Rafales'] > 60: score -= 20
            elif row['Rafales'] and row['Rafales'] > 45: score -= 10
            
            if row['Précip'] and row['Précip'] > 20: score -= 25
            elif row['Précip'] and row['Précip'] > 10: score -= 15
            elif row['Précip'] and row['Précip'] > 5: score -= 5
            
            if row['Code'] in [45, 48]: score -= 30
            elif row['Code'] in [95, 96, 99]: score -= 35
            elif row['Code'] in [71, 73, 75, 77]: score -= 30
            
            return max(0, min(100, score))
        
        df['Score'] = df.apply(calc_score, axis=1)
        df['Impact'] = df['Score'].apply(lambda x: 'Favorable' if x >= 80 else ('Modéré' if x >= 50 else 'Difficile'))
        
        # Stats
        favorable = len(df[df['Score'] >= 80])
        moderate = len(df[(df['Score'] >= 50) & (df['Score'] < 80)])
        difficult = len(df[df['Score'] < 50])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-green">{favorable}</div>
                <div class="stat-label">Jours favorables</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-yellow">{moderate}</div>
                <div class="stat-label">Jours modérés</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-red">{difficult}</div>
                <div class="stat-label">Jours difficiles</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg = df['Score'].mean()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value stat-blue">{avg:.0f}</div>
                <div class="stat-label">Score moyen</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Graphique corrélation
        fig = go.Figure()
        
        fig.add_hrect(y0=80, y1=100, fillcolor="#22C55E", opacity=0.1, line_width=0)
        fig.add_hrect(y0=50, y1=80, fillcolor="#EAB308", opacity=0.1, line_width=0)
        fig.add_hrect(y0=0, y1=50, fillcolor="#EF4444", opacity=0.1, line_width=0)
        
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Score'], mode='lines+markers', name='Score', line=dict(color='#00D4FF', width=2), yaxis='y'))
        fig.add_trace(go.Bar(x=df['Date'], y=df['Vent Max'], name='Vent (km/h)', marker_color='rgba(139, 92, 246, 0.5)', yaxis='y2'))
        
        fig.update_layout(
            title=dict(text="Corrélation Score Aviation / Vent", font=dict(size=14, color='#FAFAFA')),
            height=350,
            margin=dict(t=50, b=40, l=50, r=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#64748B'),
            yaxis=dict(title='Score', showgrid=True, gridcolor='#1E293B', color='#64748B', range=[0, 100]),
            yaxis2=dict(title='Vent (km/h)', overlaying='y', side='right', color='#64748B', range=[0, 80]),
            legend=dict(orientation='h', y=1.12, font=dict(color='#94A3B8'))
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plots
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.scatter(df, x='Vent Max', y='Score', color='Impact',
                             color_discrete_map={'Favorable': '#22C55E', 'Modéré': '#EAB308', 'Difficile': '#EF4444'},
                             title='Vent vs Score')
            fig1.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
                              yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'))
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.scatter(df, x='Précip', y='Score', color='Impact',
                             color_discrete_map={'Favorable': '#22C55E', 'Modéré': '#EAB308', 'Difficile': '#EF4444'},
                             title='Précipitations vs Score')
            fig2.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'),
                              yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#64748B'))
            st.plotly_chart(fig2, use_container_width=True)
        
        # Coefficient de corrélation
        df_clean = df.dropna(subset=['Vent Max', 'Score'])
        if len(df_clean) > 5:
            corr_vent = np.corrcoef(df_clean['Vent Max'], df_clean['Score'])[0, 1]
            corr_precip = np.corrcoef(df_clean['Précip'].fillna(0), df_clean['Score'])[0, 1]
            
            # Conclusion
            st.markdown("### Conclusions")
            
            windy_days = len(df[df['Vent Max'] > 30])
            
            st.markdown(f"""
            **Résumé des 30 derniers jours :**
            
            - **{favorable} jours** ({favorable/30*100:.0f}%) avec conditions favorables
            - **{difficult} jours** ({difficult/30*100:.0f}%) avec conditions difficiles  
            - **{windy_days} jours** avec vent supérieur à 30 km/h
            - Score moyen de la période : **{avg:.0f}/100**
            
            **Corrélations mesurées :**
            - Vent ↔ Score : **{corr_vent:.2f}** (corrélation négative attendue)
            - Précipitations ↔ Score : **{corr_precip:.2f}**
            
            Les données confirment une corrélation claire entre les conditions météo défavorables et la baisse du score aviation.
            """)

# =============================================================================
# TAB 4 : Méthodologie Trajectoires (NOUVELLE SECTION)
# =============================================================================
with tab4:
    st.markdown("### Méthodologie des Trajectoires")
    
    st.markdown("""
    <div class="alert-box alert-info">
        <b>💡 Cette section explique</b> comment les trajectoires des avions sont obtenues et affichées 
        dans la carte, ainsi que les limites des données gratuites disponibles.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Section 1 : Sources de données
    st.markdown("#### 1. Sources de données utilisées")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="methodology-box">
            <h4>🛫 FlightRadar24 (Vols en temps réel)</h4>
            <p style="color: #94A3B8; font-size: 0.9rem;">
            <b>Données fournies :</b>
            <ul style="margin-top: 0.5rem;">
                <li>Position temps réel (latitude, longitude)</li>
                <li>Altitude et vitesse</li>
                <li>Callsign et compagnie</li>
                <li>Origine et destination déclarées</li>
                <li>Type d'avion</li>
            </ul>
            <b style="color: #22C55E;">✓ Gratuit et illimité</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="methodology-box">
            <h4>📡 OpenSky Network (Trajectoires)</h4>
            <p style="color: #94A3B8; font-size: 0.9rem;">
            <b>Données fournies :</b>
            <ul style="margin-top: 0.5rem;">
                <li>Historique des positions (waypoints)</li>
                <li>Trajectoire complète du vol</li>
                <li>Données ADS-B brutes</li>
            </ul>
            <b style="color: #EAB308;">⚠️ Nécessite authentification</b><br>
            <small>Compte gratuit limité à quelques requêtes/jour</small>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Section 2 : Types de trajectoires
    st.markdown("#### 2. Types de trajectoires affichées")
    
    st.markdown("""
    <div class="methodology-box">
        <h4>🗺️ Deux types de trajectoires sur la carte</h4>
        
        <table style="width: 100%; margin-top: 1rem; color: #94A3B8;">
            <tr style="border-bottom: 1px solid #2D3748;">
                <td style="padding: 0.75rem;"><b style="color: #22C55E;">━━━ Ligne pleine</b></td>
                <td style="padding: 0.75rem;"><b>Trajectoire réelle (OpenSky)</b></td>
                <td style="padding: 0.75rem;">Points GPS historiques enregistrés par les récepteurs ADS-B</td>
            </tr>
            <tr>
                <td style="padding: 0.75rem;"><b style="color: #64748B;">- - - Ligne pointillée</b></td>
                <td style="padding: 0.75rem;"><b>Trajectoire estimée</b></td>
                <td style="padding: 0.75rem;">Ligne droite entre l'aéroport d'origine/destination et BVA</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Section 3 : Algorithme d'estimation
    st.markdown("#### 3. Comment sont estimées les trajectoires ?")
    
    st.markdown("""
    Quand les trajectoires réelles ne sont pas disponibles (compte OpenSky non authentifié ou vol sans données), 
    nous utilisons une **estimation simplifiée** :
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Algorithme utilisé :**
        
        ```python
        def estimate_flight_path(origin_coords, dest_coords, num_points=30):
            # Interpolation linéaire entre origine et destination
            points = []
            for i in range(num_points + 1):
                t = i / num_points
                lat = origin_lat + t * (dest_lat - origin_lat)
                lon = origin_lon + t * (dest_lon - origin_lon)
                points.append((lat, lon))
            return points
        ```
        
        **Limites de cette méthode :**
        - Ne prend pas en compte les couloirs aériens réels (SID/STAR)
        - Ignore la courbure terrestre (orthodromie)
        - Ne reflète pas les zones de contrôle aérien
        - Pas de prise en compte du vent ou de la météo
        """)
    
    with col2:
        st.markdown("""
        <div class="methodology-box">
            <h4>🎯 Précision</h4>
            <p style="color: #94A3B8;">
            <b>Trajectoire réelle :</b> ~10-50m<br>
            <b>Trajectoire estimée :</b> Indicative uniquement
            </p>
            <hr style="border-top: 1px solid #2D3748;">
            <p style="color: #64748B; font-size: 0.8rem;">
            Les trajectoires estimées servent uniquement à visualiser 
            l'origine/destination probable d'un vol.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Section 4 : Pour aller plus loin
    st.markdown("#### 4. Pour des trajectoires plus précises")
    
    st.markdown("""
    <div class="alert-box alert-warning">
        <b>APIs premium disponibles (hors cadre de ce projet) :</b>
        <ul style="margin-top: 0.5rem; margin-bottom: 0;">
            <li><b>FlightAware</b> - Historique complet et trajectoires détaillées (~$50/mois)</li>
            <li><b>AeroDataBox</b> - Retards, horaires, données aéroports (~$20/mois)</li>
            <li><b>OpenSky Premium</b> - Accès étendu aux données ADS-B</li>
            <li><b>Données AIRAC</b> - Routes officielles (SID/STAR) publiées par les autorités aériennes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Section 5 : Schéma explicatif
    st.markdown("#### 5. Schéma : Vraie trajectoire vs Estimation")
    
    st.markdown("""
    ```
                        ✈️ Vraie trajectoire (courbe, suit les couloirs aériens)
                       /
    ORIGINE ○─────────/─────────────────────○ BVA
                     /                      
                    /   - - - - - - - - - -   Trajectoire estimée (ligne droite)
                   /
                  ✈️
    
    La vraie trajectoire suit :
    • Les procédures de départ (SID - Standard Instrument Departure)
    • Les routes aériennes (Airways)  
    • Les procédures d'approche (STAR - Standard Terminal Arrival Route)
    • Les instructions du contrôle aérien
    ```
    """)
    
    st.markdown("")
    
    # Conclusion
    st.markdown("""
    <div class="methodology-box">
        <h4>📝 En résumé pour l'oral</h4>
        <p style="color: #FAFAFA;">
        "Les trajectoires affichées sur la carte proviennent de deux sources : 
        les <b>données réelles</b> via OpenSky Network (quand disponibles) montrant le chemin exact 
        suivi par l'avion, et des <b>estimations</b> (lignes droites) quand ces données ne sont pas 
        accessibles. Cette limitation est due aux restrictions des APIs gratuites. 
        Pour un projet professionnel, on utiliserait des données AIRAC officielles 
        et des APIs premium comme FlightAware."
        </p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    Données : OpenMeteo API • Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)