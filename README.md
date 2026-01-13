# Météo & Vols Beauvais

Projet réalisé dans le cadre de la **Mineure Numérique B2** — Surveillance météo et trafic aérien à Beauvais.

## Description

Application web interactive qui combine :
- **Données météorologiques** de Beauvais (via OpenMeteo API)
- **Trafic aérien** de l'aéroport Paris-Beauvais BVA (via Flightradar24)

L'objectif est de visualiser la corrélation entre les conditions météo et l'activité aérienne.

## Fonctionnalités prévues

- [ ] Carte interactive de Beauvais avec données météo
- [ ] Visualisation des trajectoires d'avions (arrivées/départs)
- [ ] Graphiques : trafic par heure, température, vent
- [ ] Analyse de l'impact météo sur les vols

## Technologies utilisées

- **Python 3.13**
- **Streamlit** — Interface web interactive
- **OpenMeteo API** — Données météorologiques gratuites
- **Flightradar24** — Données de trafic aérien
- **Folium** — Cartes interactives
- **Plotly** — Graphiques interactifs

## Installation

```bash
# Cloner le projet
git clone https://github.com/TON_USERNAME/meteo-vols-beauvais.git
cd meteo-vols-beauvais

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

---

## Gestion de Projet

### Informations générales

| | |
|---|---|
| **Durée** | 14 jours |
| **Équipe** | 1 personne (solo) |
| **Rôle** | Chef de projet + Développeur |

### Planning prévisionnel

| Phase | Jours | Tâches |
|-------|-------|--------|
| **Cadrage** | J1-J2 | Comprendre les APIs, définir les objectifs, installer l'environnement |
| **Conception** | J2-J3 | Structurer le projet, créer les premiers fichiers, planifier les fonctionnalités |
| **Réalisation** | J3-J12 | Développement de l'application, tests, ajustements |
| **Clôture** | J13-J14 | Finalisation, documentation, préparation de la présentation |

### Risques identifiés

| Risque | Impact | Solution |
|--------|--------|----------|
| API Flightradar limitée/bloquée | Fort | Prévoir des données de démonstration en backup |
| Manque de temps | Moyen | Prioriser les fonctionnalités essentielles (MVP) |
| Bug technique bloquant | Moyen | Chercher de l'aide rapidement, ne pas rester bloqué |

### Kanban

Suivi des tâches sur GitHub Issues ou tableau personnel :
- **À faire** → Tâches planifiées
- **En cours** → Travail actuel
- **Terminé** → Tâches validées

---

## Auteur

- **Nom** : [Ton nom]
- **Formation** : Mineure Numérique B2
- **Date** : 2025

## Licence

Projet éducatif — Tous droits réservés.