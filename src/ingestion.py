import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
from src.validation import validate_weather_data

# Set up logger for ingestion process
logger = logging.getLogger('ingestion')
logger.setLevel(logging.INFO)
# Prevent duplicate handlers if the file is imported multiple times
if not logger.handlers:
    fh = logging.FileHandler('ingestion.log')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    
    # Also log to stdout
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(sh)

# List of 5 target cities with coordinates and local timezones
CITIES = {
    "Victoria": {
        "latitude": 48.4359,
        "longitude": -123.3516,
        "timezone": "America/Vancouver"
    },
    "Vancouver": {
        "latitude": 49.2827,
        "longitude": -123.1207,
        "timezone": "America/Vancouver"
    },
    "Calgary": {
        "latitude": 51.0447,
        "longitude": -114.0719,
        "timezone": "America/Edmonton"
    },
    "Toronto": {
        "latitude": 43.6532,
        "longitude": -79.3832,
        "timezone": "America/Toronto"
    },
    "Halifax": {
        "latitude": 44.6488,
        "longitude": -63.5752,
        "timezone": "America/Halifax"
    },
    "Penticton": {
        "latitude": 49.4991,
        "longitude": -119.5937,
        "timezone": "America/Vancouver"
    }
}

# Open-Meteo Archive API endpoint
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo_client = openmeteo_requests.Client(session=retry_session)

