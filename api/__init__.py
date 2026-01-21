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

# Modules optionnels (nécessitent configuration)
try:
    from api.air_quality import (
        get_current_air_quality,
        get_air_quality_forecast,
        calculate_aviation_air_impact
    )
except ImportError:
    pass

try:
    from api.opensky_v2 import (
        get_current_flights_in_area,
        get_flight_track,
        get_historical_flights,
        test_connection as test_opensky_connection
    )
except ImportError:
    pass
