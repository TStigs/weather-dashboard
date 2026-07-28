# Weather Analytics Dashboard 🌤️📊

An interactive Streamlit web application designed for exploring, visualizing, and analyzing decadal climate patterns, temperature anomalies, precipitation norms, and extreme weather events (1980 – Present) across Canadian cities.

Data is fetched dynamically via the **Open-Meteo Historical Weather API**, validated, cached locally, and processed using **Pandas**, **NumPy**, **Matplotlib**, and **Seaborn**.

---

## ✨ Features

- 🏙️ **Multi-City Analysis**: Comprehensive historical weather data for Victoria, Vancouver, Calgary, Toronto, Halifax, and Penticton.
- 📊 **Climatology Norms**: Compare any target year's daily mean temperature and precipitation envelope against configurable historical baseline ranges (e.g., 1980–2019).
- 📈 **Rolling Anomalies**: Compute custom moving-average temperature and precipitation deviations ($7$ to $90$-day windows) to identify sustained heatwaves or cold snaps.
- 📅 **Monthly Summaries**: Analyze total monthly precipitation against baseline normal distributions with percentage variance metrics.
- 🌡️ **Heatwave Heatmaps**: Interactive matrix heatmaps displaying monthly counts of hot days above user-defined temperature thresholds (e.g., $\ge 25^\circ\text{C}$).
- ⚡ **Automated Ingestion & Caching**: Efficient API ingestion pipeline featuring SQLite response caching, automatic retries, and data validation rules.

---

## 📁 Repository Structure

```text
weather-dashboard/
├── app.py                   # Streamlit dashboard application UI & interactive charts
├── requirements.txt         # Project Python dependencies
├── src/                     # Core application modules
│   ├── ingestion.py         # Open-Meteo API fetcher, caching & data transformation
│   ├── statistics.py        # Climatology, rolling anomalies, and heatmap computations
│   └── validation.py        # Data hygiene and quality assurance checks
├── data/                    # Generated CSV datasets per city (populated after ingestion)
├── tests/                   # Automated unit test suite
│   └── test_statistics.py   # Pytest tests for statistical calculations
├── ingestion.log            # Logging output for data pipeline execution
└── data_validation.log      # Logging output for data quality checks
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
# Clone the repository
git clone https://github.com/TStigs/weather-dashboard.git
cd weather-dashboard

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the Dashboard

Run the Streamlit application:

```bash
streamlit run app.py
```

> **Note**: On initial startup, if local city dataset files are not present in `data/`, the app will prompt you to run the automated data ingestion pipeline. Click **Ingest Historical Data Now** to fetch data from Open-Meteo.

---

## 🧪 Running Tests

Run the automated test suite using `pytest`:

```bash
pytest
```

Or run via virtual environment explicitly:

```bash
.venv/bin/python -m pytest
```

---

## 🛠️ Data Source & Acknowledgments

- **Open-Meteo Historical Weather API**: High-resolution historical weather dataset derived from ERA5 reanalysis data.
- Built with [Streamlit](https://streamlit.io/), [Pandas](https://pandas.pydata.org/), [Matplotlib](https://matplotlib.org/), and [Seaborn](https://seaborn.pydata.org/).