def fetch_from_api(city_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Queries the Open-Meteo API for historical daily weather data of a specific city.
    Returns a pandas DataFrame of the variables.
    """
    city_info = CITIES[city_name]
    
    logger.info(f"Querying Open-Meteo API for {city_name} from {start_date} to {end_date}")
    
    params = {
        "latitude": city_info["latitude"],
        "longitude": city_info["longitude"],
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "daylight_duration", "sunshine_duration",
            "wind_speed_10m_max", "wind_gusts_10m_max"
        ],
        "timezone": city_info["timezone"]
    }
    
    responses = openmeteo_client.weather_api(ARCHIVE_API_URL, params=params)
    if not responses:
        raise ValueError(f"No response received from Open-Meteo API for {city_name}")
        
    response = responses[0]
    daily = response.Daily()
    
    # Extract values
    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )
    }
    
    # Variable mappings in requested order
    daily_data["temperature_2m_mean"] = daily.Variables(0).ValuesAsNumpy()
    daily_data["temperature_2m_max"] = daily.Variables(1).ValuesAsNumpy()
    daily_data["temperature_2m_min"] = daily.Variables(2).ValuesAsNumpy()
    daily_data["precipitation_sum"] = daily.Variables(3).ValuesAsNumpy()
    daily_data["daylight_duration"] = daily.Variables(4).ValuesAsNumpy()
    daily_data["sunshine_duration"] = daily.Variables(5).ValuesAsNumpy()
    daily_data["wind_speed_10m_max"] = daily.Variables(6).ValuesAsNumpy()
    daily_data["wind_gusts_10m_max"] = daily.Variables(7).ValuesAsNumpy()
    
    df = pd.DataFrame(data=daily_data)
    
    # Normalize date to keep only YYYY-MM-DD
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    
    # Add year, month, and day of year
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    
    return df

def ingest_city_data(city_name: str, force_rebuild: bool = False):
    """
    Performs ingestion for a single city. Either fetches bulk data (1980-yesterday)
    or delta updates (latest_date + 1 to yesterday) and writes to data/{city_name}.csv.
    """
    if city_name not in CITIES:
        raise ValueError(f"City '{city_name}' is not in the supported CITIES list.")
        
    os.makedirs("data", exist_ok=True)
    csv_path = f"data/{city_name.lower()}.csv"
    
    # Historical archive data is updated daily with a lag of ~2 days
    yesterday_date = (datetime.now() - timedelta(days=2))
    yesterday_str = yesterday_date.strftime("%Y-%m-%d")
    
    df_existing = None
    if os.path.exists(csv_path) and not force_rebuild:
        try:
            df_existing = pd.read_csv(csv_path)
            df_existing['date'] = pd.to_datetime(df_existing['date'])
        except Exception as e:
            logger.error(f"Error reading existing CSV for {city_name}: {e}. Forcing rebuild.")
            df_existing = None
            
    if df_existing is not None and not df_existing.empty:
        # Check latest date
        latest_date = df_existing['date'].max()
        logger.info(f"{city_name} has existing data up to {latest_date.strftime('%Y-%m-%d')}")
        
        # Delta date calculations
        start_date_delta = latest_date + timedelta(days=1)
        
        if start_date_delta > yesterday_date:
            logger.info(f"{city_name} is already up to date (Latest: {latest_date.strftime('%Y-%m-%d')}, Target: {yesterday_str}).")
            return
            
        start_date_str = start_date_delta.strftime("%Y-%m-%d")
        
        try:
            df_new = fetch_from_api(city_name, start_date_str, yesterday_str)
            if not df_new.empty:
                # Validate the new portion
                df_new_validated = validate_weather_data(df_new, city_name)
                
                # Combine
                df_combined = pd.concat([df_existing, df_new_validated], ignore_index=True)
                df_combined = df_combined.sort_values('date').drop_duplicates(subset=['date'])
                
                df_combined.to_csv(csv_path, index=False)
                logger.info(f"Successfully appended {len(df_new_validated)} new days of data to {csv_path}")
            else:
                logger.warning(f"No new data returned for {city_name} between {start_date_str} and {yesterday_str}")
        except Exception as e:
            logger.error(f"Failed to ingest delta data for {city_name}: {e}")
            raise
    else:
        # Bulk Ingestion
        start_date_str = "1980-01-01"
        logger.info(f"Performing bulk ingestion for {city_name} from {start_date_str} to {yesterday_str}")
        
        try:
            df_bulk = fetch_from_api(city_name, start_date_str, yesterday_str)
            df_validated = validate_weather_data(df_bulk, city_name)
            df_validated.to_csv(csv_path, index=False)
            logger.info(f"Successfully wrote bulk weather data ({len(df_validated)} rows) to {csv_path}")
        except Exception as e:
            logger.error(f"Failed bulk ingestion for {city_name}: {e}")
            raise

def ingest_all_cities(force_rebuild: bool = False):
    """
    Iterates through all supported cities and performs ingestion.
    Captures failures per-city and continues.
    """
    import time
    logger.info("Starting weather data ingestion for all cities...")
    success_count = 0
    failure_count = 0
    
    cities_list = list(CITIES.keys())
    for idx, city in enumerate(cities_list):
        try:
            # Check if CSV exists and is up to date (this avoids sleep if no API call is made)
            csv_path = f"data/{city.lower()}.csv"
            already_up_to_date = False
            if os.path.exists(csv_path) and not force_rebuild:
                try:
                    df_existing = pd.read_csv(csv_path)
                    if not df_existing.empty:
                        latest_date = pd.to_datetime(df_existing['date']).max()
                        yesterday_date = (datetime.now() - timedelta(days=2))
                        if latest_date + timedelta(days=1) > yesterday_date:
                            already_up_to_date = True
                except Exception:
                    pass
            
            ingest_city_data(city, force_rebuild=force_rebuild)
            success_count += 1
            
            # Sleep only if we actually hit the API and this is not the last city
            if not already_up_to_date and idx < len(cities_list) - 1:
                logger.info("Sleeping for 30 seconds to respect API rate limits...")
                time.sleep(30)
        except Exception as e:
            logger.error(f"Ingestion failed for city: {city}. Details: {e}")
            failure_count += 1
            if idx < len(cities_list) - 1:
                logger.info("Sleeping for 30 seconds after failure to respect API rate limits...")
                time.sleep(30)
            
    logger.info(f"Ingestion completed. Success: {success_count}, Failures: {failure_count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest weather data for Victoria, Vancouver, Calgary, Toronto, and Halifax.")
    parser.add_argument("--force", action="store_true", help="Force database rebuild from 1980")
    args = parser.parse_args()
    
    ingest_all_cities(force_rebuild=args.force)
