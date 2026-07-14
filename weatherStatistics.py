import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("historicalWeather.csv")

# Ensure datetime format
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Create derived columns
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_year'] = df['date'].dt.dayofyear


# =========================================================
# 1. DAILY CLIMATOLOGY (temp & precip)
# =========================================================
historical_df = df[df['year'] < 2025].copy()
recent_df     = df[df['year'] == 2025].copy()

climatology = (historical_df.groupby('day_of_year')
               .agg({'temperature_2m_mean': 'mean',
                     'precipitation_sum': 'mean'})
               .reset_index()
               .rename(columns={
                   'temperature_2m_mean': 'temp_climatology',
                   'precipitation_sum': 'precip_climatology'
               }))

comparison_df = recent_df.merge(climatology, on='day_of_year', how='left')


# ===== Plot temperature =====
plt.figure(figsize=(12,6))
plt.plot(comparison_df['day_of_year'], comparison_df['temperature_2m_mean'], label='2025')
plt.plot(comparison_df['day_of_year'], comparison_df['temp_climatology'], label='Historical Mean')
plt.legend(); plt.title("2025 Temperature vs Historical Daily Mean")
plt.xlabel("Day of Year"); plt.ylabel("°C"); plt.show()

# ===== Plot precipitation =====
plt.figure(figsize=(12,6))
plt.plot(comparison_df['day_of_year'], comparison_df['precipitation_sum'], label='2025')
plt.plot(comparison_df['day_of_year'], comparison_df['precip_climatology'], label='Historical Mean')
plt.legend(); plt.title("2025 Precip vs Historical Daily Mean")
plt.xlabel("Day of Year"); plt.ylabel("mm"); plt.show()


# =========================================================
# 2. 30-DAY ROLLING ANOMALIES
# =========================================================
climatology['temp_clim_roll30']   = climatology['temp_climatology'].rolling(30, center=True).mean()
climatology['precip_clim_roll30'] = climatology['precip_climatology'].rolling(30, center=True).mean()

recent_df['temp_roll30']   = recent_df['temperature_2m_mean'].rolling(30, center=True).mean()
recent_df['precip_roll30'] = recent_df['precipitation_sum'].rolling(30, center=True).mean()

comp_30 = recent_df.merge(climatology[['day_of_year','temp_clim_roll30','precip_clim_roll30']],
                          on='day_of_year', how='left')

comp_30['temp_anomaly_30']   = comp_30['temp_roll30'] - comp_30['temp_clim_roll30']
comp_30['precip_anomaly_30'] = comp_30['precip_roll30'] - comp_30['precip_clim_roll30']

# Plot anomalies
plt.figure(figsize=(12,6))
plt.plot(comp_30['day_of_year'], comp_30['temp_anomaly_30'])
plt.axhline(0, linestyle='--'); plt.title("2025 30-Day Temperature Anomaly")
plt.ylabel("°C"); plt.xlabel("Day of Year"); plt.show()

plt.figure(figsize=(12,6))
plt.plot(comp_30['day_of_year'], comp_30['precip_anomaly_30'])
plt.axhline(0, linestyle='--'); plt.title("2025 30-Day Precipitation Anomaly")
plt.ylabel("mm"); plt.xlabel("Day of Year"); plt.show()


# =========================================================
# 3. MONTHLY PRECIP — 🟩 THE FIX IS HERE
# =========================================================

# Step 1: monthly totals per year
monthly_hist_totals = (historical_df.groupby(['year','month'])['precipitation_sum']
                       .sum()
                       .reset_index())

# Step 2: average monthly total across all years
monthly_climatology = (monthly_hist_totals.groupby('month')['precipitation_sum']
                       .mean()
                       .reset_index()
                       .rename(columns={'precipitation_sum': 'precip_climatology'}))

# Step 3: total monthly precip for 2025
monthly_2025 = (recent_df.groupby('month')['precipitation_sum']
                .sum()
                .reset_index()
                .rename(columns={'precipitation_sum': 'precip_2025'}))

# Step 4: compare
compare = monthly_2025.merge(monthly_climatology, on='month', how='left')
compare['difference_mm'] = compare['precip_2025'] - compare['precip_climatology']
compare['percent_diff'] = (compare['difference_mm'] / compare['precip_climatology']) * 100


