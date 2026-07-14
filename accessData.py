## This project aims to visualize weather patterns in the last few decades in victoria
## Possible extensions could include more locations

import openmeteo_requests
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests_cache
from retry_requests import retry

#
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
	"latitude": 48.4359,
	"longitude": -123.3516,
	"start_date": "1980-01-01",
	"end_date": "2025-12-12",
	"daily": ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min", "precipitation_sum", "daylight_duration", "sunshine_duration", "wind_speed_10m_max", "wind_gusts_10m_max"],
	"timezone": "America/Los_Angeles"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()
daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
daily_daylight_duration = daily.Variables(4).ValuesAsNumpy()
daily_sunshine_duration = daily.Variables(5).ValuesAsNumpy()
daily_wind_speed_10m_max = daily.Variables(6).ValuesAsNumpy()
daily_wind_gusts_10m_max = daily.Variables(7).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}

daily_data["temperature_2m_mean"] = daily_temperature_2m_mean
daily_data["temperature_2m_max"] = daily_temperature_2m_max
daily_data["temperature_2m_min"] = daily_temperature_2m_min
daily_data["precipitation_sum"] = daily_precipitation_sum
daily_data["daylight_duration"] = daily_daylight_duration
daily_data["sunshine_duration"] = daily_sunshine_duration
daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
daily_data["wind_gusts_10m_max"] = daily_wind_gusts_10m_max

daily_dataframe = pd.DataFrame(data = daily_data)
print(daily_dataframe.head())

# Normalize to remove time and timezone, keeping only the date
daily_dataframe["date"] = pd.to_datetime(daily_dataframe["date"]).dt.normalize()

daily_dataframe["year"] = daily_dataframe["date"].dt.year
daily_dataframe["day_of_year"] = daily_dataframe["date"].dt.dayofyear





#######
# All historical weather outputted here. Next steps are to output a certain date range.
######

daily_dataframe.to_csv("historicalWeather.csv", index=False)

######
# This is really the end of the document. The rest is plotting
######



## Plotting Year over year trends (starting simple with a subset of 2020-2025)

##
# Get a subsample of the data
#

df_filtered = daily_dataframe[
    daily_dataframe["year"].between(2020, 2025)
].copy()


# Optional: Sort to ensure lines plot in correct order
df_filtered = df_filtered.sort_values(["year", "day_of_year"])

print(df_filtered[["date", "year", "day_of_year"]].head())



###### Outputs a csv with all of the historical weather data
df_filtered.to_csv("weather_data.csv", index=False)



df_filtered = pd.read_csv("weather_data.csv")

print(df_filtered.columns)

# # Plotting mean temperature example
plt.figure(figsize=(14, 6))
sns.lineplot(
    data=df_filtered,
    x="day_of_year",
    y="temperature_2m_mean",  # You can change this to any variable
    hue="year",
    palette="tab10"
)

plt.title("Daily Mean Temperature (2020–2024)")
plt.xlabel("Day of Year")
plt.ylabel("Mean Temperature (°C)")
plt.legend(title="Year")

plt.show()


# Plot daily total precipitation for 2020–2024
sns.lineplot(
    data=df_filtered,
    x="day_of_year",
    y="precipitation_sum",
    hue="year",
    palette="coolwarm"
)
plt.title("Daily Precipitation (2020–2024)")
plt.xlabel("Day of Year")
plt.ylabel("Precipitation (mm)")
plt.tight_layout()
plt.show()

## Plots average mean daily temperature per day for 2020-2024

# Group by day of year and average across all years
avg_daily_temp = df_filtered.groupby('day_of_year')['temperature_2m_mean'].mean()

# Plot
plt.figure(figsize=(12, 6))
plt.plot(avg_daily_temp.index, avg_daily_temp.values, label='Average Daily Mean (2020–2024)', color='tab:blue')
plt.title('Average Daily Mean Temperature (2020–2024)')
plt.xlabel('Day of Year')
plt.ylabel('Temperature (°C)')
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()



# overlays all years over the average per day


