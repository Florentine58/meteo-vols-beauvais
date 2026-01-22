# CLAUDE.md - AI Assistant Guide for meteo-vols-beauvais

## Project Overview

**BVA Monitor** is a real-time monitoring web application for Paris-Beauvais Airport (LFOB/BVA) that combines meteorological data, air traffic tracking, and environmental impact analysis. This is an academic project created for a "Mineure Numérique B2" program in 2025.

**Core Purpose:** Visualize correlations between weather conditions and aviation activity while tracking environmental impact (air quality, emissions) from airport operations.

**Author:** Meunier Florentine
**Duration:** 14-day sprint project
**Language:** French (UI, comments, documentation)

---

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13 | Backend language |
| **Streamlit** | ≥1.45.0 | Web UI framework (interactive dashboard) |
| **Folium** | ≥0.19.0 | Interactive mapping/cartography |
| **Plotly** | ≥6.0.0 | Interactive charts and visualizations |
| **Pandas** | ≥2.2.0 | Data manipulation and analysis |
| **Requests** | ≥2.32.0 | HTTP API calls |
| **FlightRadarAPI** | ≥1.4.0 | Flight tracking (educational use only) |
| **python-dotenv** | ≥1.0.0 | Environment variable management |
| **python-dateutil** | ≥2.9.0 | Date/time utilities |
| **streamlit-folium** | ≥0.24.0 | Streamlit-Folium integration |

---

## Codebase Structure

```
meteo-vols-beauvais/                    [~7,819 LOC, 610 KB]
│
├── app.py                               [805 lines] - Main dashboard entry point
├── test_api.py                          [98 lines] - API connection testing
├── requirements.txt                     - Python dependencies
├── README.md                            - Project documentation (French)
├── .gitignore                           - Git exclusions
│
├── .streamlit/
│   └── config.toml                      - Streamlit theme (dark aviation)
│
├── api/                                 [2,157 lines] - Backend API layer
│   ├── __init__.py                      [62 lines] - Module exports
│   ├── weather.py                       [605 lines] - OpenMeteo weather API
│   ├── flights.py                       [222 lines] - FlightRadar24 integration
│   ├── air_quality.py                   [311 lines] - Air quality (OpenMeteo)
│   ├── opensky_v2.py                    [657 lines] - Aircraft trajectories (v2)
│   ├── opensky.py                       [497 lines] - OpenSky (legacy)
│   └── aerodatabox.py                   [373 lines] - AeroDataBox (RapidAPI)
│
└── pages/                               [4,288 lines] - Streamlit pages
    ├── Carte.py                         [664 lines] - Real-time map
    ├── Meteo.py                         [479 lines] - Weather details
    ├── Vols.py                          [455 lines] - Flight traffic analysis
    ├── Statistiques.py                  [467 lines] - Stats & air quality
    ├── Historique.py                    [579 lines] - Historical data & forecasts
    ├── AnalyseHistorique.py             [787 lines] - Correlation analysis
    └── CarteHistorique.py               [856 lines] - Historical flight map
```

---

## Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Streamlit Multi-page App)                        │
│  ├─ app.py (Main dashboard)                                 │
│  └─ pages/ (7 specialized analysis pages)                   │
├─────────────────────────────────────────────────────────────┤
│  VISUALIZATION LAYER                                        │
│  ├─ Folium (interactive maps)                               │
│  ├─ Plotly (charts/graphs)                                  │
│  └─ Pandas (data tables)                                    │
├─────────────────────────────────────────────────────────────┤
│  BUSINESS LOGIC LAYER                                       │
│  ├─ Weather analysis (aviation scoring)                     │
│  ├─ Flight tracking & filtering                             │
│  └─ Air quality correlation                                 │
├─────────────────────────────────────────────────────────────┤
│  API INTEGRATION LAYER (/api/)                              │
│  ├─ OpenMeteo (weather + air quality)                       │
│  ├─ FlightRadar24 (real-time flights)                       │
│  ├─ OpenSky Network (trajectories)                          │
│  └─ AeroDataBox (FIDS data)                                 │
├─────────────────────────────────────────────────────────────┤
│  EXTERNAL SERVICES (REST APIs)                              │
│  ├─ api.open-meteo.com                                      │
│  ├─ opensky-network.org                                     │
│  ├─ RapidAPI/aerodatabox                                    │
│  └─ FlightRadar24 (unofficial)                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. User interacts with Streamlit UI (`app.py` or `pages/`)
2. Frontend calls API module functions from `/api/`
3. API modules call external REST APIs
4. Data is processed and formatted
5. Visualizations rendered with Plotly/Folium/Pandas

