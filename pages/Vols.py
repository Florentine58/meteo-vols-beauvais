"""
Page Vols — Trafic aérien autour de Paris-Beauvais
Distinction claire entre vols BVA et vols en transit
Style professionnel sobre

Projet Mineure Numérique B2 — 2025
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import des modules API
from api.flights import get_flights_in_area, get_airport_info, get_airlines_stats, get_aircraft_stats

# Configuration de la page
st.set_page_config(
    page_title="BVA Monitor | Vols",
    page_icon="✈️",
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
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    .stat-value { font-size: 1.5rem; font-weight: 700; color: #FAFAFA; }
    .stat-label { font-size: 0.7rem; color: #64748B; text-transform: uppercase; }
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
    
    .flight-card-arrival { border-left-color: #22C55E; }
    .flight-card-departure { border-left-color: #F97316; }
    .flight-card-transit { border-left-color: #64748B; }
    
    .alert-box {
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    .alert-info { background: rgba(0, 212, 255, 0.1); border-left: 3px solid #00D4FF; color: #7DD3FC; }
    
    .legend-box {
        background: #151B28;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2D3748;
        margin: 1rem 0;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0;
        font-size: 0.85rem;
        color: #94A3B8;
    }
    
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
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
    hr { border: none; border-top: 1px solid #2D3748; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Fonctions de classification
# =============================================================================
def classify_flight(flight):
    """
    Classifie un vol : arrivée BVA, départ BVA, ou transit.
    """
    origin = flight.get('origin', 'N/A')
    destination = flight.get('destination', 'N/A')
    
    is_arriving_bva = destination in ['BVA', 'LFOB']
    is_departing_bva = origin in ['BVA', 'LFOB']
    
    if is_arriving_bva:
        return 'arrival'
    elif is_departing_bva:
        return 'departure'
    else:
        return 'transit'


# =============================================================================
# En-tête
# =============================================================================
st.markdown("""
<div class="page-header">
    <h1>Trafic Aérien — Paris-Beauvais</h1>
    <p>Surveillance des vols dans un rayon de 50 km autour de l'aéroport</p>
</div>
""", unsafe_allow_html=True)

# Explication de la page
st.markdown("""
<div class="alert-box alert-info">
    <b>Comprendre cette page :</b><br>
    Cette page affiche <b>tous les avions</b> dans un rayon de 50 km autour de Beauvais, pas seulement les vols BVA.<br>
    Les vols sont classés en 3 catégories : <span style="color:#22C55E">Arrivées BVA</span> | 
    <span style="color:#F97316">Départs BVA</span> | <span style="color:#94A3B8">Transit</span> (avions de passage)
