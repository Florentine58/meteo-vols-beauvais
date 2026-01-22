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

### Carte Interactive
- Visualisation temps réel des avions autour de Beauvais
- **Trajectoires** des vols (origines et destinations)
- Données météo en overlay
- Qualité de l'air en temps réel

###  Analyses
- Score aviation (impact météo sur les opérations)
- Prévisions 7 jours avec alertes
- Corrélation météo / trafic
- Tendances climatiques multi-annuelles

### Impact Environnemental
- Qualité de l'air (PM2.5, PM10, NO₂, O₃)
- Estimation des émissions (CO₂, NOx, particules)
- European Air Quality Index (AQI)

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
git clone https://github.com/TON_USERNAME/meteo-vols-beauvais.git
cd meteo-vols-beauvais

# Installer les dépendances
pip install -r requirements.txt

# Configurer les APIs (optionnel)
cp .env.example .env
# Éditer .env avec tes clés API

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
  - Va dans Settings > API Clients > Create New Client
  - Copie `client_id` et `client_secret` dans `.env`

## Structure du Projet

```
meteo-vols-beauvais/
├── app.py                    # Dashboard principal
├── api/
│   ├── __init__.py
│   ├── weather.py            # Météo + Qualité de l'air
│   ├── flights.py            # FlightRadar24
│   ├── air_quality.py        # Qualité de l'air détaillée
│   └── opensky_v2.py         # OpenSky avec trajectoires
├── pages/
│   ├── 1_Carte.py            # Carte interactive
│   ├── 2_Meteo.py            # Détails météo
│   ├── 3_Statistiques.py     # Analyse trafic
│   └── 4_Historique.py       # Corrélations
├── .streamlit/
│   └── config.toml           # Thème sombre
├── .env.example              # Template configuration
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