---

## Key Components

### API Layer (`/api/`)

#### 1. **weather.py** - OpenMeteo Weather API
- **Purpose:** Weather data retrieval and aviation condition scoring
- **Key Functions:**
  - Current weather, hourly forecasts, 7-day forecasts
  - Historical weather (30 days + archive to 1940)
  - Aviation conditions scoring algorithm
- **Coordinates:** Beauvais (49.4295°N, 2.0807°E)
- **API:** `api.open-meteo.com` (free, no key required)

#### 2. **air_quality.py** - Air Quality Monitoring
- **Purpose:** Air quality data and environmental impact
- **Pollutants:** PM2.5, PM10, NO₂, O₃, CO, SO₂
- **Index:** European AQI (Air Quality Index)
- **Features:** Aviation impact calculations, health risk scoring
- **API:** OpenMeteo Air Quality API (free)

#### 3. **flights.py** - Flight Tracking (FlightRadar24)
- **Purpose:** Real-time flight data around BVA
- **Radius:** 50km from Beauvais
- **Data:** Callsign, origin, destination, altitude, speed, heading
- **Airport:** ICAO: LFOB, IATA: BVA
- **API:** FlightRadarAPI (educational use only)
- **Note:** Unofficial API, use responsibly

#### 4. **opensky_v2.py** - Aircraft Trajectories (Preferred)
- **Purpose:** Historical flight tracks with waypoints
- **Features:**
  - Trajectory cropping (30km approach radius)
  - 24-hour lookback window
  - Authentication support
- **API:** OpenSky Network (requires account for full features)
- **Note:** This is the preferred version over `opensky.py`

#### 5. **opensky.py** - OpenSky Legacy
- **Status:** Legacy/redundant
- **Note:** Use `opensky_v2.py` for new development

#### 6. **aerodatabox.py** - AeroDataBox (RapidAPI)
- **Purpose:** Airport FIDS (Flight Information Display System)
- **Features:** Arrivals, departures, delay statistics
- **API:** RapidAPI/AeroDataBox (requires API key)
- **Status:** Optional enhancement

#### 7. **__init__.py** - Module Exports
- Central import point for all API functions
- Try/except blocks for optional modules (graceful degradation)

### Frontend Pages (`/pages/`)

Streamlit multipage application - each file is auto-discovered:

1. **Carte.py** - Real-time Interactive Map
   - Folium map centered on Beauvais
   - Live flight markers with position updates
   - Weather overlay and air quality visualization

2. **Meteo.py** - Weather Dashboard
   - Current conditions display
   - 7-day forecast with weather icons
   - Hourly forecast charts
   - Aviation impact indicators

3. **Vols.py** - Flight Traffic Analysis
   - Live flight list with real-time updates
   - Filter: BVA arrivals/departures vs transit
   - Airline and aircraft statistics

4. **Statistiques.py** - Statistics & Analysis
   - Traffic distribution by airline/aircraft
   - Air quality metrics and trends
   - Aviation impact scores

5. **Historique.py** - Historical Data & Forecasts
   - 7-day detailed forecast with alerts
   - Historical weather (up to 1940)
   - Long-term trends analysis

6. **AnalyseHistorique.py** - Correlation Analysis
   - Weather vs aviation activity correlation
   - Multi-year trend analysis
   - Statistical visualizations

7. **CarteHistorique.py** - Historical Trajectories Map
   - Flight paths from OpenSky historical data
   - Trajectory visualization with waypoints
   - Weather overlay on historical dates

### Main Application (app.py)

