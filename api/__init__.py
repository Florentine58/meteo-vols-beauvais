# Module API pour le projet Météo & Vols Beauvais
# Importe les fonctions principales

from api.weather import (
    get_current_weather,
    get_hourly_forecast,
    get_7day_forecast,
    get_historical_weather,
    get_long_term_historical_weather,
    get_aviation_conditions_forecast,
    get_weather_code_description,
    BEAUVAIS_LAT,
    BEAUVAIS_LON
)

from api.flights import (
    get_flights_in_area,
    get_airport_info,
    get_arrivals,
    get_departures,
    get_airlines_stats,
    get_aircraft_stats,
    BVA_LAT,
    BVA_LON
)

# Modules qualité de l'air
try:
    from api.air_quality import (
        get_current_air_quality,
        get_air_quality_forecast,
        calculate_aviation_air_impact
    )
except ImportError:
    pass

# Module OpenSky V2 pour trajectoires historiques
try:
    from api.opensky_v2 import (
        get_current_flights_in_area,
        get_flight_track,
        get_beauvais_flights_with_tracks,
        get_historical_flights_by_day,
        get_airport_coords,
        estimate_flight_path,
        test_connection as test_opensky_connection,
        BVA_LAT as OPENSKY_BVA_LAT,
        BVA_LON as OPENSKY_BVA_LON,
        AIRPORT_ICAO
    )
except ImportError:
    pass

# Module AeroDataBox
try:
    from api.aerodatabox import (
        get_airport_departures,
        get_airport_arrivals,
        get_delay_statistics,
        test_connection as test_aerodatabox_connection
    )
except ImportError:
    pass