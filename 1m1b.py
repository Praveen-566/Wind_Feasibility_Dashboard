import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# Turbine specs
rho = 1.225  # air density in kg/m³
radius = 40  # rotor radius in meters
efficiency = 0.4
area = np.pi * radius**2

# Get lat/lon from city name using OpenStreetMap Nominatim
def get_lat_lon(location_name):
    url = "https://nominatim.openstreetmap.org/search"
    # Added a User-Agent header as Nominatim might block requests without it
    headers = {'User-Agent': 'YourAppName/1.0 (your_email@example.com)'}
    params = {'q': location_name, 'format': 'json', 'limit': 1}
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates for {location_name}: {e}")
        return None, None

# Fetch wind forecast using Open-Meteo API
def fetch_forecast(lat, lon, location):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "windspeed_10m",
        "forecast_days": 3,
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if 'hourly' not in data or 'time' not in data['hourly'] or 'windspeed_10m' not in data['hourly']:
            print(f"Unexpected data structure for {location}: {data}")
            return pd.DataFrame() # Return empty DataFrame on error

        timestamps = pd.to_datetime(data['hourly']['time'])
        wind_speeds = data['hourly']['windspeed_10m']
        
        df = pd.DataFrame({
            "location": location,
            "timestamp": timestamps,
            "wind_speed": wind_speeds
        })
        # Calculate power in kW
        df["power_kw"] = 0.5 * rho * area * (df["wind_speed"] ** 3) * efficiency / 1000
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching forecast for {location}: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

# Main script
def generate_forecast_data(cities_input):
    cities = [city.strip() for city in cities_input.split(",")]
    
    final_df = pd.DataFrame()

    for city in cities:
        lat, lon = get_lat_lon(city)
        if lat is not None and lon is not None:
            print(f"Fetching data for {city}...")
            city_df = fetch_forecast(lat, lon, city)
            if not city_df.empty:
                final_df = pd.concat([final_df, city_df], ignore_index=True)
            else:
                print(f"No forecast data obtained for {city}.")
        else:
            print(f"Could not get coordinates for {city}. Skipping.")
    
    if not final_df.empty:
        # Save to CSV
        file_name = "forecast_multi_city.csv"
        final_df.to_csv(file_name, index=False)
        print(f"Forecast saved to {file_name}")
    else:
        print("No data was generated for any city.")

# Example usage:
if __name__ == "__main__":
    # You can change this to be hardcoded, or keep the input for local testing.
    # For Tableau Public, you'd run this script to generate the CSV, then upload.
    user_input_cities = input("Enter cities separated by comma (e.g., Chennai,Hyderabad): ")
    generate_forecast_data(user_input_cities)
