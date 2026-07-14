import pandas as pd
import numpy as np
import logging
import os

# Setup logging configuration
logging.basicConfig(
    filename='data_validation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def validate_weather_data(df: pd.DataFrame, city_name: str) -> pd.DataFrame:
    """
    Validates weather data columns, checks bounds, handles missing values (NaNs),
    and logs warnings for extreme anomalies. Returns a cleaned DataFrame.
    """
    df = df.copy()
    
    # 1. Check for required columns
    required_cols = [
        'date', 'temperature_2m_mean', 'temperature_2m_max', 'temperature_2m_min',
        'precipitation_sum', 'daylight_duration', 'sunshine_duration',
        'wind_speed_10m_max', 'wind_gusts_10m_max'
    ]
    for col in required_cols:
        if col not in df.columns:
            msg = f"City {city_name}: Missing required column {col} in fetched data."
            logging.error(msg)
            raise ValueError(msg)

    # Convert date to datetime if not already
    df['date'] = pd.to_datetime(df['date'])

    # 2. Check for missing values (NaNs) and impute them
    nan_counts = df[required_cols].isna().sum()
    total_nans = nan_counts.sum()
    if total_nans > 0:
        logging.warning(f"City {city_name}: Found {total_nans} missing values in variables. Attempting interpolation.")
        for col in required_cols:
            if col != 'date' and df[col].isna().any():
                missing_indices = df[df[col].isna()].index
                logging.info(f"City {city_name}: Interpolating missing values in column '{col}' at indices: {list(missing_indices)}")
                
                # Perform linear interpolation for short gaps
                df[col] = df[col].interpolate(method='linear', limit_direction='both')

    # 3. Value Bounds Checks
    # Temperature Bounds: -60°C to 50°C
    temp_cols = ['temperature_2m_mean', 'temperature_2m_max', 'temperature_2m_min']
    for col in temp_cols:
        outliers = df[(df[col] < -60.0) | (df[col] > 55.0)]
        if not outliers.empty:
            for idx, row in outliers.iterrows():
                logging.warning(
                    f"City {city_name}: Extreme temperature detected on {row['date'].strftime('%Y-%m-%d')} "
                    f"in '{col}': {row[col]}°C"
                )

    # Max temperature must be greater than or equal to min temperature
    temp_mismatch = df[df['temperature_2m_max'] < df['temperature_2m_min']]
    if not temp_mismatch.empty:
        for idx, row in temp_mismatch.iterrows():
            logging.warning(
                f"City {city_name}: Temperature inversion anomaly on {row['date'].strftime('%Y-%m-%d')}. "
                f"Max ({row['temperature_2m_max']}°C) < Min ({row['temperature_2m_min']}°C)."
            )

    # Precipitation bounds: precipitation must be >= 0
    negative_precip = df[df['precipitation_sum'] < 0]
    if not negative_precip.empty:
        for idx, row in negative_precip.iterrows():
            logging.warning(
                f"City {city_name}: Negative precipitation ({row['precipitation_sum']} mm) "
                f"detected on {row['date'].strftime('%Y-%m-%d')}. Clamping to 0."
            )
        df.loc[df['precipitation_sum'] < 0, 'precipitation_sum'] = 0.0

    # Wind speed bounds: wind speed must be >= 0
    for col in ['wind_speed_10m_max', 'wind_gusts_10m_max']:
        negative_wind = df[df[col] < 0]
        if not negative_wind.empty:
            for idx, row in negative_wind.iterrows():
                logging.warning(
                    f"City {city_name}: Negative wind speed in {col} ({row[col]} km/h) "
                    f"detected on {row['date'].strftime('%Y-%m-%d')}. Clamping to 0."
                )
            df.loc[df[col] < 0, col] = 0.0

    # Daylight and sunshine duration bounds (cannot exceed 24 hours / 86400 seconds)
    duration_cols = ['daylight_duration', 'sunshine_duration']
    for col in duration_cols:
        invalid_duration = df[df[col] > 86400.0]
        if not invalid_duration.empty:
            for idx, row in invalid_duration.iterrows():
                logging.warning(
                    f"City {city_name}: Invalid duration in {col} ({row[col]} s > 24h) "
                    f"detected on {row['date'].strftime('%Y-%m-%d')}. Clamping to 86400."
                )
            df.loc[df[col] > 86400.0, col] = 86400.0

    return df
