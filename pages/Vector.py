import json
import requests
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

class GeoDataVisualizer:
    def __init__(self):
        self.map = folium.Map([0, 0], zoom_start=2)
        self.marker_cluster = MarkerCluster().add_to(self.map)
        self.uploaded_files = None
        self.data_frames = []
        self.latitude_column = None
        self.longitude_column = None
        self._setup_page()

    def _setup_page(self):
        st.set_page_config(page_title="Data Visualization", layout="wide", page_icon="🗺️")
        st.sidebar.markdown("# Vector Data Visualization 🗺️")
        self.uploaded_files = self._get_uploaded_files()
        self._add_basemaps()
        self._load_data()

    def _get_uploaded_files(self):
        file = st.file_uploader("Upload a file", type=["csv", "xlsx", "zip", "geojson"], accept_multiple_files=True)
        if file:
            return file
        st.write("Or")
        file_options = self._fetch_github_files()
        return st.multiselect("Choose one or more options", file_options)

    def _fetch_github_files(self):
        url = "https://api.github.com/repos/MEADecarb/st-gis/contents/data"
        response = requests.get(url)
        if response.status_code == 200:
            file_list = [file_info['download_url'] for file_info in response.json() if file_info['name'].endswith(('.csv', '.geojson', '.xlsx', '.zip'))]
            return file_list
        else:
            st.error("Failed to fetch files from GitHub repository")
            return []

    def _add_basemaps(self):
        folium.TileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            name="ESRI Satellite",
            attr="ESRI",
        ).add_to(self.map)
        folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark").add_to(self.map)

    def _load_data(self):
        if self.uploaded_files:
            for uploaded_file in self.uploaded_files:
                if isinstance(uploaded_file, str):
                    self._load_data_from_url(uploaded_file)
                else:
                    self._load_data_from_file(uploaded_file)
            self._fit_map_to_all_bounds()
            folium.LayerControl().add_to(self.map)
            folium_static(self.map, width=1000)

    def _load_data_from_url(self, url):
        extension = url.split(".")[-1]
        layer_name = url.split('/')[-1].split('.')[0]
        if extension == "geojson":
            data_frame = gpd.read_file(url)
            self.data_frames.append(data_frame)
            json_data_frame = json.loads(data_frame.to_json())
            self._display_data(data_frame)
            self._add_geojson_layer(json_data_frame, layer_name)
        elif extension in {"csv", "xlsx"}:
            data_frame = self._load_tabular_data(url, extension)
            self.data_frames.append(data_frame)
            self._display_data(data_frame)
            self._add_markers(data_frame)
        else:
            st.write("Unsupported URL format or unable to load data.")

    def _load_data_from_file(self, uploaded_file):
        extension = uploaded_file.name.split(".")[-1]
        if extension in {"csv", "xlsx"}:
            data_frame = self._load_tabular_data(uploaded_file, extension)
            self.data_frames.append(data_frame)
            self._display_data(data_frame)
            self._add_markers(data_frame)
        else:
            data_frame = gpd.read_file(uploaded_file)
            self.data_frames.append(data_frame)
            layer_name = uploaded_file.name.split(".")[0]
            json_data_frame = json.loads(data_frame.to_json())
            self._display_data(data_frame)
            self._add_geojson_layer(json_data_frame, layer_name)

    def _load_tabular_data(self, file, extension):
        if extension == "csv":
            data_frame = pd.read_csv(file)
        else:
            data_frame = pd.read_excel(file, engine="openpyxl")

        self.latitude_column, self.longitude_column = self._select_lat_long_columns(data_frame)

        data_frame = gpd.GeoDataFrame(
            data_frame,
            geometry=gpd.points_from_xy(
                data_frame[self.longitude_column],
                data_frame[self.latitude_column],
            ),
            crs="wgs84",
        ).dropna(subset=[self.longitude_column, self.latitude_column])

        return data_frame

    def _select_lat_long_columns(self, data_frame):
        col1, col2 = st.columns(2)

        with col1:
            lat_index = self._get_column_index(data_frame, "lat|latitude")
            latitude_column = st.selectbox(
                "Choose latitude column:", data_frame.columns, index=lat_index
            )
        with col2:
            lng_index = self._get_column_index(data_frame, "lng|long|longitude")
            longitude_column = st.selectbox(
                "Choose longitude column:", data_frame.columns, index=lng_index
            )

        return latitude_column, longitude_column

    def _get_column_index(self, data_frame, pattern):
        column_guess = data_frame.columns.str.contains(pattern, case=False)
        if column_guess.any():
            return data_frame.columns.get_loc(data_frame.columns[column_guess][0])
        return 0

    def _add_geojson_layer(self, json_data_frame, layer_name):
        if "features" in json_data_frame and json_data_frame["features"]:
            property_keys = list(json_data_frame["features"][0]["properties"].keys())
            folium.GeoJson(
                json_data_frame,
                name=layer_name,
                zoom_on_click=True,
                highlight_function=lambda feature: {"fillColor": "dark gray"},
                popup=folium.GeoJsonPopup(
                    fields=property_keys,
                    aliases=property_keys,
                    localize=True,
                    style="max-height: 200px; overflow-y: auto;",
                ),
            ).add_to(self.map)
        else:
            folium.GeoJson(json_data_frame, name=layer_name, zoom_on_click=True).add_to(self.map)

    def _fit_map_to_bounds(self, bounds):
        self.map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def _fit_map_to_all_bounds(self):
        if self.data_frames:
            combined_bounds = None
            for data_frame in self.data_frames:
                if combined_bounds is None:
                    combined_bounds = data_frame.total_bounds
                else:
                    combined_bounds[0] = min(combined_bounds[0], data_frame.total_bounds[0])
                    combined_bounds[1] = min(combined_bounds[1], data_frame.total_bounds[1])
                    combined_bounds[2] = max(combined_bounds[2], data_frame.total_bounds[2])
                    combined_bounds[3] = max(combined_bounds[3], data_frame.total_bounds[3])
            self._fit_map_to_bounds(combined_bounds)

    def _add_markers(self, data_frame):
        for _, row in data_frame.iterrows():
            popup_html = self.create_popup_html(row[:-1])
            folium.Marker(
                location=[row[self.latitude_column], row[self.longitude_column]],
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(self.marker_cluster)

    def _display_data(self, data_frame):
        st.dataframe(data_frame.drop(columns="geometry"))

    def create_popup_html(self, properties):
        html = "<div style='max-height: 200px; overflow-y: auto;'>"
        for key, value in properties.items():
            html += f"<b>{key}</b>: {value}<br>"
        html += "</div>"
        return html

if __name__ == "__main__":
    GeoDataVisualizer()
