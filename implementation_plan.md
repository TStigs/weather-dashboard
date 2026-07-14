# Weather Data Visualization Project Plan

This document reviews the current python scripts and presents potential directions for expanding, refactoring, and enhancing the weather data project.

## Project Analysis

Currently, the project consists of three main Python scripts with overlapping functionality:
1. [accessData.py](file:///Users/tylerstigall/Documents/Coding/projects/weatherDataVis/accessData.py): Fetches daily weather data from the Open-Meteo Archive API (1980–2025) for Victoria, BC, saves it as `historicalWeather.csv` and a 2020–2025 subset as `weather_data.csv`, and outputs simple matplotlib/seaborn line plots.
2. [weatherStatistics.py](file:///Users/tylerstigall/Documents/Coding/projects/weatherDataVis/weatherStatistics.py): Loads the historical weather data, calculates climatology (baseline averages), computes 30-day rolling anomalies (temperature and precipitation) for 2025, calculates monthly precipitation totals compared to normals, and prints/plots comparisons.
3. [Data Vis.py](file:///Users/tylerstigall/Documents/Coding/projects/weatherDataVis/Data%20Vis.py): Performs very similar calculations to `weatherStatistics.py` (climatology, 30-day rolling anomalies, monthly precip differences) and generates heatmaps of "hot days" (>25°C) and line plots.

### Current Challenges
* **Code Duplication**: Logic for computing climatology, rolling anomalies, and monthly summaries is duplicated across `Data Vis.py` and `weatherStatistics.py`.
* **Hardcoded Settings**: Location (Victoria coordinates), date ranges, temperature thresholds (25°C), and baseline year ranges are hardcoded in the scripts.
* **Static Visualizations**: Plots are displayed sequentially using blocking `plt.show()`, making exploration tedious.

---

## Open Questions

Before we write code, which of the following directions would you like to prioritize?

> [!IMPORTANT]
> **Please review the options below and let me know your preferences:**

1. **Option A: Interactive Dashboard (Recommended)**
   * Build a local interactive dashboard (e.g., using **Streamlit** or **Plotly Dash** in Python).
   * Allow users to dynamically adjust the location, threshold temperature, baseline years, smoothing window, and date ranges.
   * Provide interactive, hoverable charts for climatology comparison, anomalies, and heatmaps.

2. **Option B: Multi-Location & CLI Support**
   * Refactor data fetching to support searching for locations by name (geocoding) or coordinates.
   * Create a Command Line Interface (CLI) to fetch data, generate summaries, and export CSV/Excel/images for any custom location and time range.

3. **Option C: Advanced Climate & Trend Analysis**
   * Implement statistical trend analysis (e.g., linear regression of average yearly temperature, rate of warming, frequency of extreme weather events over the decades).
   * Detect heatwaves, cold snaps, and precipitation drought periods.

4. **Option D: Code Refactoring & Testing Focus**
   * Clean up the existing codebase: separate data access, processing/math, and plotting into reusable modules.
   * Write unit tests for the core logic (e.g., climatology and anomaly math) to ensure calculations are correct and robust.

---

## Proposed Technical Changes

Depending on your selection, here is how the files will be structured:

### Refactoring & Core Logic (Applies to all paths)

#### [MODIFY] [accessData.py](file:///Users/tylerstigall/Documents/Coding/projects/weatherDataVis/accessData.py)
* Extract the API fetching logic into a reusable function/class.
* Support parameterized latitude, longitude, start_date, and end_date.

#### [NEW] `weather_core.py` (or a `utils/` folder)
* Move shared functions here:
  * `calculate_climatology(df, baseline_years)`
  * `calculate_rolling_anomalies(df, target_year, climatology, window)`
  * `calculate_monthly_precipitation_comparison(df, target_year, baseline_years)`
  * `count_hot_days(df, threshold)`

### Visualizations / Presentation (Choose one or more)

#### [NEW] `app.py` (If choosing Option A)
* A Streamlit dashboard file importing functions from `weather_core.py` to construct a premium web interface.

#### [MODIFY] [Data Vis.py](file:///Users/tylerstigall/Documents/Coding/projects/weatherDataVis/Data%20Vis.py) (If keeping static scripts)
* Clean up to import calculations from `weather_core.py` rather than recalculating in-place.

---

## Verification Plan

### Automated Tests
* Create unit tests to verify the calculations in `weather_core.py` (e.g. check that climatology calculations correctly average the same day of year across years).

### Manual Verification
* Run the scripts/dashboard and confirm visual and textual output match previous calculations.