- **Purpose:** Main dashboard and entry point
- **Features:**
  - Real-time metrics: weather, flights, air quality
  - Aviation conditions score display
  - Professional CSS styling (dark aviation theme)
  - Status indicators and badges
- **Configuration:**
  - Page title, icon, layout
  - Custom CSS for professional appearance

---

## Development Workflows

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Florentine58/meteo-vols-beauvais.git
cd meteo-vols-beauvais

# Install dependencies
pip install -r requirements.txt

# Optional: Configure API keys
# Create .env file with:
# OPENSKY_USERNAME=your_username
# OPENSKY_PASSWORD=your_password
# RAPIDAPI_KEY=your_key

# Test API connections (optional but recommended)
python test_api.py

# Run application
streamlit run app.py
```

### Running the Application

```bash
# Standard run (opens browser automatically)
streamlit run app.py

# Headless mode (server only)
streamlit run app.py --server.headless=true

# Custom port
streamlit run app.py --server.port=8502
```

### Testing API Connections

```bash
# Validate all API integrations
python test_api.py
```

**test_api.py checks:**
- OpenSky Network connectivity and authentication
- AeroDataBox API access
- OpenMeteo weather data retrieval
- FlightRadar24 flight data access

---

## Key Conventions & Patterns

### Code Style

1. **Language:** French for UI strings, comments, and documentation
2. **Naming:**
   - Functions: `snake_case`
   - Variables: `snake_case`
   - Constants: `UPPER_CASE` (e.g., `BEAUVAIS_LAT`, `BEAUVAIS_LON`)
3. **Comments:** French, descriptive, explain business logic
4. **Docstrings:** Minimal (improvement opportunity)

### Design Patterns

1. **Functional Programming:** Functions return data, minimal state
2. **Separation of Concerns:** API layer completely isolated from UI
3. **Configuration Centralization:** Constants at module level
4. **Error Handling:** Try/except with graceful degradation
5. **Caching:** Streamlit `@st.cache_data` for performance optimization

### API Integration Patterns

```python
# Standard pattern for API calls in /api/ modules

import requests
from typing import Optional, Dict, List

BEAUVAIS_LAT = 49.4295
BEAUVAIS_LON = 2.0807

def get_data(params: Optional[Dict] = None) -> Optional[Dict]:
    """Retrieve data from external API."""
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur API: {e}")
        return None
```

### Streamlit Page Pattern

```python
# Standard pattern for pages/*.py files

import streamlit as st
from api import weather, flights  # Import from api module

