import requests
import sqlite3
from datetime import date, timedelta

DB_PATH = "weather.db"

LOCATIONS = [
    {"name": "Madrid", "lat": 40.4168, "lon": -3.7038},
    {"name": "Vienna", "lat": 48.2082, "lon": 16.3738},
    {"name": "Aalborg", "lat": 57.0488, "lon": 9.9217},
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
        PRIMARY KEY (location, date)
    )
    """)

    conn.commit()
    return conn


def fetch_weather(lat, lon, forecast_date):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "start_date": forecast_date,
        "end_date": forecast_date,
        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()["daily"]

    return {
        "temp_max": data["temperature_2m_max"][0],
        "temp_min": data["temperature_2m_min"][0],
        "precipitation": data["precipitation_sum"][0],
        "wind": data["wind_speed_10m_max"][0]
    }


def main():
    conn = init_db()
    forecast_date = get_tomorrow()

    for loc in LOCATIONS:
        weather = fetch_weather(loc["lat"], loc["lon"], forecast_date)

        conn.execute("""
        INSERT OR REPLACE INTO weather VALUES (?, ?, ?, ?, ?, ?)
        """, (
            loc["name"],
            forecast_date,
            weather["temp_max"],
            weather["temp_min"],
            weather["precipitation"],
            weather["wind"]
        ))

    conn.commit()
    conn.close()

    print("Weather data stored successfully")


if __name__ == "__main__":
    main()