# ===== Plot =====
plt.figure(figsize=(10,5))
plt.bar(compare['month'], compare['percent_diff'])
plt.axhline(0, color='black', linestyle='--')
plt.title("2025 Monthly Precipitation % Difference vs Historical Normal")
plt.xlabel("Month"); plt.ylabel("% vs Normal")
plt.show()


# ===== Summary Printer =====
def precipitation_summary(month_number):
    row = compare[compare['month'] == month_number].iloc[0]
    if row['difference_mm'] > 0:
        return f"{month_number}: Wetter by {row['difference_mm']:.1f} mm ({row['percent_diff']:.1f}% above normal)"
    else:
        return f"{month_number}: Drier by {-row['difference_mm']:.1f} mm ({-row['percent_diff']:.1f}% below normal)"

for m in compare['month']:
    print(precipitation_summary(m))





import pandas as pd
import matplotlib.pyplot as plt

def compare_years(df, year1, year2, plot=True):
    """
    Compare monthly precipitation totals between two years.
    Returns a dataframe with monthly totals, differences, and percent change.

    year1 → baseline/reference year
    year2 → year being compared
    """

    # Ensure datetime + month columns exist
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    # Monthly totals for each year
    y1 = (df[df['year'] == year1]
          .groupby('month')['precipitation_sum']
          .sum().reset_index()
          .rename(columns={'precipitation_sum': f'precip_{year1}'}))

    y2 = (df[df['year'] == year2]
          .groupby('month')['precipitation_sum']
          .sum().reset_index()
          .rename(columns={'precipitation_sum': f'precip_{year2}'}))

    # Merge + compute anomaly
    compare = y1.merge(y2, on='month', how='outer').sort_values('month')
    compare['difference_mm'] = compare[f'precip_{year2}'] - compare[f'precip_{year1}']
    compare['percent_diff'] = (compare['difference_mm'] / compare[f'precip_{year1}']) * 100

    # Optional plot
    if plot:
        plt.figure(figsize=(10,5))
        plt.bar(compare['month'], compare['percent_diff'])
        plt.axhline(0, color='black', linestyle='--')
        plt.title(f"{year2} Precip vs {year1} — % Difference by Month")
        plt.xlabel("Month")
        plt.ylabel(f"% difference relative to {year1}")
        plt.show()

    return compare


result = compare_years(df, 2024, 2025)
print(result)



import pandas as pd

def compare_year_to_baseline(df, target_year, compare_years,
                             metrics=['temperature_2m_mean', 'precipitation_sum', 'sunshine_duration'],
                             monthly=True):

    # ensure datetime exists
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        raise ValueError("DataFrame must contain a 'date' column.")

    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    # split target year and baseline years
    target = df[df['year'] == target_year]
    baseline = df[df['year'].isin(compare_years)]

    if monthly:
        # monthly summaries
        target_monthly = target.groupby('month')[metrics].mean()
        baseline_monthly = baseline.groupby('month')[metrics].mean()
    else:
        # yearly summary
        target_monthly = target[metrics].mean().to_frame().T
        baseline_monthly = baseline[metrics].mean().to_frame().T

    # combine results
    comparison = target_monthly.copy()
    for m in metrics:
        comparison[f"{m}_baseline"] = baseline_monthly[m]
        comparison[f"{m}_diff"] = target_monthly[m] - baseline_monthly[m]
        comparison[f"{m}_pct_diff"] = (comparison[f"{m}_diff"] / baseline_monthly[m]) * 100

    return comparison.round(2)

def pretty_summary(result, target_year, baseline_years):
    print(f"\n=== Climate Comparison: {target_year} vs {min(baseline_years)}-{max(baseline_years)} ===\n")
    for month, row in result.iterrows():
        print(f"Month {month}:")
        for col in ['temperature_2m_mean', 'precipitation_sum', 'sunshine_duration']:
            diff = row[f"{col}_diff"]
            pct = row[f"{col}_pct_diff"]
            if diff > 0:
                change = f"↑ {diff:.2f} ({pct:.1f}%) above normal"
            else:
                change = f"↓ {abs(diff):.2f} ({abs(pct):.1f}%) below normal"
            print(f"  • {col.replace('_',' ').title()}: {change}")
        print("")


historicalYears = list(range(2000,2024))
result = compare_year_to_baseline(df, 2025, historicalYears)
pretty_summary(result, 2025, range(2000,2025))