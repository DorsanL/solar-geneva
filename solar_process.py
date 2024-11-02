from unicodedata import numeric

import geopandas as gpd
import pandas as pd
import numpy as np
import pickle

from statsmodels.tsa.holtwinters import ExponentialSmoothing

communes = gpd.read_file("data/raw/communes.gpkg")
girec = gpd.read_file("data/raw/girec.gpkg")
pronovo = gpd.read_file("data/raw/pronovo.gpkg")

girec_potential = pd.read_pickle("data/qbuildings/girec_potential.pickle") / 1000  # Convert to MWc

# %% Create merged GeoDataFrame from pronovo, girec, and communes

# spatial join between pronovo and girec to assign sub-municipality (girec)
pronovo_girec = gpd.sjoin(pronovo, girec[['geometry', 'NOM', 'NO_COMM']], how="left", predicate='within')

# join between pronovo_girec and communes to assign the municipality (commune)
pronovo_girec_commune = pronovo_girec.merge(communes[['COMMUNE', 'NO_COMM']], on='NO_COMM', how='left')

# final GeoDataFrame with the required columns
photovoltaic = pronovo_girec_commune[['TotalPower', 'BeginningOfOperation', 'NOM', 'COMMUNE', 'geometry']].copy()
photovoltaic = photovoltaic.rename(columns={
    'TotalPower': 'power',
    'BeginningOfOperation': 'construction',
    'NOM': 'girec',
    'COMMUNE': 'commune'
})

# %% Process data to get historical values (girec)

# Convert 'construction' column to datetime format
photovoltaic['construction'] = pd.to_datetime(photovoltaic['construction'])

# Extract the year and convert 'power' column to numeric for aggregation
photovoltaic['year'] = photovoltaic['construction'].dt.year
photovoltaic['power'] = pd.to_numeric(photovoltaic['power'], errors='coerce') / 1000  # Convert to MWc

# Group by 'girec' and 'year', and sum the power
yearly_power = photovoltaic.groupby(['girec', 'year'])['power'].sum().reset_index()

# Pivot the table to have each year as a column
pivot_power = yearly_power.pivot(index='girec', columns='year', values='power').fillna(0)

# Calculate the cumulative sum starting from year 2005 to 2024
years = list(range(2005, 2024 + 1))

# Add all years in the pivot table to ensure no missing years for cumulative calculation
all_years = sorted(pivot_power.columns.union(years))
pivot_power = pivot_power.reindex(columns=all_years, fill_value=0).cumsum(axis=1)

# Select only the cumulative sums for 2005 to 2024
pivot_power = pivot_power[years]

# Join the cumulative power back to the 'girec' GeoDataFrame
girec_historical = girec.merge(pivot_power, left_on='NOM', right_index=True, how='left')

# Replace missing values with 0 (if there are any sub-municipalities with no installations)
girec_historical = girec_historical.fillna(0)

# Replace the integer COMMUNE identifiers in girec_historical with the corresponding names
commune_mapping = communes.set_index('NO_COMM')['COMMUNE'].to_dict()
girec_historical['COMMUNE'] = girec_historical['NO_COMM'].map(commune_mapping)

# Set NOM as the index and keep only relevant columns
girec_historical = girec_historical.set_index('NOM')
girec_historical = girec_historical[['COMMUNE', 'geometry'] + [col for col in list(range(2005, 2024 + 1))]]

# %% Forecasting future values with Holt’s Linear Trend Model (girec)

years = list(range(2005, 2025))
forecast_years = list(range(2025, 2051))

girec_forecast_lin = pd.DataFrame(index=girec_historical.index, columns=forecast_years)

# Loop through each girec
for girec in girec_historical.index:
    # Get historical data for the girec
    girec_data = np.asarray(girec_historical.loc[girec, years])

    # Fit Holt's Linear Model (trend only, no seasonality)
    model = ExponentialSmoothing(girec_data, trend='add', seasonal=None)
    fit = model.fit()

    # Forecast for the next years
    forecast = fit.forecast(len(forecast_years))

    # Save forecast in the result DataFrame
    girec_forecast_lin.loc[girec, :] = forecast

girec_forecast_lin = girec_forecast_lin.astype(float)

girec_lin = pd.concat([girec_historical, girec_forecast_lin, girec_potential], axis=1)

# %% Forecasting future values with Exponential Trend Model (girec)

current_year = 2024
target_capacity_2050 = 1000  # MWc

girec_forecast_exp = pd.DataFrame(index=girec_historical.index, columns=forecast_years)

# Sum of the PV capacities for each girec in 2024 (used as y_0)
y_0_total = girec_historical[2024].sum()

# Determine the required growth rate to reach 1000 MWc by 2050
# r = ln(target / y_0) / (forecast_year - current_year)
r_target = np.log(target_capacity_2050 / y_0_total) / (2050 - current_year)

# Forecast capacity for each municipality with exponential growth
for girec in girec_historical.index:
    # y_0 for the girec (capacity at the end of 2024)
    y_0_girec = girec_historical.loc[girec, 2024]

    # Generate forecasts using the adjusted growth rate
    forecast_values = [y_0_girec * np.exp(r_target * (year - current_year)) for year in forecast_years]

    # Store results in the forecast DataFrame
    girec_forecast_exp.loc[girec, :] = forecast_values

girec_forecast_exp = girec_forecast_exp.astype(float)
girec_exp = pd.concat([girec_historical, girec_forecast_exp, girec_potential], axis=1)

# %% Forecasting future values for communes from girec aggregation
communes_lin = girec_lin.dissolve(by='COMMUNE', aggfunc='sum')
communes_lin = communes_lin.reset_index().set_index('COMMUNE')
communes_lin = communes_lin[['geometry'] + [col for col in list(range(2005, 2050 + 1))] + ['pv_potential']]

communes_exp = girec_exp.dissolve(by='COMMUNE', aggfunc='sum')
communes_exp = communes_exp.reset_index().set_index('COMMUNE')
communes_exp = communes_exp[['geometry'] + [col for col in list(range(2005, 2050 + 1))] + ['pv_potential']]

# %% Save the processed data to pickle files

output = {
    'girec_lin': girec_lin,
    'communes_lin': communes_lin,
    'girec_exp': girec_exp,
    'communes_exp': communes_exp
}

for key, value in output.items():
    value = value.fillna(0)
    value = value.round(2)
    value = value.set_crs("EPSG:2056").to_crs("EPSG:4326")

    f = open(f"output/{key}.pickle", 'wb')
    pickle.dump(value, f)
    f.close()


# %% Print some results

lin_2050 = communes_lin[2050].sum()
exp_2050 = communes_exp[2050].sum()

print("lin_2050 : ", lin_2050)
print("exp_2050 : ", exp_2050)
