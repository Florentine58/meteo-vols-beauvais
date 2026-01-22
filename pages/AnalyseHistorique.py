"""
Page Analyse Historique — Corrélation Météo & Aviation
Style sobre professionnel
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
    get_long_term_historical_weather
)

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Analyse Historique",
    page_icon="📊",
    layout="wide"
)

# =============================================================================
# CSS Professionnel Sobre
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
# Fonctions utilitaires
# =============================================================================
def render_stat_card(value, label, color_class=""):
    """Affiche une carte de statistique de manière standardisée."""
    return f"""
    <div class="stat-card">
        <div class="stat-value {color_class}">{value}</div>
        <div class="stat-label">{label}</div>
    </div>
    """

# =============================================================================
# En-tête
# =============================================================================
st.markdown("""
<div class="page-header">
    <h1>Analyse Historique & Corrélations</h1>
    <p>Analyse approfondie des tendances climatiques et corrélations météo-aviation</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Onglets
# =============================================================================
tab1, tab2 = st.tabs([
    "Corrélations Avancées",
    "Tendances Multi-Annuelles"
])

# =============================================================================
# TAB 1 : Corrélations Avancées
# =============================================================================
with tab1:
    st.markdown("### Analyse des Corrélations Météo-Aviation")

    st.markdown("""
    <div class="alert-box alert-info">
        <b>Méthodologie :</b> Analyse statistique des corrélations entre conditions météorologiques
        et score aviation basée sur les 30 derniers jours de données.
    </div>
    """, unsafe_allow_html=True)



    with st.expander("ℹ️ Comment est calculé le score aviation ?"):
        st.markdown("""
        <div class="methodology-box">
            <h4 style="color: #00D4FF; margin-top: 0;">Algorithme du Score Aviation</h4>

            Le score part de **100** et diminue selon les conditions :

            | Facteur | Condition | Impact |
            |---------|-----------|--------|
            | **Vent** | > 50 km/h | -40 pts |
            | | 35-50 km/h | -25 pts |
            | | 25-35 km/h | -10 pts |
            | **Précipitations** | > 20 mm | -25 pts |
            | | 10-20 mm | -15 pts |
            | | 5-10 mm | -5 pts |

            **Interprétation :**
            - **80-100** : Conditions favorables
            - **50-79** : Vigilance recommandée
            - **0-49** : Conditions difficiles
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Analyse statistique sur 30 jours")

    history = get_historical_weather(days=30)
    if history and history.get('time'):
        df_hist = pd.DataFrame({
            'Date': history['time'],
            'Vent': history['wind_speed_10m_max'],
            'Précip': history['precipitation_sum']
        })

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
            - Corrélation Vent / Score : **{corr_vent:.2f}** (négative = plus de vent = score plus bas)
            - Corrélation Précip / Score : **{corr_precip:.2f}**
            """)

# =============================================================================
# TAB 2 : Tendances Multi-Annuelles
# =============================================================================
with tab2:
    st.markdown("### Évolution climatique multi-annuelle")
    
    st.markdown("""
    <div class="alert-box alert-info">
        <b>Source :</b> OpenMeteo Archive fournit des données météo depuis 1940.
        Cette analyse permet d'identifier les tendances à long terme.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_year = st.selectbox(
            "Année de début",
            options=[2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2010, 2005, 2000, 1995, 1990],
            index=5,
            key="start_year"
        )
    
    with col2:
        end_options = [y for y in [2026, 2025, 2024, 2023, 2022, 2021, 2020] if y >= start_year]
        end_year = st.selectbox(
            "Année de fin",
            options=end_options,
            index=0,
            key="end_year"
        )
    
    with col3:
        if st.button("Analyser", type="primary"):
            st.session_state['analyze_climate'] = True
    
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
                temp_trend = df_years['Temp Moy'].iloc[-1] - df_years['Temp Moy'].iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    color = "stat-red" if temp_trend > 0.5 else "stat-blue" if temp_trend < -0.5 else ""
                    sign = "+" if temp_trend > 0 else ""
                    st.markdown(render_stat_card(f"{sign}{temp_trend:.1f}°C", "Évolution température", color), unsafe_allow_html=True)

                with col2:
                    avg_wind_days = df_years['Jours Vent Fort'].mean()
                    st.markdown(render_stat_card(f"{avg_wind_days:.0f}", "Moy. jours vent fort/an", "stat-yellow"), unsafe_allow_html=True)

                with col3:
                    avg_fog = df_years['Jours Brouillard'].mean()
                    st.markdown(render_stat_card(f"{avg_fog:.0f}", "Moy. jours brouillard/an"), unsafe_allow_html=True)

                with col4:
                    avg_storm = df_years['Jours Orage'].mean()
                    st.markdown(render_stat_card(f"{avg_storm:.0f}", "Moy. jours orage/an", "stat-orange"), unsafe_allow_html=True)
                
                st.markdown("")
                
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=df_years['Année'], y=df_years['Temp Moy'],
                    mode='lines+markers',
                    line=dict(color='#EF4444', width=3),
                    marker=dict(size=10),
                    name='Température moyenne'
                ))
                
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
                
                with st.expander("Voir les données annuelles"):
                    st.dataframe(df_years, use_container_width=True, hide_index=True)
                
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
    Données : OpenMeteo API & FlightRadar24 — Projet Mineure Numérique B2 — 2025
</div>
""", unsafe_allow_html=True)