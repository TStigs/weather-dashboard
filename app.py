import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Ensure src is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.ingestion import CITIES, ingest_all_cities, ingest_city_data
from src.statistics import (
    calculate_climatology,
    calculate_rolling_anomalies,
    calculate_monthly_precipitation_comparison,
    calculate_hot_days
)

# Set page layout and aesthetics
st.set_page_config(
    page_title="Climate Analytics Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design: glassmorphism, typography, and card panels
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 300;
        color: #8A99AD;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Custom stats card container */
    .metric-card {
        background: var(--st-secondary-background-color, rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease, border 0.2s ease;
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border: 1px solid rgba(77, 150, 255, 0.4);
    }
    
    .metric-title {
        color: var(--st-text-color, #8A99AD);
        opacity: 0.75;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--st-text-color, #FFFFFF);
    }
    
    .metric-diff-positive {
        color: #00C853;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .metric-diff-negative {
        color: #D50000;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    /* Streamlit overrides */
    div.stButton > button {
        background: linear-gradient(135deg, #4D96FF 0%, #6BCB77 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 4px 15px rgba(77, 150, 255, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to check if data is populated
def check_data_exists():
    for city in CITIES.keys():
        csv_path = f"data/{city.lower()}.csv"
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) < 100:
            return False
    return True

# Initialize data if not present
if not check_data_exists():
    st.warning("⚠️ Weather database is missing or incomplete. Press the button below to ingest the historical data (1980–present) for all 5 cities.")
    if st.button("🚀 Ingest Historical Data Now"):
        with st.spinner("Fetching data from Open-Meteo Archive API... This may take up to a minute (uses local caching)."):
            try:
                ingest_all_cities(force_rebuild=False)
                st.success("🎉 Ingestion complete! Reloading dashboard...")
                st.rerun()
            except Exception as e:
                st.error(f"Error during ingestion: {e}")
                st.stop()
    st.stop()

# Title banner
st.markdown('<div class="main-title">Weather Analytics Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Decadal Climate Patterns and Anomalies (1980 - Present)</div>', unsafe_allow_html=True)

# Sidebar layout
st.sidebar.markdown("### Navigation & Settings")

# City selection
selected_city = st.sidebar.selectbox(
    "Select Target City:",
    options=list(CITIES.keys()),
    index=0
)

# Load data for selected city
csv_path = f"data/{selected_city.lower()}.csv"
df = pd.read_csv(csv_path)
df['date'] = pd.to_datetime(df['date'])
if 'month' not in df.columns:
    df['month'] = df['date'].dt.month
if 'year' not in df.columns:
    df['year'] = df['date'].dt.year
if 'day_of_year' not in df.columns:
    df['day_of_year'] = df['date'].dt.dayofyear

min_year = int(df['year'].min())
max_year = int(df['year'].max())

# Target Year Selection
target_year = st.sidebar.selectbox(
    "Select Target Year to Analyze:",
    options=sorted(list(df['year'].unique()), reverse=True),
    index=1 if len(df['year'].unique()) > 1 else 0  # Default to recent complete year
)

# Baseline Years Selection
st.sidebar.markdown("---")
st.sidebar.markdown("### Climatology Reference Baseline")
baseline_range = st.sidebar.slider(
    "Select Baseline Years Range:",
    min_value=min_year,
    max_value=max_year,
    value=(1980, 2019)
)

# Additional parameters
st.sidebar.markdown("---")
st.sidebar.markdown("### Parameters")
anomaly_window = st.sidebar.slider(
    "Smoothing Window (Days):",
    min_value=7,
    max_value=90,
    value=30,
    step=1
)

hot_day_threshold = st.sidebar.slider(
    "Hot Day Threshold (°C):",
    min_value=15.0,
    max_value=40.0,
    value=25.0,
    step=0.5
)

# Filter baseline array
baseline_years = list(range(baseline_range[0], baseline_range[1] + 1))

# Math operations using statistics module
climatology = calculate_climatology(df, baseline_years)
df_target_year = df[df['year'] == target_year]

# Summary statistics for target year
if not df_target_year.empty:
    mean_temp = df_target_year['temperature_2m_mean'].mean()
    max_temp = df_target_year['temperature_2m_max'].max()
    min_temp = df_target_year['temperature_2m_min'].min()
    total_precip = df_target_year['precipitation_sum'].sum()
    
    # Calculate baseline normals for comparison
    df_baseline = df[df['year'].isin(baseline_years)]
    normal_mean_temp = df_baseline['temperature_2m_mean'].mean()
    normal_total_precip = df_baseline.groupby('year')['precipitation_sum'].sum().mean()
    
    temp_diff = mean_temp - normal_mean_temp
    precip_pct_diff = ((total_precip - normal_total_precip) / normal_total_precip) * 100
    
    # Render layout metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp_class = "metric-diff-positive" if temp_diff > 0 else "metric-diff-negative"
        sign = "+" if temp_diff > 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Mean Temp ({target_year})</div>
            <div class="metric-value">{mean_temp:.2f}°C</div>
            <div class="{temp_class}">{sign}{temp_diff:.2f}°C vs Norm</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Max / Min Temp ({target_year})</div>
            <div class="metric-value" style="font-size: 1.8rem; padding-top: 0.3rem;">
                {max_temp:.1f}°C / {min_temp:.1f}°C
            </div>
            <div class="metric-title" style="margin-top:0.7rem; font-size:0.75rem;">Yearly Extremes</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        precip_class = "metric-diff-positive" if total_precip > normal_total_precip else "metric-diff-negative"
        psign = "+" if total_precip > normal_total_precip else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Precip ({target_year})</div>
            <div class="metric-value">{total_precip:.1f} mm</div>
            <div class="{precip_class}">{psign}{precip_pct_diff:.1f}% vs Norm ({normal_total_precip:.1f}mm)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        # Calculate hot days for this year
        hot_days_grid = calculate_hot_days(df_target_year, hot_day_threshold)
        total_hot_days = hot_days_grid.values.sum()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Hot Days (>{hot_day_threshold}°C)</div>
            <div class="metric-value">{total_hot_days} Days</div>
            <div class="metric-title" style="margin-top:0.7rem; font-size:0.75rem;">Target threshold: {hot_day_threshold}°C</div>
        </div>
        """, unsafe_allow_html=True)

# Layout: Tabs for visualization views
tab1, tab2, tab3, tab4 = st.tabs([
    "Climatology Comparison", 
    "Rolling Anomalies", 
    "Monthly Summaries", 
    "Heatwave Heatmaps"
])

# Customize matplotlib and seaborn styles to look modern
plt.style.use('dark_background')
sns.set_theme(style="darkgrid", rc={
    "grid.color": "#2D3748",
    "grid.linestyle": "--",
    "axes.facecolor": "#1A202C",
    "figure.facecolor": "#0F172A",
    "axes.edgecolor": "#2D3748",
    "text.color": "#E2E8F0",
    "xtick.color": "#A0AEC0",
    "ytick.color": "#A0AEC0",
    "font.family": "sans-serif"
})

# Tab 1: Climatology comparison plots
with tab1:
    st.markdown("### Daily Temperature & Precipitation compared to Historical Normals")
    
    if df_target_year.empty:
        st.warning("No data found for the selected target year.")
    else:
        # Merge target year with climatology
        comp_df = df_target_year.merge(climatology, on='day_of_year', how='left')
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(comp_df['day_of_year'], comp_df['temperature_2m_mean'], label=f'{target_year} Daily Mean', color='#4D96FF', alpha=0.9, linewidth=1.5)
            ax.plot(comp_df['day_of_year'], comp_df['temp_climatology'], label='Historical Normal', color='#FF6B6B', alpha=0.9, linestyle='--', linewidth=2)
            
            # Add range shading (Min to Max historical range or target Min-Max envelope)
            ax.fill_between(comp_df['day_of_year'], comp_df['temperature_2m_min'], comp_df['temperature_2m_max'], color='#4D96FF', alpha=0.1, label='Target Year Min-Max Range')
            
            ax.set_title(f"{selected_city}: {target_year} Temperature vs Climatology Norm", fontsize=12, fontweight='bold', pad=15)
            ax.set_xlabel("Day of Year", labelpad=10)
            ax.set_ylabel("Temperature (°C)", labelpad=10)
            ax.legend(frameon=True, facecolor='#1A202C', edgecolor='none')
            fig.tight_layout()
            st.pyplot(fig)
            
        with col_c2:
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Smooth precipitation for better visualization
            target_precip_smooth = comp_df['precipitation_sum'].rolling(7, center=True).mean()
            clim_precip_smooth = comp_df['precip_climatology'].rolling(7, center=True).mean()
            
            ax.plot(comp_df['day_of_year'], target_precip_smooth, label=f'{target_year} (7-Day Smooth)', color='#6BCB77', alpha=0.9, linewidth=2)
            ax.plot(comp_df['day_of_year'], clim_precip_smooth, label='Normal (7-Day Smooth)', color='#FFD93D', alpha=0.8, linestyle='--', linewidth=2)
            
            ax.set_title(f"{selected_city}: Daily Precipitation vs Climatology Norm", fontsize=12, fontweight='bold', pad=15)
            ax.set_xlabel("Day of Year", labelpad=10)
            ax.set_ylabel("Precipitation (mm)", labelpad=10)
            ax.legend(frameon=True, facecolor='#1A202C', edgecolor='none')
            fig.tight_layout()
            st.pyplot(fig)

# Tab 2: Rolling Anomalies
with tab2:
    st.markdown(f"### {anomaly_window}-Day Rolling Anomalies")
    st.write("Anomalies show whether temperature or precipitation values were consistently above (positive) or below (negative) the baseline norm, smoothed by a moving average filter.")
    
    anom_df = calculate_rolling_anomalies(df, target_year, climatology, anomaly_window)
    
    if anom_df.empty:
        st.warning("Could not calculate anomalies. Make sure target year contains data.")
    else:
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(anom_df['day_of_year'], anom_df['temp_anomaly_roll'], color='#FF6B6B', linewidth=2, label='Temperature Anomaly')
            ax.axhline(0, color='#8A99AD', linestyle='--', alpha=0.7)
            
            # Fill anomaly area for visual pop
            ax.fill_between(
                anom_df['day_of_year'], 
                0, 
                anom_df['temp_anomaly_roll'], 
                where=(anom_df['temp_anomaly_roll'] >= 0), 
                color='#FF6B6B', 
                alpha=0.2
            )
            ax.fill_between(
                anom_df['day_of_year'], 
                0, 
                anom_df['temp_anomaly_roll'], 
                where=(anom_df['temp_anomaly_roll'] < 0), 
                color='#4D96FF', 
                alpha=0.2
            )
            
            ax.set_title(f"{selected_city}: Temperature Anomaly vs Normal", fontsize=12, fontweight='bold', pad=15)
            ax.set_ylabel("Temperature Anomaly (°C)", labelpad=10)
            ax.set_xlabel("Day of Year", labelpad=10)
            fig.tight_layout()
            st.pyplot(fig)
            
        with col_a2:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(anom_df['day_of_year'], anom_df['precip_anomaly_roll'], color='#6BCB77', linewidth=2, label='Precipitation Anomaly')
            ax.axhline(0, color='#8A99AD', linestyle='--', alpha=0.7)
            
            # Fill anomaly area
            ax.fill_between(
                anom_df['day_of_year'], 
                0, 
                anom_df['precip_anomaly_roll'], 
                where=(anom_df['precip_anomaly_roll'] >= 0), 
                color='#6BCB77', 
                alpha=0.2
            )
            ax.fill_between(
                anom_df['day_of_year'], 
                0, 
                anom_df['precip_anomaly_roll'], 
                where=(anom_df['precip_anomaly_roll'] < 0), 
                color='#FFD93D', 
                alpha=0.2
            )
            
            ax.set_title(f"{selected_city}: Precipitation Anomaly vs Normal", fontsize=12, fontweight='bold', pad=15)
            ax.set_ylabel("Precipitation Anomaly (mm)", labelpad=10)
            ax.set_xlabel("Day of Year", labelpad=10)
            fig.tight_layout()
            st.pyplot(fig)

# Tab 3: Monthly Summaries
with tab3:
    st.markdown("### Monthly Precipitation Summary")
    
    monthly_comp = calculate_monthly_precipitation_comparison(df, target_year, baseline_years)
    
    if monthly_comp.empty:
        st.warning("Could not compute monthly comparisons.")
    else:
        col_m1, col_m2 = st.columns([3, 2])
        
        with col_m1:
            fig, ax = plt.subplots(figsize=(10, 5))
            
            months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            colors = ['#FF6B6B' if val < 0 else '#6BCB77' for val in monthly_comp['percent_diff']]
            
            bars = ax.bar(monthly_comp['month'], monthly_comp['percent_diff'], color=colors, alpha=0.85, width=0.6)
            ax.axhline(0, color='#FFFFFF', linestyle='-', linewidth=0.8, alpha=0.7)
            
            # Add text labels on bars
            for bar in bars:
                height = bar.get_height()
                label_y = height + 1.5 if height >= 0 else height - 4.5
                ax.annotate(f'{height:.1f}%',
                            xy=(bar.get_x() + bar.get_width() / 2, label_y),
                            xytext=(0, 0),  
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, color='#E2E8F0')
            
            ax.set_title(f"{selected_city}: Monthly Precipitation % Difference relative to Normal ({target_year})", fontsize=11, fontweight='bold', pad=15)
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels(months_names)
            ax.set_ylabel("% Difference", labelpad=10)
            ax.set_ylim(min(monthly_comp['percent_diff']) - 15, max(monthly_comp['percent_diff']) + 15)
            fig.tight_layout()
            st.pyplot(fig)
            
        with col_m2:
            st.markdown("#### Detailed Anomalies Summary")
            
            def render_month_summary(row):
                m_num = int(row['month'])
                m_name = months_names[m_num - 1]
                diff = row['difference_mm']
                pct = row['percent_diff']
                
                if diff > 0:
                    icon = "🌧️"
                    change_text = f"**{diff:.1f} mm** ({pct:.1f}% **above** normal)"
                    color = "rgba(107, 203, 119, 0.15)"
                    border_color = "#6BCB77"
                else:
                    icon = "☀️"
                    change_text = f"**{-diff:.1f} mm** ({-pct:.1f}% **below** normal)"
                    color = "rgba(255, 107, 107, 0.15)"
                    border_color = "#FF6B6B"
                    
                st.markdown(f"""
                <div style="background: {color}; border-left: 5px solid {border_color}; padding: 0.8rem; border-radius: 4px; margin-bottom: 0.5rem;">
                    {icon} <strong>{m_name}</strong>: {change_text}
                </div>
                """, unsafe_allow_html=True)
                
            for index, row in monthly_comp.iterrows():
                render_month_summary(row)

# Tab 4: Extreme Heat Heatmaps
with tab4:
    st.markdown("### Extreme Temperature Heatmap")
    st.write(f"The grid shows the exact number of days in each month where the daily maximum temperature exceeded **{hot_day_threshold}°C**.")
    
    # We want to display a full heatmap of hot days for the recent years to trace the historical progression
    hot_days_all = calculate_hot_days(df, hot_day_threshold)
    
    # Filter heatmap to recent decade for readable visual
    recent_years_limit = 10
    hot_days_recent = hot_days_all.tail(recent_years_limit)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    sns.heatmap(
        hot_days_recent, 
        annot=True, 
        fmt=".0f", 
        cmap="YlOrRd", 
        cbar_kws={'label': f'Days > {hot_day_threshold}°C'},
        linewidths=0.5,
        ax=ax,
        annot_kws={"fontsize": 10}
    )
    
    ax.set_title(f"Number of Extreme Heat Days Per Month (>{hot_day_threshold}°C) - Last {recent_years_limit} Years", fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("Month", labelpad=10)
    ax.set_ylabel("Year", labelpad=10)
    ax.set_xticklabels(months_labels)
    fig.tight_layout()
    st.pyplot(fig)
    
    # Bar chart of yearly totals of hot days over the entire dataset
    st.markdown("#### Long-term Trend: Extreme Heat Days Per Year")
    yearly_totals = hot_days_all.sum(axis=1)
    
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    ax2.bar(yearly_totals.index, yearly_totals.values, color='#FF9F43', alpha=0.85)
    ax2.set_title(f"Annual Frequency of Extreme Heat Days (>{hot_day_threshold}°C)", fontsize=11, fontweight='bold', pad=15)
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Count of Days")
    fig2.tight_layout()
    st.pyplot(fig2)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #8A99AD; font-size: 0.8rem; margin-top: 2rem;'>"
    "Data Source: Open-Meteo Historical Weather API. Local caching is enabled to prevent redundant API queries."
    "</div>", 
    unsafe_allow_html=True
)
