import json
from typing import List, Dict, Any
import requests
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

# Constants
DEFAULT_MAP_CENTER = [39.0458, -76.6413]  # Maryland
DEFAULT_ZOOM = 7
ALLOWED_FILE_TYPES = ["csv", "xlsx", "geojson"]
CHART_TYPES = ['Bar', 'Pie']

class GeoDataVisualizer:
  def __init__(self):
      self.map = folium.Map(location=DEFAULT_MAP_CENTER, zoom_start=DEFAULT_ZOOM)
      self.marker_cluster = MarkerCluster().add_to(self.map)
      self.data_frames: List[pd.DataFrame] = []
      self.map_bounds: Dict[str, Any] = {}

  @st.cache_data
  def load_data_from_url(self, url: str) -> pd.DataFrame:
      try:
          if url.endswith("geojson"):
              return gpd.read_file(url)
          elif url.endswith("csv"):
              return pd.read_csv(url)
          else:
              st.error(f"Unsupported file type: {url}")
              return pd.DataFrame()
      except Exception as e:
          st.error(f"Error loading data from {url}: {str(e)}")
          return pd.DataFrame()

  @st.cache_data
  def load_data_from_file(self, file) -> pd.DataFrame:
      try:
          if file.name.endswith("csv"):
              return pd.read_csv(file)
          elif file.name.endswith("xlsx"):
              return pd.read_excel(file)
          else:
              st.error(f"Unsupported file type: {file.name}")
              return pd.DataFrame()
      except Exception as e:
          st.error(f"Error loading data from {file.name}: {str(e)}")
          return pd.DataFrame()

  def add_geojson_layer(self, data: gpd.GeoDataFrame, layer_name: str):
      folium.GeoJson(data, name=layer_name).add_to(self.map)

  def add_markers(self, data: pd.DataFrame):
      if 'lat' not in data.columns or 'lon' not in data.columns:
          st.error("Data must contain 'lat' and 'lon' columns")
          return
      for _, row in data.iterrows():
          folium.Marker(
              location=[row['lat'], row['lon']], 
              popup=folium.Popup(str(row))
          ).add_to(self.marker_cluster)

  def filter_data_by_bounds(self, bounds: Dict[str, Any]) -> pd.DataFrame:
      if not bounds or not self.data_frames:
          return pd.DataFrame()
      min_lon, min_lat = bounds['_southWest']['lng'], bounds['_southWest']['lat']
      max_lon, max_lat = bounds['_northEast']['lng'], bounds['_northEast']['lat']
      data_frame = pd.concat(self.data_frames)
      return data_frame[(data_frame['lon'] >= min_lon) & (data_frame['lon'] <= max_lon) &
                        (data_frame['lat'] >= min_lat) & (data_frame['lat'] <= max_lat)]

  def plot_charts(self, data: pd.DataFrame, columns: List[str], chart_type: str):
      for column in columns:
          fig, ax = plt.subplots()
          if chart_type == 'Bar':
              data[column].value_counts().plot(kind='bar', ax=ax)
          elif chart_type == 'Pie':
              data[column].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
          st.pyplot(fig)

  def run(self):
      st.set_page_config(page_title="Web Layers", layout="wide", page_icon="🛰️")
      st.sidebar.markdown("# Web Feature Services Visualization 🛰️")
      st.sidebar.write("This is where you can find MD GIS data: [MD iMAP](https://data.imap.maryland.gov/)")

      uploaded_files = st.file_uploader("Upload one or more files", type=ALLOWED_FILE_TYPES, accept_multiple_files=True)
      wfs_url = st.text_input("Or enter WFS URL")

      if uploaded_files or wfs_url:
          for file in uploaded_files:
              df = self.load_data_from_file(file)
              if not df.empty:
                  self.data_frames.append(df)
                  self.add_markers(df)

          if wfs_url:
              df = self.load_data_from_url(wfs_url)
              if not df.empty:
                  self.data_frames.append(df)
                  if isinstance(df, gpd.GeoDataFrame):
                      self.add_geojson_layer(df, wfs_url.split('/')[-1])
                  else:
                      self.add_markers(df)

          folium.LayerControl().add_to(self.map)

          col1, col2 = st.columns([2, 1])
          with col1:
              map_data = st_folium(self.map, width=800, height=500, returned_objects=['bounds'])
              self.map_bounds = map_data['bounds'] if 'bounds' in map_data else {}
              st.write(f"Current map bounds: {self.map_bounds}")
          
          with col2:
              if self.map_bounds:
                  st.write("Displaying data within current bounds:")
                  visible_data = self.filter_data_by_bounds(self.map_bounds)
                  st.dataframe(visible_data)
                  
                  chart_columns = st.multiselect("Select columns for charting:", visible_data.columns)
                  chart_type = st.selectbox("Select chart type:", CHART_TYPES)
                  if chart_columns:
                      self.plot_charts(visible_data, chart_columns, chart_type)

if __name__ == "__main__":
  GeoDataVisualizer().run()