</div>
""", unsafe_allow_html=True)

# Contrôles
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("Actualiser", type="primary", use_container_width=True):
        st.rerun()

st.divider()

# =============================================================================
# Chargement des données
# =============================================================================
with st.spinner("Recherche des vols en cours..."):
    flights = get_flights_in_area()
    airport = get_airport_info()

# Classifier les vols
arrivals_bva = []
departures_bva = []
transit_flights = []

for flight in flights:
    category = classify_flight(flight)
    flight['category'] = category
    
    if category == 'arrival':
        arrivals_bva.append(flight)
    elif category == 'departure':
        departures_bva.append(flight)
    else:
        transit_flights.append(flight)

# Compter en vol vs au sol
in_flight = len([f for f in flights if not f.get('on_ground', False)])
on_ground = len([f for f in flights if f.get('on_ground', False)])

# =============================================================================
# Métriques principales
# =============================================================================
st.markdown("### Vue d'ensemble")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-blue">{len(flights)}</div>
        <div class="stat-label">Total Zone 50km</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-green">{len(arrivals_bva)}</div>
        <div class="stat-label">Arrivées BVA</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-orange">{len(departures_bva)}</div>
        <div class="stat-label">Départs BVA</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value stat-gray">{len(transit_flights)}</div>
        <div class="stat-label">Transit</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{in_flight}</div>
        <div class="stat-label">En vol</div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{on_ground}</div>
        <div class="stat-label">Au sol</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# Liste des vols par catégorie
# =============================================================================
if flights:
    st.markdown("### Détail des vols")
    
    col1, col2, col3 = st.columns(3)
    
    # Arrivées BVA
    with col1:
        st.markdown(f"#### Arrivées BVA ({len(arrivals_bva)})")
        
        if arrivals_bva:
            for flight in arrivals_bva[:8]:
                status = "Au sol" if flight.get('on_ground') else f"{flight['altitude']} ft"
                origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
                
                st.markdown(f"""
                <div class="flight-card flight-card-arrival">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #22C55E;">{flight['callsign']}</strong>
                        <span style="font-size: 0.75rem; color: #64748B;">{status}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.25rem;">
                        {origin} → <b>BVA</b> | {flight['aircraft_type']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(arrivals_bva) > 8:
                st.caption(f"... et {len(arrivals_bva) - 8} autres")
        else:
            st.caption("Aucune arrivée en cours")
    
    # Départs BVA
    with col2:
        st.markdown(f"#### Départs BVA ({len(departures_bva)})")
        
        if departures_bva:
            for flight in departures_bva[:8]:
                status = "Au sol" if flight.get('on_ground') else f"{flight['altitude']} ft"
                dest = flight['destination'] if flight['destination'] != 'N/A' else '???'
                
                st.markdown(f"""
                <div class="flight-card flight-card-departure">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #F97316;">{flight['callsign']}</strong>
                        <span style="font-size: 0.75rem; color: #64748B;">{status}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.25rem;">
                        <b>BVA</b> → {dest} | {flight['aircraft_type']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(departures_bva) > 8:
                st.caption(f"... et {len(departures_bva) - 8} autres")
        else:
            st.caption("Aucun départ en cours")
    
    # Transit
    with col3:
        st.markdown(f"#### Transit ({len(transit_flights)})")
        
        if transit_flights:
            for flight in transit_flights[:8]:
                status = "Au sol" if flight.get('on_ground') else f"{flight['altitude']} ft"
                origin = flight['origin'] if flight['origin'] != 'N/A' else '?'
                dest = flight['destination'] if flight['destination'] != 'N/A' else '?'
                
                st.markdown(f"""
                <div class="flight-card flight-card-transit">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #94A3B8;">{flight['callsign']}</strong>
                        <span style="font-size: 0.75rem; color: #64748B;">{status}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #64748B; margin-top: 0.25rem;">
                        {origin} → {dest} | {flight['aircraft_type']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(transit_flights) > 8:
                st.caption(f"... et {len(transit_flights) - 8} autres")
        else:
            st.caption("Aucun transit détecté")

    st.divider()
    
    # =============================================================================
    # Statistiques compagnies et avions
    # =============================================================================
    st.markdown("### Statistiques")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Compagnies aériennes")
        airlines_stats = get_airlines_stats(flights)
        
        if airlines_stats:
            # Trier par nombre de vols
            sorted_airlines = sorted(airlines_stats.items(), key=lambda x: x[1], reverse=True)
            
            for airline, count in sorted_airlines[:6]:
                pct = count / len(flights) * 100
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #2D3748;">
                    <span style="color: #FAFAFA;">{airline}</span>
                    <span style="color: #00D4FF;">{count} vols ({pct:.0f}%)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Données insuffisantes")
    
    with col2:
        st.markdown("#### Types d'avions")
        aircraft_stats = get_aircraft_stats(flights)
        
        if aircraft_stats:
            sorted_aircraft = sorted(aircraft_stats.items(), key=lambda x: x[1], reverse=True)
            
            for aircraft, count in sorted_aircraft[:6]:
                pct = count / len(flights) * 100
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #2D3748;">
                    <span style="color: #FAFAFA;">{aircraft}</span>
                    <span style="color: #8B5CF6;">{count} ({pct:.0f}%)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Données insuffisantes")
    
    st.divider()
    
    # =============================================================================
    # Tableau complet
    # =============================================================================
    st.markdown("### Tableau complet")
    
    with st.expander("Voir tous les vols"):
        df = pd.DataFrame(flights)
        
        # Ajouter la catégorie lisible
        category_map = {'arrival': 'Arrivée BVA', 'departure': 'Départ BVA', 'transit': 'Transit'}
        df['Catégorie'] = df['category'].map(category_map)
        
        # Sélectionner les colonnes à afficher
        cols_to_show = ['callsign', 'Catégorie', 'airline_icao', 'aircraft_type', 'origin', 'destination', 'altitude', 'ground_speed', 'on_ground']
        df_display = df[[c for c in cols_to_show if c in df.columns]].copy()
        df_display.columns = ['Callsign', 'Catégorie', 'Compagnie', 'Avion', 'Origine', 'Destination', 'Altitude (ft)', 'Vitesse (kts)', 'Au sol']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

else:
    st.info("Aucun vol détecté dans la zone de 50 km autour de Beauvais. Cela peut arriver si le trafic est faible à cette heure.")

# =============================================================================
# Informations aéroport
# =============================================================================
st.divider()
st.markdown("### Informations sur l'aéroport")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**{airport['name']}**")
    st.caption(f"IATA: {airport['code_iata']} | ICAO: {airport['code_icao']}")

with col2:
    st.markdown("**Localisation**")
    st.caption(f"{airport['city']}, {airport['country']}")
    st.caption(f"Altitude: {airport['altitude']} m")

with col3:
    st.markdown("**Compagnies principales**")
    st.caption(" | ".join(airport['principales_compagnies']))

# =============================================================================
# Légende
# =============================================================================
st.markdown("""
<div class="legend-box">
    <div style="font-weight: 600; color: #FAFAFA; margin-bottom: 0.5rem;">Légende des catégories</div>
    <div class="legend-item">
        <div class="legend-dot" style="background: #22C55E;"></div>
        <b>Arrivées BVA</b> — Vols dont la destination est Paris-Beauvais
    </div>
    <div class="legend-item">
        <div class="legend-dot" style="background: #F97316;"></div>
        <b>Départs BVA</b> — Vols partant de Paris-Beauvais
    </div>
    <div class="legend-item">
        <div class="legend-dot" style="background: #64748B;"></div>
        <b>Transit</b> — Avions passant dans la zone sans s'arrêter à BVA (ex: Paris-CDG vers Londres)
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# Section Explicative du Code
# =============================================================================
st.divider()
with st.expander("📘 Comprendre le code de cette page"):
    st.markdown("""
    ### Architecture de la Page Vols (Vols.py)

    Cette page affiche le **trafic aérien détaillé** autour de Paris-Beauvais avec une
    classification claire : arrivées BVA, départs BVA, et vols en transit.

    #### 📦 Fonction de Classification (lignes 119-134)

    **classify_flight() - Logique Métier**
    ```python
    def classify_flight(flight):
        origin = flight.get('origin', 'N/A')
        destination = flight.get('destination', 'N/A')

        if destination in ['BVA', 'LFOB']:
            return 'arrival'
        elif origin in ['BVA', 'LFOB']:
            return 'departure'
        else:
            return 'transit'
    ```
    - **BVA** : Code IATA de Paris-Beauvais
    - **LFOB** : Code ICAO de Paris-Beauvais
    - **Transit** : Tous les autres vols dans la zone 50 km

    **Codes Aéroport**
    | Type | Code | Usage |
    |------|------|-------|
    | IATA | BVA | Code 3 lettres (billets, bagages) |
    | ICAO | LFOB | Code 4 lettres (ATC, plans de vol) |

    #### 📊 Métriques Principales (lignes 195-245)

    **Classification Automatique**
    ```python
    for flight in flights:
        category = classify_flight(flight)
        flight['category'] = category

        if category == 'arrival':
            arrivals_bva.append(flight)
        elif category == 'departure':
            departures_bva.append(flight)
        else:
            transit_flights.append(flight)
    ```
    - **Ajout de propriété** : `flight['category']` enrichit les données
    - **Répartition** : Tri dans 3 listes distinctes

    **Comptage En Vol vs Au Sol**
    ```python
    in_flight = len([f for f in flights if not f.get('on_ground', False)])
    on_ground = len([f for f in flights if f.get('on_ground', False)])
    ```
    - **List comprehension avec filtre**
    - **get('on_ground', False)** : Valeur par défaut si clé absente

    #### 🎨 Affichage des Vols (lignes 250-335)

    **3 Colonnes Égales**
    ```python
    col1, col2, col3 = st.columns(3)

    with col1:  # Arrivées BVA
        for flight in arrivals_bva[:8]:  # Limite 8 premiers
            st.markdown(f\"\"\"
            <div class="flight-card flight-card-arrival">
                <strong style="color: #22C55E;">{flight['callsign']}</strong>
                {origin} → <b>BVA</b> | {flight['aircraft_type']}
            </div>
            \"\"\")
    ```
    - **[:8]** : Slicing Python, affiche seulement les 8 premiers
    - **HTML embarqué** : Style personnalisé avec classes CSS
    - **Couleurs** : Vert (arrivée), Orange (départ), Gris (transit)

    **Gestion des Listes Longues**
    ```python
    if len(arrivals_bva) > 8:
        st.caption(f"... et {len(arrivals_bva) - 8} autres")
    ```
    - Évite de surcharger l'interface
    - Indique qu'il y a plus de données

    #### 📈 Statistiques (lignes 340-381)

    **Tri par Fréquence**
    ```python
    airlines_stats = get_airlines_stats(flights)
    sorted_airlines = sorted(
        airlines_stats.items(),
        key=lambda x: x[1],  # Trier par valeur (nombre de vols)
        reverse=True         # Décroissant
    )
    ```
    - **items()** : Retourne les paires (clé, valeur)
    - **lambda x: x[1]** : Fonction de tri sur la valeur

    **Affichage avec Pourcentages**
    ```python
    for airline, count in sorted_airlines[:6]:
        pct = count / len(flights) * 100
        st.markdown(f\"\"\"
        <div>
            <span>{airline}</span>
            <span>{count} vols ({pct:.0f}%)</span>
        </div>
        \"\"\")
    ```
    - **Calcul dynamique** du pourcentage
    - **:.0f** : Format sans décimale

    #### 🗂️ Tableau Complet (lignes 387-401)

    **DataFrame Pandas**
    ```python
    df = pd.DataFrame(flights)

    # Mapping catégorie
    category_map = {
        'arrival': 'Arrivée BVA',
        'departure': 'Départ BVA',
        'transit': 'Transit'
    }
    df['Catégorie'] = df['category'].map(category_map)

    # Sélection colonnes
    cols_to_show = ['callsign', 'Catégorie', 'airline_icao', ...]
    df_display = df[[c for c in cols_to_show if c in df.columns]]
    ```
    - **map()** : Remplace les valeurs selon un dictionnaire
    - **List comprehension** : Sélection conditionnelle des colonnes
    - **Sécurité** : Vérifie que la colonne existe

    **Renommage des Colonnes**
    ```python
    df_display.columns = [
        'Callsign', 'Catégorie', 'Compagnie',
        'Avion', 'Origine', 'Destination',
        'Altitude (ft)', 'Vitesse (kts)', 'Au sol'
    ]
    ```
    - **Noms lisibles** en français
    - **Unités explicites** : (ft), (kts)

    #### 🔧 Points Techniques

    **Gestion des Valeurs Manquantes**
    ```python
    origin = flight['origin'] if flight['origin'] != 'N/A' else '???'
    status = "Au sol" if flight.get('on_ground') else f"{flight['altitude']} ft"
    ```
    - **Ternaire** : if-else condensé
    - **Affichage cohérent** : Remplace les valeurs invalides

    **Classes CSS Dynamiques**
    ```python
    <div class="flight-card flight-card-arrival">  # Arrivée
    <div class="flight-card flight-card-departure">  # Départ
    <div class="flight-card flight-card-transit">  # Transit
    ```
    - **Multiple classes** : Classe de base + classe spécifique
    - **Bordure colorée** via `border-left-color` en CSS

    #### 📊 Légende (lignes 430-446)

    **Box Explicative**
    ```python
    st.markdown(\"\"\"
    <div class="legend-box">
        <div class="legend-item">
            <div class="legend-dot" style="background: #22C55E;"></div>
            <b>Arrivées BVA</b> — Vols dont la destination est BVA
        </div>
        <!-- ... -->
    </div>
    \"\"\")
    ```
    - **Pastilles colorées** pour la légende
    - **Explications détaillées** de chaque catégorie

    #### 🚀 Améliorations Possibles

    1. **Filtrage** : Filtrer par compagnie, type d'avion, altitude
    2. **Tri** : Trier par altitude, vitesse, heure d'arrivée
    3. **Recherche** : Chercher un callsign spécifique
    4. **Historique** : Voir les vols des dernières heures
    5. **Export** : Télécharger la liste en CSV/Excel
    6. **Notifications** : Alertes pour vols spécifiques

    *Cette page permet de surveiller précisément l'activité aérienne
    et de distinguer le trafic BVA des vols en transit.*
    """)

# =============================================================================
# Footer
# =============================================================================
st.markdown(f"""
<div class="footer">
    Données : FlightRadar24 API — Usage éducatif uniquement<br>
    Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""", unsafe_allow_html=True)