"""
Météo & Vols Beauvais
Application Streamlit pour visualiser la météo et le trafic aérien à Beauvais.
"""

import streamlit as st

# Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="Météo & Vols Beauvais",
    page_icon="",
    layout="wide"
)

# Titre principal
st.title("Météo & Vols Beauvais")
st.markdown("*Surveillance météo et trafic aérien de l'aéroport Paris-Beauvais*")

# Ligne de séparation
st.divider()

# Deux colonnes pour météo et vols
col1, col2 = st.columns(2)

with col1:
    st.header("🌤️ Météo")
    st.info("Les données météo apparaîtront ici.")
    # TODO: Appeler api/weather.py et afficher les données

with col2:
    st.header("Trafic aérien")
    st.info("Les données de vols apparaîtront ici.")
    # TODO: Appeler api/flights.py et afficher les données

# Section carte (pleine largeur)
st.divider()
st.header("Carte interactive")
st.info("La carte de Beauvais avec météo et trajectoires apparaîtra ici.")
# TODO: Intégrer une carte Folium

# Footer
st.divider()
st.caption("Projet Mineure Numérique B2 — 2025")