st.set_page_config(
    page_title="Page Title",
    page_icon="🛩️",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
    <style>
    /* Dark aviation theme */
    /* Colors: #00D4FF (cyan), #0E1117 (background) */
    </style>
""", unsafe_allow_html=True)

# Main content
st.title("Page Title")

# Data retrieval with error handling
data = weather.get_current_weather()
if data:
    # Display data
    st.metric("Temperature", f"{data['temp']}°C")
else:
    st.error("Erreur de chargement des données")
```

---

## Environment Configuration

### Required Environment Variables

None required for basic operation (all APIs are free tier without keys).

### Optional Environment Variables (.env)

```bash
# OpenSky Network (for trajectory data)
OPENSKY_USERNAME=your_username
OPENSKY_PASSWORD=your_password

# AeroDataBox (for FIDS data)
RAPIDAPI_KEY=your_rapidapi_key
```

### Streamlit Configuration (.streamlit/config.toml)

```toml
[theme]
primaryColor = "#00D4FF"        # Cyan
backgroundColor = "#0E1117"      # Near black
secondaryBackgroundColor = "#1A1F2E"
textColor = "#FAFAFA"
font = "sans serif"

[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false
```

---

## External APIs

### 1. OpenMeteo (Weather + Air Quality)

- **URL:** `https://api.open-meteo.com`
- **Authentication:** None required
- **Rate Limits:** Free tier, generous limits
- **Endpoints Used:**
  - `/v1/forecast` - Weather forecasts
  - `/v1/air-quality` - Air quality data
  - `/v1/archive` - Historical weather
- **Documentation:** https://open-meteo.com/

### 2. FlightRadar24

- **Library:** `FlightRadarAPI`
- **Authentication:** None (educational use)
- **Limitations:** Unofficial API, use responsibly
- **Usage:** Real-time flight tracking within radius
- **Note:** Not for commercial use

### 3. OpenSky Network

- **URL:** `https://opensky-network.org/api`
- **Authentication:** Optional (username/password)
- **Free Tier:** Limited historical data
- **Authenticated:** Full trajectory access
- **Endpoints Used:**
  - `/tracks/all` - Flight trajectories
  - `/states/all` - Current flight states
- **Documentation:** https://openskynetwork.github.io/opensky-api/

### 4. AeroDataBox (RapidAPI)

- **URL:** RapidAPI hub
- **Authentication:** API key required
- **Status:** Optional enhancement
- **Usage:** Airport FIDS data (arrivals/departures)
- **Note:** Requires paid RapidAPI subscription for production

---

## Important Constants

### Geographic Coordinates

```python
# Beauvais Airport (Paris-Beauvais)
BEAUVAIS_LAT = 49.4295
BEAUVAIS_LON = 2.0807

# ICAO & IATA Codes
AIRPORT_ICAO = "LFOB"
AIRPORT_IATA = "BVA"

# Search radius for flights
FLIGHT_RADIUS_KM = 50
TRAJECTORY_CROP_RADIUS_KM = 30
```

### API Timeouts

```python
API_TIMEOUT = 10  # seconds
```

---

## Common Development Tasks

### Adding a New API Module

1. Create new file in `/api/` directory (e.g., `api/new_source.py`)
2. Implement functions following the functional pattern
3. Add try/except for error handling
4. Export functions in `api/__init__.py`:

```python
# api/__init__.py
try:
    from .new_source import get_new_data
except ImportError:
    get_new_data = None
```

5. Use in pages with null checks:

```python
from api import get_new_data

if get_new_data:
    data = get_new_data()
```

### Adding a New Page

1. Create file in `/pages/` with numeric prefix (e.g., `8_NewPage.py`)
2. Set page config with title and icon
3. Add custom CSS matching aviation theme
4. Import necessary API functions
5. Implement data visualization
6. Page will auto-appear in sidebar

### Modifying the Theme

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#NEW_COLOR"
```

Colors must maintain good contrast with dark background.

### Adding Dependencies

1. Install package: `pip install package-name`
2. Add to `requirements.txt` with version:

```
package-name>=X.Y.Z
```

3. Test with `pip install -r requirements.txt`

---

## Testing & Validation

### Manual Testing

```bash
# Test all API connections
python test_api.py

# Expected output:
# ✅ OpenSky: Connected
# ✅ AeroDataBox: Connected (if key provided)
# ✅ OpenMeteo: Data retrieved
# ✅ FlightRadar24: Flights found
```

### Testing Individual APIs

```python
# Test weather API
from api.weather import get_current_weather
data = get_current_weather()
print(data)

# Test flights API
from api.flights import get_flights_around_beauvais
flights = get_flights_around_beauvais()
print(f"Found {len(flights)} flights")
```

### No Automated Tests

**Current State:** No pytest, unittest, or automated test suite.

**Recommendation for Contributors:**
- Add unit tests for API modules
- Mock external API calls
- Test data processing functions
- Validate data transformations

---

## Performance Considerations

### Caching Strategy

Use Streamlit's caching to avoid redundant API calls:

```python
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_weather_cached():
    return get_current_weather()
```

**Recommended TTL (Time To Live):**
- Real-time flight data: 30-60 seconds
- Weather data: 5-10 minutes
- Historical data: 1 hour or more
- Air quality: 10-15 minutes

### API Rate Limiting

- **OpenMeteo:** Generous free tier, no explicit limits
- **FlightRadar24:** Use responsibly, unofficial API
- **OpenSky:**
  - Anonymous: Limited requests
  - Authenticated: Higher limits
- **AeroDataBox:** Based on RapidAPI plan

### Optimization Tips

1. **Batch API calls** when possible
2. **Cache expensive computations** with `@st.cache_data`
3. **Lazy load** data only when page is active
4. **Minimize map redraws** (Folium can be slow)
5. **Use Pandas efficiently** for large datasets

---

## Known Issues & Limitations

### Current Limitations

1. **No Authentication UI:** API keys must be manually added to `.env`
2. **FlightRadar24 Unofficial:** May break if API changes
3. **No Error Logging:** Errors printed to console, not logged
4. **Limited Docstrings:** Code documentation could be improved
5. **No Type Hints:** Missing type annotations for better IDE support
6. **No CI/CD:** No automated testing/deployment pipeline
7. **French Only:** No internationalization support

### Browser Compatibility

- **Tested:** Chrome, Firefox, Edge (modern versions)
- **Known Issues:** Safari may have Folium rendering quirks
- **Recommendation:** Use Chromium-based browsers for best experience

---

## Security Considerations

### API Keys

- **Never commit** `.env` files to Git (already in `.gitignore`)
- **Use environment variables** for sensitive data
- **Rotate keys** if accidentally exposed

### External APIs

- **FlightRadar24:** Unofficial API, educational use only
- **OpenSky:** Respect terms of service
- **AeroDataBox:** Commercial use requires paid plan

### Data Privacy

- **No user data collected** by default
- **Streamlit analytics disabled** (`gatherUsageStats = false`)
- **No cookies** or tracking

---

## Troubleshooting

### Common Issues

#### 1. API Connection Failures

```python
# Symptom: "Erreur API" messages
# Solution: Check internet connection, verify API status
python test_api.py
```

#### 2. Streamlit Port Already in Use

```bash
# Error: Port 8501 already in use
# Solution: Use different port
streamlit run app.py --server.port=8502
```

#### 3. Missing Dependencies

```bash
# Error: ModuleNotFoundError
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

#### 4. OpenSky Authentication Failed

```bash
# Symptom: 401 Unauthorized
# Solution: Check credentials in .env
OPENSKY_USERNAME=your_username
OPENSKY_PASSWORD=your_password
```

#### 5. Folium Map Not Rendering

```python
# Symptom: Blank map area
# Solution: Check Folium version, clear Streamlit cache
pip install --upgrade folium streamlit-folium
# In app: Clear cache via "C" hotkey or Settings menu
```

---

## Git Workflow

### Current Branch Strategy

- **Main/Production:** `main` branch (not explicitly shown)
- **Development:** Feature branches with `claude/` prefix
- **Current:** `claude/claude-md-mkpirkzopvit5yyr-Sjkxz`

### Commit Conventions

**Observed Pattern:** Simple test commits ("test23", "TEST 22")

**Recommended for Production:**
```bash
# Semantic commit messages
git commit -m "feat: add new air quality indicator"
git commit -m "fix: correct temperature conversion"
git commit -m "docs: update README with setup instructions"
git commit -m "refactor: optimize flight data processing"
```

### Pushing Changes

```bash
# Standard push to feature branch
git add .
git commit -m "descriptive message"
git push -u origin claude/branch-name

# Note: Branch must start with 'claude/' per requirements
```

---

## Development Best Practices

### When Adding Features

1. **Read existing code first** - Understand current patterns
2. **Follow French naming** - Maintain language consistency
3. **Match existing style** - Use similar structure to existing pages
4. **Test API calls** - Verify with `test_api.py`
5. **Add error handling** - Always use try/except for external calls
6. **Consider caching** - Use `@st.cache_data` for expensive operations
7. **Update CLAUDE.md** - Document significant changes

### When Fixing Bugs

1. **Reproduce issue** - Verify bug exists
2. **Check API status** - External services may be down
3. **Review recent commits** - Identify potential causes
4. **Test fix locally** - Run `streamlit run app.py`
5. **Verify related functionality** - Ensure no regressions

### Code Review Checklist

- [ ] Code follows existing patterns
- [ ] French naming maintained
- [ ] Error handling implemented
- [ ] No hardcoded credentials
- [ ] Dependencies added to `requirements.txt`
- [ ] Caching used appropriately
- [ ] No console errors in browser
- [ ] Works in Chrome/Firefox

---

## File-Specific Guidance

### app.py (Main Dashboard)

- **Purpose:** Entry point, overview dashboard
- **Key Features:** Real-time metrics, aviation score
- **Style:** Professional CSS with aviation theme
- **Pattern:** Display-only, no complex logic
- **Updates:** Modify for new metrics or dashboard layout

### api/*.py (API Modules)

- **Purpose:** External API integration
- **Pattern:** Functional, return data or None
- **Error Handling:** Try/except with graceful failure
- **Constants:** Define at module level
- **Caching:** Not here - implement in pages

### pages/*.py (UI Pages)

- **Purpose:** Specific analysis views
- **Pattern:** Import from api, display with Streamlit
- **Caching:** Use `@st.cache_data` for API calls
- **Style:** Include custom CSS matching theme
- **Layout:** `layout="wide"` for map/chart pages

### test_api.py (Testing)

- **Purpose:** Validate API connectivity
- **Usage:** Run before deployment or after API changes
- **Updates:** Add tests for new API modules

---

## Resources & References

### Official Documentation

- **Streamlit:** https://docs.streamlit.io/
- **Folium:** https://python-visualization.github.io/folium/
- **Plotly:** https://plotly.com/python/
- **Pandas:** https://pandas.pydata.org/docs/
- **OpenMeteo:** https://open-meteo.com/en/docs
- **OpenSky API:** https://openskynetwork.github.io/opensky-api/

### Useful Links

- **FlightRadar24 API:** https://github.com/JeanExtreme002/FlightRadarAPI
- **Streamlit Theming:** https://docs.streamlit.io/library/advanced-features/theming
- **Python Dotenv:** https://github.com/theskumar/python-dotenv

### Academic Context

- **Formation:** Mineure Numérique B2
- **Institution:** Not specified in codebase
- **Timeline:** 14-day project (2025)
- **License:** Educational - All rights reserved

---

## Contact & Support

### Project Maintainer

- **Author:** Meunier Florentine
- **GitHub:** Florentine58 (inferred from context)

### Getting Help

1. **Check this CLAUDE.md** for guidance
2. **Review README.md** for setup instructions
3. **Run test_api.py** to diagnose API issues
4. **Check Streamlit logs** in terminal for errors

---

## Quick Reference Commands

```bash
# Setup
pip install -r requirements.txt

# Run application
streamlit run app.py

# Test APIs
python test_api.py

# Git workflow
git add .
git commit -m "message"
git push -u origin claude/branch-name

# Environment variables
# Create .env file:
OPENSKY_USERNAME=xxx
OPENSKY_PASSWORD=xxx
RAPIDAPI_KEY=xxx
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-22 | 1.0 | Initial CLAUDE.md creation with comprehensive documentation |

---

**Last Updated:** 2026-01-22
**Document Purpose:** AI Assistant onboarding and development reference
**Maintained By:** AI assistants working on this codebase

---

## Notes for AI Assistants

### When Working on This Codebase

1. **Preserve French language** - All UI strings, comments in French
2. **Maintain aviation theme** - Dark colors (#00D4FF cyan, #0E1117 background)
3. **Follow functional patterns** - API layer returns data, pages display
4. **Always handle API failures** - External services may be unavailable
5. **Test before committing** - Run application locally
6. **Update this file** - Keep CLAUDE.md current with changes
7. **Respect API limits** - Be mindful of free tier restrictions
8. **Educational context** - This is an academic project

### Code Modification Guidelines

- **Enhance, don't replace** - Build on existing functionality
- **Match existing style** - Consistency over personal preference
- **Explain changes** - Clear commit messages in French or English
- **Consider performance** - Cache appropriately, minimize API calls
- **Think mobile** - Some users may access on tablets/phones

### Common AI Assistant Tasks

1. **Adding new data sources** → Create module in `/api/`, export in `__init__.py`
2. **New visualizations** → Add page in `/pages/`, use Plotly or Folium
3. **UI improvements** → Modify CSS in page files, maintain theme
4. **Bug fixes** → Test with `test_api.py`, verify in browser
5. **Performance optimization** → Add caching, optimize data processing
6. **Documentation** → Update README.md and this CLAUDE.md

---

*End of CLAUDE.md - Comprehensive AI Assistant Guide*
