import pytest
import pandas as pd
import numpy as np
from src.statistics import (
    calculate_climatology,
    calculate_rolling_anomalies,
    calculate_monthly_precipitation_comparison,
    calculate_hot_days
)

@pytest.fixture
def sample_weather_data():
    """
    Generates a 3-year mock weather dataset for testing calculations.
    Years: 2020, 2021, 2022
    Each year has 365 days.
    """
    dates = pd.date_range(start="2020-01-01", end="2022-12-31", freq="D")
    df = pd.DataFrame({
        "date": dates,
        "temperature_2m_mean": np.linspace(10, 20, len(dates)), # predictable linear slope
        "temperature_2m_max": np.linspace(15, 25, len(dates)),
        "temperature_2m_min": np.linspace(5, 15, len(dates)),
        "precipitation_sum": np.ones(len(dates)) * 5.0, # constant precipitation (5mm/day)
        "sunshine_duration": np.ones(len(dates)) * 3600.0,
        "wind_speed_10m_max": np.ones(len(dates)) * 10.0,
        "wind_gusts_10m_max": np.ones(len(dates)) * 15.0
    })
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    return df

def test_calculate_climatology(sample_weather_data):
    baseline_years = [2020, 2021]
    climatology = calculate_climatology(sample_weather_data, baseline_years)
    
    # Climatology should contain 366 records (including leap year day of year 366)
    assert not climatology.empty
    assert 'temp_climatology' in climatology.columns
    assert 'precip_climatology' in climatology.columns
    
    # Since precip is constant 5mm/day, the baseline average for day_of_year must be 5.0
    assert np.allclose(climatology['precip_climatology'], 5.0)

def test_calculate_rolling_anomalies(sample_weather_data):
    baseline_years = [2020, 2021]
    climatology = calculate_climatology(sample_weather_data, baseline_years)
    
    # Target year = 2022
    anomalies = calculate_rolling_anomalies(sample_weather_data, 2022, climatology, window=7)
    
    assert not anomalies.empty
    assert 'temp_anomaly_roll' in anomalies.columns
    assert 'precip_anomaly_roll' in anomalies.columns
    
    # Since precip is constant, precip rolling anomaly should be ~0.0
    # Allow small discrepancies due to rolling boundaries at edges (which output NaN)
    valid_anom = anomalies['precip_anomaly_roll'].dropna()
    assert len(valid_anom) > 0
    assert np.allclose(valid_anom, 0.0, atol=1e-5)

def test_calculate_monthly_precipitation_comparison(sample_weather_data):
    baseline_years = [2020, 2021]
    target_year = 2022
    
    monthly_comp = calculate_monthly_precipitation_comparison(
        sample_weather_data, target_year, baseline_years
    )
    
    assert not monthly_comp.empty
    assert len(monthly_comp) == 12 # 12 months
    
    # Total monthly precipitation should be difference ~ 0 since it is constant
    # Wait, leap year in 2020 has 29 days in Feb, whereas 2021 and 2022 have 28 days.
    # So Feb baseline will be slightly higher: ((29*5) + (28*5)) / 2 = 142.5mm
    # Target Feb (2022) is 28 * 5 = 140mm
    # Difference should be -2.5mm
    feb_row = monthly_comp[monthly_comp['month'] == 2]
    assert np.allclose(feb_row['difference_mm'].values[0], -2.5, atol=0.1)

def test_calculate_hot_days(sample_weather_data):
    # Set threshold where only max temperatures near the end of 2022 exceed it
    threshold = 24.5
    hot_days = calculate_hot_days(sample_weather_data, threshold)
    
    assert not hot_days.empty
    # The output is pivoted by year (rows) and month (cols)
    assert 2020 in hot_days.index
    assert 2022 in hot_days.index
    assert len(hot_days.columns) == 12
    
    # Max temperature goes from 15 to 25 linearly.
    # The end of the series (late 2022) has temps > 24.5, so they must be counted.
    total_hot_days_2022 = hot_days.loc[2022].sum()
    assert total_hot_days_2022 > 0
