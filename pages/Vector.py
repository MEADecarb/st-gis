import json
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
        self.uploaded_file = None
        self.data_frame = None
        self.latitude_column = None
        self.longitude_column = None
        self._setup_page()

    def _setup_page(self):
        st.set_page_config(page_title="Data Visualization", layout="wide", page_icon="🗺️")
        st.sidebar.markdown("# Vector Data Visualization 🗺️")
        self.uploaded_file = self._get_uploaded_file()
        self._add_basemaps()
        self._load_data()

    def _get_uploaded_file(self):
        file = st.file_uploader("Upload a file", type=["csv", "xlsx", "zip", "geojson"])
        if file:
            return file
        st.write("Or")
        return st.selectbox(
            "Choose an option",
            [
                "https://raw.githubusercontent.com/incubated-geek-cc/xy-to-latlng-convertor/main/data/CHASClinics_Output.csv",
                "https://raw.githubusercontent.com/LonnyGomes/CountryGeoJSONCollection/master/geojson/EGY.geojson",
                "https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/vienna-streets.geojson",
            ],
        )

    def _add_basemaps(self):
        folium.TileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            name="ESRI Satellite",
            attr="ESRI",
        ).add_to(self.map)
        folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark").add_to(self.map)

    def _load_data(self):
        if isinstance(self.uploaded_file, str):
            self._load_data_from_url(self.uploaded_file)
        elif self.uploaded_file is not None:
            extension = self.uploaded_file.name.split(".")[-1]
            if extension in {"csv", "xlsx"}:
                self._load_tabular_data(extension)
            else:
                self._load_geospatial_data()

    def _load_data_from_url(self, url):
        extension = url.split(".")[-1]
        layer_name = url.split('/')[-1].split('.')[0]
        if extension == "geojson":
            self.data_frame = gpd.read_file(url)
            json_data_frame = json.loads(self.data_frame.to_json())
            self._display_data()
            self._fit_map_to_bounds(self.data_frame.total_bounds)
            self._add_geojson_layer(json_data_frame, layer_name)
        elif extension in {"csv", "xlsx"}:
            self._load_tabular_data(extension)
        else:
            st.write("Unsupported URL format or unable to load data.")

    def _load_tabular_data(self, extension):
        if extension == "csv":
            self.data_frame = pd.read_csv(self.uploaded_file)
        else:
            self.data_frame = pd.read_excel(self.uploaded_file, engine="openpyxl")

        self.latitude_column, self.longitude_column = self._select_lat_long_columns()

        self.data_frame = gpd.GeoDataFrame(
            self.data_frame,
            geometry=gpd.points_from_xy(
                self.data_frame[self.longitude_column],
                self.data_frame[self.latitude_column],
            ),
            crs="wgs84",
        ).dropna(subset=[self.longitude_column, self.latitude_column])

        self._fit_map_to_bounds(self.data_frame.total_bounds)
        self._display_data()
        self._add_markers()
        folium.LayerControl().add_to(self.map)
        folium_static(self.map, width=1000)

    def _select_lat_long_columns(self):
        col1, col2 = st.columns(2)

        with col1:
            lat_index = self._get_column_index("lat|latitude")
            latitude_column = st.selectbox(
                "Choose latitude column:", self.data_frame.columns, index=lat_index
            )
        with col2:
            lng_index = self._get_column_index("lng|long|longitude")
            longitude_column = st.selectbox(
                "Choose longitude column:", self.data_frame.columns, index=lng_index
            )

        return latitude_column, longitude_column

    def _get_column_index(self, pattern):
        column_guess = self.data_frame.columns.str.contains(pattern, case=False)
        if column_guess.any():
            return self.data_frame.columns.get_loc(self.data_frame.columns[column_guess][0])
        return 0

    def _load_geospatial_data(self):
        self.data_frame = gpd.read_file(self.uploaded_file)
        layer_name = self.uploaded_file.name.split(".")[0]
        json_data_frame = json.loads(self.data_frame.to_json())
        self._display_data()
        self._fit_map_to_bounds(self.data_frame.total_bounds)
        self._add_geojson_layer(json_data_frame, layer_name)

    def _add_geojson_layer(self, json_data_frame, layer_name):
        if "features" in json_data_frame and json_data_frame["features"]:
            property_keys = list(json_data_frame["features"][0]["properties"].keys())
            folium.GeoJson(
                self.data_frame,
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
            folium.GeoJson(self.data_frame, name=layer_name, zoom_on_click=True).add_to(self.map)
        folium.LayerControl().add_to(self.map)
        folium_static(self.map, width=1000)

    def _fit_map_to_bounds(self, bounds):
        self.map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def _add_markers(self):
        for _, row in self.data_frame.iterrows():
            popup_html = self.create_popup_html(row[:-1])
            folium.Marker(
                location=[row[self.latitude_column], row[self.longitude_column]],
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(self.marker_cluster)

    def _display_data(self):
        st.dataframe(self.data_frame.drop(columns="geometry"))

    def create_popup_html(self, properties):
        html = "<div style='max-height: 200px; overflow-y: auto;'>"
        for key, value in properties.items():
            html += f"<b>{key}</b>: {value}<br>"
        html += "</div>"
        return html


if __name__ == "__main__":
    GeoDataVisualizer()
