import pandas as pd
import numpy as np

def calculate_climatology(df: pd.DataFrame, baseline_years: list) -> pd.DataFrame:
    """
    Computes daily climatology (historical averages) for temperature, precipitation,
    and sunshine duration over a specified range of baseline years.
    
    Returns a DataFrame indexed by day_of_year with:
      - temp_climatology
      - precip_climatology
      - sunshine_climatology
    """
    df_baseline = df[df['year'].isin(baseline_years)].copy()
    
    climatology = (
        df_baseline.groupby('day_of_year')
        .agg({
            'temperature_2m_mean': 'mean',
            'precipitation_sum': 'mean',
            'sunshine_duration': 'mean'
        })
        .reset_index()
        .rename(columns={
            'temperature_2m_mean': 'temp_climatology',
            'precipitation_sum': 'precip_climatology',
            'sunshine_duration': 'sunshine_climatology'
        })
    )
    return climatology

def calculate_rolling_anomalies(df: pd.DataFrame, target_year: int, climatology: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    Computes anomalies (deviations from climatology) for a target year using rolling averages.
    Smooths both target year daily values and daily climatology using a rolling window.
    
    Returns a DataFrame merged by day_of_year with columns:
      - temp_anomaly_roll
      - precip_anomaly_roll
      - And the raw rolling values
    """
    # Extract target year
    recent_df = df[df['year'] == target_year].copy()
    
    # Check if target year has data
    if recent_df.empty:
        return pd.DataFrame()
        
    # Calculate rolling averages for target year
    recent_df['temp_roll'] = recent_df['temperature_2m_mean'].rolling(window, center=True).mean()
    recent_df['precip_roll'] = recent_df['precipitation_sum'].rolling(window, center=True).mean()
    
    # Calculate rolling averages for daily climatology
    clim_copy = climatology.copy()
    clim_copy['temp_clim_roll'] = clim_copy['temp_climatology'].rolling(window, center=True).mean()
    clim_copy['precip_clim_roll'] = clim_copy['precip_climatology'].rolling(window, center=True).mean()
    
    # Merge
    comparison = recent_df.merge(
        clim_copy[['day_of_year', 'temp_clim_roll', 'precip_clim_roll']],
        on='day_of_year',
        how='left'
    )
    
    # Compute anomalies
    comparison['temp_anomaly_roll'] = comparison['temp_roll'] - comparison['temp_clim_roll']
    comparison['precip_anomaly_roll'] = comparison['precip_roll'] - comparison['precip_clim_roll']
    
    return comparison

def calculate_monthly_precipitation_comparison(df: pd.DataFrame, target_year: int, baseline_years: list) -> pd.DataFrame:
    """
    Compares the total monthly precipitation of a target year with the historical average monthly totals.
    
    Returns a DataFrame with columns:
      - month
      - precip_target (total precipitation in target year)
      - precip_climatology (average monthly total over baseline years)
      - difference_mm
      - percent_diff
    """
    df_baseline = df[df['year'].isin(baseline_years)].copy()
    df_target = df[df['year'] == target_year].copy()
    
    if df_target.empty:
        return pd.DataFrame()

    # Step 1: Monthly totals per year in baseline
    monthly_hist_totals = (
        df_baseline.groupby(['year', 'month'])['precipitation_sum']
        .sum()
        .reset_index()
    )
    
    # Step 2: Average monthly total across baseline years
    monthly_climatology = (
        monthly_hist_totals.groupby('month')['precipitation_sum']
        .mean()
        .reset_index()
        .rename(columns={'precipitation_sum': 'precip_climatology'})
    )
    
    # Step 3: Monthly totals for target year
    monthly_target = (
        df_target.groupby('month')['precipitation_sum']
        .sum()
        .reset_index()
        .rename(columns={'precipitation_sum': 'precip_target'})
    )
    
    # Step 4: Compare
    comparison = monthly_target.merge(monthly_climatology, on='month', how='left')
    comparison['difference_mm'] = comparison['precip_target'] - comparison['precip_climatology']
    comparison['percent_diff'] = (comparison['difference_mm'] / comparison['precip_climatology']) * 100
    
    return comparison

def calculate_hot_days(df: pd.DataFrame, threshold: float = 25.0) -> pd.DataFrame:
    """
    Flags days exceeding a temperature threshold and groups them by year and month.
    
    Returns a pivoted DataFrame with years as rows, months (1-12) as columns,
    and counts of hot days as values.
    """
    df = df.copy()
    
    # Create hot day flag
    df['hot_day'] = df['temperature_2m_max'] > threshold
    
    # Group and count
    hot_days_grouped = df.groupby(['year', 'month'])['hot_day'].sum().unstack(fill_value=0)
    
    # Ensure all months (1-12) are represented in the columns
    hot_days_grouped = hot_days_grouped.reindex(columns=range(1, 13), fill_value=0)
    
    return hot_days_grouped

def compare_years(df: pd.DataFrame, year1: int, year2: int) -> pd.DataFrame:
    """
    Compares monthly precipitation totals between two specific years.
    """
    df = df.copy()
    
    y1 = (
        df[df['year'] == year1]
        .groupby('month')['precipitation_sum']
        .sum().reset_index()
        .rename(columns={'precipitation_sum': f'precip_{year1}'})
    )
    
    y2 = (
        df[df['year'] == year2]
        .groupby('month')['precipitation_sum']
        .sum().reset_index()
        .rename(columns={'precipitation_sum': f'precip_{year2}'})
    )
    
    compare = y1.merge(y2, on='month', how='outer').sort_values('month')
    compare['difference_mm'] = compare[f'precip_{year2}'] - compare[f'precip_{year1}']
    compare['percent_diff'] = (compare['difference_mm'] / compare[f'precip_{year1}']) * 100
    
    return compare
