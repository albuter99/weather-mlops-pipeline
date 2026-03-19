import openmeteo_requests
import sqlite3
from datetime import date, timedelta
import requests_cache
from retry_requests import retry

DB_PATH = "weather.db"

LOCATIONS = [
    {"name": "Madrid", "lat": 40.4165, "lon": -3.7026},
    {"name": "Vienna", "lat": 48.2085, "lon": 16.3721},
    {"name": "Aalborg", "lat": 57.048, "lon": 9.9187},
]


def get_tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        location TEXT,
        date TEXT,
        temp_max REAL,
        temp_min REAL,
        precipitation REAL,
        wind REAL,
        daylight REAL,
        uv REAL,
        PRIMARY KEY (location, date)
    )
    """)

    conn.commit()
    return conn


def main():
    # Setup API client
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    conn = init_db()

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": [loc["lat"] for loc in LOCATIONS],
        "longitude": [loc["lon"] for loc in LOCATIONS],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "daylight_duration",
            "uv_index_max"
        ],
        "timezone": "Europe/Berlin",
        "forecast_days": 1,
    }

    responses = openmeteo.weather_api(url, params=params)

    forecast_date = get_tomorrow()

    for i, response in enumerate(responses):
        location = LOCATIONS[i]["name"]

        daily = response.Daily()

        temp_max = daily.Variables(0).ValuesAsNumpy()[0]
        temp_min = daily.Variables(1).ValuesAsNumpy()[0]
        precipitation = daily.Variables(2).ValuesAsNumpy()[0]
        wind = daily.Variables(3).ValuesAsNumpy()[0]
        daylight = daily.Variables(4).ValuesAsNumpy()[0]
        uv = daily.Variables(5).ValuesAsNumpy()[0]

        conn.execute("""
        INSERT OR REPLACE INTO weather VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            location,
            forecast_date,
            float(temp_max),
            float(temp_min),
            float(precipitation),
            float(wind),
            float(daylight),
            float(uv)
        ))

    conn.commit()
    conn.close()

    print("Weather data stored successfully")


if __name__ == "__main__":
    main()
