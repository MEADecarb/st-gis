from streamlit_folium import st_folium
import json
import requests
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt

class GeoDataVisualizer:
    def __init__(self):
        self.map = folium.Map(location=[39.0458, -76.6413], zoom_start=7)  # Centered on Maryland
        self.marker_cluster = MarkerCluster().add_to(self.map)
        self.uploaded_files = []
        self.selected_files = []
        self.data_frames = []
        self.latitude_column = None
        self.longitude_column = None
        self.github_files = {}
        self.chart_columns = []  # Store chart columns selected by the user
        self.chart_type = 'Bar'  # Default chart type
        self._setup_page()

    def _setup_page(self):
        st.set_page_config(page_title="Web Layers", layout="wide", page_icon="🛰️")
        st.sidebar.markdown("# Web Feature Services Visualization 🛰️")
        st.sidebar.write("This is where you can find MD GIS data: [MD iMAP](https://data.imap.maryland.gov/)")
        self._get_files()
        if self.uploaded_files or self.selected_files:
            self._load_data()
            self._display_layout()

    def _get_files(self):
        uploaded_files = st.file_uploader("Upload one or more files", type=["csv", "xlsx", "geojson"], accept_multiple_files=True)
        if uploaded_files:
            self.uploaded_files = uploaded_files
        st.write("Or")
        wfs_url = st.text_input("Enter WFS URL")
        if wfs_url:
            self.selected_files.append(wfs_url)

    def _load_data(self):
        all_files = self.uploaded_files + self.selected_files
        if all_files:
            for file in all_files:
                if isinstance(file, str):
                    self._load_data_from_url(file)
                else:
                    self._load_data_from_file(file)
            folium.LayerControl().add_to(self.map)

    def _load_data_from_url(self, url):
        extension = url.split(".")[-1]
        if extension == "geojson":
            data_frame = gpd.read_file(url)
            self.data_frames.append(data_frame)
            json_data_frame = json.loads(data_frame.to_json())
            self._add_geojson_layer(json_data_frame, url.split('/')[-1])
        elif extension == "csv":
            data_frame = pd.read_csv(url)
            self.data_frames.append(data_frame)
            self._add_markers(data_frame)

    def _load_data_from_file(self, uploaded_file):
        extension = uploaded_file.name.split(".")[-1]
        if extension in {"csv", "xlsx"}:
            data_frame = pd.read_csv(uploaded_file) if extension == "csv" else pd.read_excel(uploaded_file)
            self.data_frames.append(data_frame)
            self._add_markers(data_frame)

    def _add_geojson_layer(self, json_data_frame, layer_name):
        folium.GeoJson(json_data_frame, name=layer_name).add_to(self.map)

    def _add_markers(self, data_frame):
        for _, row in data_frame.iterrows():
            folium.Marker(
                location=[row['lat'], row['lon']], 
                popup=folium.Popup(str(row))
            ).add_to(self.marker_cluster)

    def _display_layout(self):
        col1, col2 = st.columns([2, 1])
        with col1:
            map_data = st_folium(self.map, width=800, height=500, returned_objects=['bounds'])
            self.map_bounds = map_data['bounds'] if 'bounds' in map_data else None
            st.write(f"Current map bounds: {self.map_bounds}")
        
        with col2:
            if self.map_bounds:
                st.write("Displaying data within current bounds:")
                visible_data = self._filter_data_by_bounds(self.map_bounds)
                st.dataframe(visible_data)
                self._plot_charts_based_on_columns(visible_data)

    def _filter_data_by_bounds(self, bounds):
        if not bounds or not self.data_frames:
            return pd.DataFrame()
        min_lon, min_lat = bounds['_southWest']['lng'], bounds['_southWest']['lat']
        max_lon, max_lat = bounds['_northEast']['lng'], bounds['_northEast']['lat']
        data_frame = pd.concat(self.data_frames)
        return data_frame[(data_frame['lon'] >= min_lon) & (data_frame['lon'] <= max_lon) &
                          (data_frame['lat'] >= min_lat) & (data_frame['lat'] <= max_lat)]

    def _plot_charts_based_on_columns(self, visible_data):
        chart_columns = st.sidebar.multiselect("Select columns for charting:", visible_data.columns)
        chart_type = st.sidebar.selectbox("Select chart type:", ['Bar', 'Pie'])
        if chart_columns:
            for column in chart_columns:
                if chart_type == 'Bar':
                    visible_data[column].value_counts().plot(kind='bar')
                    st.pyplot(plt.gcf())
                elif chart_type == 'Pie':
                    visible_data[column].value_counts().plot(kind='pie', autopct='%1.1f%%')
                    st.pyplot(plt.gcf())

if __name__ == "__main__":
    GeoDataVisualizer()
