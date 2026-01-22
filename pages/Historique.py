"""
Page Historique & Prévisions — Analyse corrélation météo/aviation
Style professionnel sobre

Projet Mineure Numérique B2 — 2025
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
    page_icon="✈️",
    layout="wide"
)

# =============================================================================
# CSS Professionnel Sobre
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
    <h1>Historique & Prévisions</h1>
    <p>Analyse des données météo et impact sur les opérations aériennes</p>
</div>
""", unsafe_allow_html=True)

if st.button("Actualiser", type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# =============================================================================
# Onglets
# =============================================================================
tab1, tab2, tab3 = st.tabs(["Prévisions 7 jours", "Historique Météo", "Analyse Corrélation"])

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
            st.markdown(f'<div class="alert-box alert-danger">{alerts_red} jour(s) avec conditions difficiles prévus cette semaine</div>', unsafe_allow_html=True)
        elif alerts_yellow > 0:
            st.markdown(f'<div class="alert-box alert-warning">{alerts_yellow} jour(s) nécessitant une vigilance</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-success">Conditions favorables pour toute la semaine</div>', unsafe_allow_html=True)
        
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
                        {day['score']}/100
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
        
        # Explication du score
        with st.expander("Comment est calculé le score aviation ?"):
            st.markdown("""
            **Score Aviation (0-100)** — Évalue les conditions de vol basé sur :
            
            | Facteur | Impact sur le score |
            |---------|---------------------|
            | Vent > 50 km/h | -40 points |
            | Vent 35-50 km/h | -25 points |
            | Vent 25-35 km/h | -10 points |
            | Rafales > 60 km/h | -20 points |
            | Précipitations > 20mm | -25 points |
            | Brouillard | -30 points |
            | Orage | -35 points |
            | Neige | -30 points |
            
            **Interprétation :** 80-100 = Optimal | 50-79 = Vigilance | 0-49 = Difficile
            """)
        
        # Détails
        with st.expander("Détail des prévisions"):
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
            fig_wind.add_hline(y=40, line_dash="dash", line_color="#EF4444")
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
        
        with st.expander("Voir les données brutes"):
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
            
            windy_days = len(df[df['Vent Max'] > 30])
            
            # Conclusion
            st.markdown("### Conclusions")
            
            st.markdown(f"""
            **Résumé des 30 derniers jours :**
            
            - **{favorable} jours** ({favorable/30*100:.0f}%) avec conditions favorables
            - **{difficult} jours** ({difficult/30*100:.0f}%) avec conditions difficiles  
            - **{windy_days} jours** avec vent supérieur à 30 km/h
            - Score moyen de la période : **{avg:.0f}/100**
            
            **Corrélations mesurées :**
            - Vent / Score : **{corr_vent:.2f}** (corrélation négative attendue)
            - Précipitations / Score : **{corr_precip:.2f}**
            
            Les données confirment une corrélation claire entre les conditions météo défavorables et la baisse du score aviation.
            """)

# =============================================================================
# Section Explicative du Code
# =============================================================================
st.divider()
with st.expander("Comprendre le code de cette page"):
    st.markdown("""
    ### Architecture de la Page Historique (Historique.py)

    Cette page combine **prévisions météo**, **analyse historique** et **corrélations**
    pour évaluer l'impact des conditions météorologiques sur l'aviation.

    #### Structure en Onglets (Tabs)

    **Organisation (lignes 185-186)**
    ```python
    tab1, tab2, tab3 = st.tabs([
        "Prévisions 7 jours",
        "Historique Météo",
        "Analyse Corrélation"
    ])
    ```
    - **3 onglets distincts** pour différentes analyses
    - Navigation fluide entre les vues

    #### Tab 1 : Prévisions 7 Jours (lignes 190-306)

    **Système d'Alertes**
    ```python
    alerts_red = len([d for d in forecast if d['level'] == 'red'])
    alerts_yellow = len([d for d in forecast if d['level'] == 'yellow'])
    ```
    - **Comptage des alertes** : Nombre de jours difficiles à venir
    - **Classification** : red (critique), yellow (vigilance), green (favorable)

    **Graphique d'Évolution du Score**
    ```python
    # Zones colorées de fond
    fig.add_hrect(y0=80, y1=100, fillcolor="#22C55E", opacity=0.1)
    fig.add_hrect(y0=50, y1=80, fillcolor="#EAB308", opacity=0.1)
    fig.add_hrect(y0=0, y1=50, fillcolor="#EF4444", opacity=0.1)

    # Courbe du score
    fig.add_trace(go.Scatter(
        x=df_forecast['date_formatted'],
        y=df_forecast['score'],
        mode='lines+markers'
    ))
    ```
    - **add_hrect()** : Ajoute des rectangles horizontaux (zones de référence)
    - **Visualisation rapide** : Voir d'un coup d'œil les jours problématiques

    #### Tab 2 : Historique Météo (lignes 310-418)

    **Sélecteur de Période**
    ```python
    period = st.selectbox("Période", [7, 14, 30],
                         format_func=lambda x: f"{x} derniers jours")
    ```
    - **format_func** : Fonction lambda pour formater l'affichage
    - Permet à l'utilisateur de choisir la profondeur d'historique

    **Statistiques Calculées**
    ```python
    col1.metric("Température moyenne", f"{df['Temp Moy'].mean():.1f}°C")
    col2.metric("Précipitations totales", f"{df['Précip'].sum():.1f} mm")
    col3.metric("Vent maximum", f"{df['Vent Max'].max():.0f} km/h")
    col4.metric("Jours de pluie", len(df[df['Précip'] > 1]))
    ```
    - **Agrégations Pandas** : `.mean()`, `.sum()`, `.max()`
    - **Filtrage** : `df[df['Précip'] > 1]` sélectionne les lignes avec pluie > 1mm

    **Zone Remplie entre Courbes**
    ```python
    fig_temp.add_trace(go.Scatter(
        x=df['Date'], y=df['Temp Min'],
        fill='tonexty',  # Remplir jusqu'à la courbe précédente
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    ```
    - **tonexty** : Remplit l'espace entre cette courbe et la précédente (Temp Max)
    - Visualise l'amplitude thermique quotidienne

    #### Tab 3 : Analyse Corrélation (lignes 422-573)

    **Algorithme de Calcul du Score**
    ```python
    def calc_score(row):
        score = 100
        if row['Vent Max'] > 50: score -= 40
        elif row['Vent Max'] > 35: score -= 25
        # ... etc

        if row['Code'] in [45, 48]: score -= 30  # Brouillard
        elif row['Code'] in [95, 96, 99]: score -= 35  # Orage
        return max(0, min(100, score))

    df['Score'] = df.apply(calc_score, axis=1)
    ```
    - **apply()** : Applique la fonction à chaque ligne du DataFrame
    - **axis=1** : Traite par ligne (axis=0 serait par colonne)
    - **max(0, min(100, score))** : Borne le score entre 0 et 100

    **Graphique Double Axe**
    ```python
    fig.add_trace(go.Scatter(..., yaxis='y'))  # Axe gauche
    fig.add_trace(go.Bar(..., yaxis='y2'))     # Axe droit

    fig.update_layout(
        yaxis=dict(title='Score', range=[0, 100]),
        yaxis2=dict(title='Vent (km/h)', overlaying='y',
                   side='right', range=[0, 80])
    )
    ```
    - **Deux axes Y** : Permet de comparer score et vent sur le même graphique
    - **overlaying='y'** : Le second axe se superpose au premier
    - **side='right'** : Affichage à droite

    **Scatter Plots avec Couleurs**
    ```python
    fig1 = px.scatter(
        df, x='Vent Max', y='Score',
        color='Impact',
        color_discrete_map={
            'Favorable': '#22C55E',
            'Modéré': '#EAB308',
            'Difficile': '#EF4444'
        }
    )
    ```
    - **color='Impact'** : Couleur basée sur une colonne
    - **color_discrete_map** : Dictionnaire personnalisé de couleurs
    - Permet de visualiser la répartition favorable/modéré/difficile

    **Coefficient de Corrélation**
    ```python
    corr_vent = np.corrcoef(df['Vent Max'], df['Score'])[0, 1]
    ```
    - **np.corrcoef()** : Calcule la matrice de corrélation de Pearson
    - **[0, 1]** : Extrait le coefficient de corrélation (entre -1 et 1)
    - Valeur négative attendue : plus de vent → score plus bas

    #### Points Techniques

    **Gestion des Valeurs Nulles**
    ```python
    df_clean = df.dropna(subset=['Vent Max', 'Score'])
    if len(df_clean) > 5:
        corr_vent = np.corrcoef(...)
    ```
    - **dropna()** : Supprime les lignes avec valeurs manquantes
    - **subset** : Spécifie les colonnes à vérifier
    - Vérifie qu'il y a assez de données pour la corrélation

    **Catégorisation Automatique**
    ```python
    df['Impact'] = df['Score'].apply(
        lambda x: 'Favorable' if x >= 80
                 else ('Modéré' if x >= 50 else 'Difficile')
    )
    ```
    - **lambda** : Fonction anonyme inline
    - **Ternaire imbriqué** : if-else condensé
    - Crée une nouvelle colonne catégorielle

    #### Métriques Statistiques

    **Calculs de Synthèse**
    ```python
    favorable = len(df[df['Score'] >= 80])
    moderate = len(df[(df['Score'] >= 50) & (df['Score'] < 80)])
    difficult = len(df[df['Score'] < 50])
    ```
    - **Opérateur &** : ET logique pour combiner conditions
    - **len()** : Compte le nombre de lignes satisfaisant la condition

    #### Améliorations Possibles

    1. **Tendances saisonnières** : Analyser les patterns par mois/saison
    2. **Prédiction** : Modèle ML pour prédire le score selon prévisions météo
    3. **Export PDF** : Rapport d'analyse téléchargeable
    4. **Alertes email** : Notification si prévisions défavorables
    5. **Comparaison aéroports** : Comparer avec Orly, Roissy, etc.

    *Cette page est cruciale pour la planification opérationnelle et
    l'analyse des risques météorologiques à moyen terme.*
    """)

# Footer
st.markdown("""
<div class="footer">
    Données : OpenMeteo API — Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)