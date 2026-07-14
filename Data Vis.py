import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

## This data is 2020-2024
df_filtered = pd.read_csv("weather_data.csv")

df_filtered["date"] = pd.to_datetime(df_filtered["date"])
print(df_filtered["date"].dtype)

# Extract year and month
df_filtered['year'] = df_filtered['date'].dt.year
df_filtered['month'] = df_filtered['date'].dt.month

# Define temperature threshold
threshold = 25  # e.g. degrees Celsius

# Create a flag for days above threshold
df_filtered['hot_day'] = df_filtered['temperature_2m_max'] > threshold

# Group and count hot days per year/month
hot_days = df_filtered.groupby(['year', 'month'])['hot_day'].sum().unstack(fill_value=0)

# Reindex to ensure all months appear (1 to 12)
hot_days = hot_days.reindex(columns=range(1, 13), fill_value=0)

# Plot
plt.figure(figsize=(12, 6))
sns.heatmap(hot_days, annot=True, fmt=".0f", cmap="YlOrRd", cbar_kws={'label': 'Days > {}°C'.format(threshold)})
plt.title(f"Number of Hot Days Per Month (>{threshold}°C)")
plt.xlabel("Month")
plt.ylabel("Year")
plt.xticks(ticks=[i + 0.5 for i in range(12)], labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=45)
plt.tight_layout()
plt.show()


## Now want to plot average precipitation for each



## calculating historical averages for temp and precipitation

df = pd.read_csv("historicalWeather.csv")
df['date'] = pd.to_datetime(df['date'], errors='coerce')

historical_df = df[df['year'] < 2025]   # exclude most recent year
recent_df = df[df['year'] == 2025]      # year to compare

## mean for each day of year

## group by day of year then take the mean (output is mean of specific day across all years for each day)
climatology = historical_df.groupby('day_of_year').agg({
    'temperature_2m_mean': 'mean',
    'precipitation_sum': 'mean'
}).reset_index()

## rename and reformat dataset
climatology = climatology.rename(columns={
    'temperature_2m_mean': 'temp_climatology',
    'precipitation_sum': 'precip_climatology'
})

## merging the data frame of averages to the current year
comparison_df = recent_df.merge(climatology, on='day_of_year', how='left')


plt.figure(figsize=(12,6))
plt.plot(comparison_df['day_of_year'], comparison_df['temperature_2m_mean'], label='2025 Temperature')
plt.plot(comparison_df['day_of_year'], comparison_df['temp_climatology'], label='Historical Average (1980-2024)')
plt.legend()
plt.xlabel("Day of Year")
plt.ylabel("Temperature (°C)")
plt.title("2025 Temperature vs Historical Daily Average")
plt.show()


plt.figure(figsize=(12,6))
plt.plot(comparison_df['day_of_year'], comparison_df['precipitation_sum'], label='2025 Precipitation')
plt.plot(comparison_df['day_of_year'], comparison_df['precip_climatology'], label='Historical Average (1980-2024)')
plt.legend()
plt.xlabel("Day of Year")
plt.ylabel("Precipitation (mm)")
plt.title("2025 precipitation vs Historical Daily Average")
plt.show()




## calcualting rolling averages (30 days)
climatology['temp_clim_roll30'] = climatology['temp_climatology'].rolling(30, center=True).mean()
climatology['precip_clim_roll30'] = climatology['precip_climatology'].rolling(30, center=True).mean()

recent_df = df[df['year'] == 2025].copy()

recent_df['temp_roll30'] = recent_df['temperature_2m_mean'].rolling(30, center=True).mean()
recent_df['precip_roll30'] = recent_df['precipitation_sum'].rolling(30, center=True).mean()

comp_30 = recent_df.merge(climatology[['day_of_year','temp_clim_roll30','precip_clim_roll30']],
                          on='day_of_year', how='left')

comp_30['temp_anomaly_30']  = comp_30['temp_roll30']  - comp_30['temp_clim_roll30']
comp_30['precip_anomaly_30'] = comp_30['precip_roll30'] - comp_30['precip_clim_roll30']


plt.figure(figsize=(12,6))
plt.plot(comp_30['day_of_year'], comp_30['temp_anomaly_30'])
plt.axhline(0, linestyle='--')
plt.title("2025 — 30-Day Temperature Anomaly vs Historical Norm")
plt.xlabel("Day of Year")
plt.ylabel("Temperature Anomaly (°C)")
plt.show()

plt.figure(figsize=(12,6))
plt.plot(comp_30['day_of_year'], comp_30['precip_anomaly_30'])
plt.axhline(0, linestyle='--')
plt.title("2025 — 30-Day Precipitation Anomaly vs Historical Norm")
plt.xlabel("Day of Year")
plt.ylabel("Precipitation Anomaly (mm)")
plt.show()


## Is this month wetter or drier than normal, and if so by how much

historical = df[df['year'] < 2025].copy()

historical['month'] = historical['date'].dt.month
monthly_climatology = (historical.groupby('month')['precipitation_sum']
                       .mean()
                       .reset_index()
                       .rename(columns={'precipitation_sum': 'precip_climatology'}))


recent = df[df['year'] == 2025].copy()
recent['month'] = recent['date'].dt.month

monthly_2025 = (recent.groupby('month')['precipitation_sum']
                .sum()
                .reset_index()
                .rename(columns={'precipitation_sum': 'precip_2025'}))

compare = monthly_2025.merge(monthly_climatology, on='month', how='left')

compare['difference_mm'] = compare['precip_2025'] - compare['precip_climatology']
compare['percent_diff'] = (compare['difference_mm'] / compare['precip_climatology']) * 100


plt.figure(figsize=(10,5))
plt.bar(compare['month'], compare['percent_diff'])
plt.axhline(0, color='black', linestyle='--')
plt.title("2025 Precipitation vs Historical Monthly Average")
plt.xlabel("Month")
plt.ylabel("% Difference from Normal")
plt.show()


def precipitation_summary(month_number):
    row = compare[compare['month'] == month_number].iloc[0]
    if row['difference_mm'] > 0:
        return (f"{month_number}: Wetter than normal by {row['difference_mm']:.1f}mm "
                f"({row['percent_diff']:.1f}% above average).")
    else:
        return (f"{month_number}: Drier than normal by {-row['difference_mm']:.1f}mm "
                f"({-row['percent_diff']:.1f}% below average).")

for m in compare['month']:
    print(precipitation_summary(m))


