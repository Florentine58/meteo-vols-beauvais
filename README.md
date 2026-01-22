# BVA Monitor — Météo & Vols Beauvais

Projet réalisé dans le cadre de la **Mineure Numérique B2** — Surveillance météo, trafic aérien et impact environnemental à Beauvais.

## Description

Application web interactive combinant :
- **Données météorologiques** de Beauvais (via OpenMeteo API)
- **Trafic aérien** temps réel (via FlightRadar24)
- **Qualité de l'air** et impact environnemental (via OpenMeteo Air Quality)
- **Trajectoires des avions** (via OpenSky Network)

L'objectif est de visualiser la **corrélation entre les conditions météo et l'activité aérienne**, ainsi que l'**impact environnemental** de l'aéroport.

## Fonctionnalités

### Cartes Interactives
- **Carte Temps Réel** — Visualisation live des avions autour de Beauvais (50km)
  - Positions des avions avec données de vol
  - Overlay météo et qualité de l'air
  - Filtre vols BVA / transit
- **Carte Historique** — Trajectoires passées avec waypoints
  - Visualisation des routes aériennes
  - Données météo historiques en overlay
  - Recherche par période

### Analyses Trafic Aérien
- **Vols en Direct** — Liste temps réel des vols
  - Filtrage arrivées/départs BVA
  - Statistiques par compagnie/appareil
  - Indicateurs de trafic
- **Analyse Historique** — Corrélations météo/aviation
  - Analyse multi-annuelle des tendances
  - Corrélation conditions météo / activité aérienne
  - Visualisations statistiques

### Météo & Prévisions
- **Météo Détaillée** — Conditions actuelles et prévisions
  - Score aviation (impact météo sur opérations)
  - Prévisions 7 jours avec alertes
  - Données horaires détaillées
- **Historique Météo** — Archive jusqu'à 1960
  - Tendances climatiques long terme
  - Analyse comparative par période

### Impact Environnemental
- Qualité de l'air temps réel (PM2.5, PM10, NO₂, O₃, CO, SO₂)
- European Air Quality Index (AQI)
- Impact aviation sur la qualité de l'air
- Statistiques environnementales

## Technologies

| Technologie | Usage |
|-------------|-------|
| Python 3.13 | Backend |
| Streamlit | Interface web |
| OpenMeteo API | Météo + Qualité de l'air (gratuit) |
| FlightRadar24 | Vols temps réel (gratuit) |
| OpenSky Network | Trajectoires (gratuit avec compte) |
| Folium | Cartes interactives |
| Plotly | Graphiques |

## Installation

```bash
# Cloner le projet
git clone https://github.com/Florentine58/meteo-vols-beauvais.git
cd meteo-vols-beauvais

# Installer les dépendances
pip install -r requirements.txt

# Configurer les APIs (optionnel)
# Créer un fichier .env à la racine du projet avec :
# OPENSKY_USERNAME=ton_username
# OPENSKY_PASSWORD=ton_password
# RAPIDAPI_KEY=ta_cle_rapidapi

# Lancer l'application
streamlit run app.py
```

## Configuration API

### APIs Gratuites (sans configuration)
- **OpenMeteo Weather** — Météo actuelle, prévisions, historique
- **OpenMeteo Air Quality** — Qualité de l'air, polluants
- **FlightRadar24** — Vols temps réel

### APIs Optionnelles (nécessitent un compte)
- **OpenSky Network** — Trajectoires détaillées des avions
  - Crée un compte sur [opensky-network.org](https://opensky-network.org)
  - Ajoute tes identifiants dans un fichier `.env` :
    ```
    OPENSKY_USERNAME=ton_username
    OPENSKY_PASSWORD=ton_password
    ```
- **AeroDataBox (RapidAPI)** — Données FIDS (arrivées/départs détaillées)
  - Optionnel, nécessite une clé RapidAPI
  - Ajoute dans `.env` : `RAPIDAPI_KEY=ta_cle`

## Structure du Projet

```
meteo-vols-beauvais/
├── app.py                    # Dashboard principal
├── test_api.py               # Tests de connexion aux APIs
├── api/
│   ├── __init__.py           # Exports des modules
│   ├── weather.py            # Météo OpenMeteo
│   ├── air_quality.py        # Qualité de l'air OpenMeteo
│   ├── flights.py            # FlightRadar24
│   ├── opensky_v2.py         # OpenSky trajectoires (v2 - préféré)
│   ├── opensky.py            # OpenSky legacy
│   └── aerodatabox.py        # AeroDataBox (RapidAPI)
├── pages/
│   ├── Carte.py              # Carte temps réel
│   ├── Meteo.py              # Détails météo
│   ├── Vols.py               # Analyse trafic aérien
│   ├── Statistiques.py       # Stats & qualité de l'air
│   ├── Historique.py         # Données historiques & prévisions
│   ├── AnalyseHistorique.py  # Corrélations météo/aviation
│   └── CarteHistorique.py    # Trajectoires historiques
├── .streamlit/
│   └── config.toml           # Thème sombre aviation
├── requirements.txt
└── README.md
```

## Données Disponibles

### Météo (OpenMeteo)
- Température, humidité, vent
- Prévisions 7 jours
- Historique jusqu'à 1940

### Qualité de l'Air
- PM2.5, PM10 (particules fines)
- NO₂, O₃, CO, SO₂
- Index AQI européen

### Trafic Aérien
- Position temps réel des avions
- Origine / Destination
- Altitude, vitesse, cap
- Trajectoires (avec OpenSky)

## Contexte Académique

| | |
|---|---|
| **Formation** | Mineure Numérique B2 |
| **Durée** | 14 jours |
| **Auteur** | Meunier Florentine |
| **Date** | 2025 |

## Licence

Projet éducatif — Tous droits réservés.

---

*Sources de données : OpenMeteo, FlightRadar24, OpenSky Network*
