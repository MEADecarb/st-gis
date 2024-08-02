import json
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import requests

class GeoDataManipulator:
    def __init__(self):
        self.map = folium.Map([0, 0], zoom_start=2)
        self.marker_cluster = MarkerCluster().add_to(self.map)
        self.uploaded_files = None
        self.selected_files = None
        self.data_frame = None
        self.latitude_column = None
        self.longitude_column = None
        self.github_files = {}
        self._setup_page()

    def _setup_page(self):
        st.set_page_config(page_title="Data Visualization", layout="wide", page_icon="🗺️")
        st.sidebar.markdown("# Vector Data Visualization 🗺️")
        with st.sidebar.expander("User Instructions"):
            st.markdown("""
            ### Instructions:
            1. **Upload Files**: Use the uploader to add your own files in CSV, XLSX, ZIP, or GEOJSON formats.
            2. **Select Files**: Alternatively, select from pre-uploaded files using the dropdown menu.
            3. **View Map**: The map will automatically update to display the data from the selected or uploaded files.
            4. **Data Table**: The data associated with the map will be displayed below the map.
            """)
        self._get_files()
        self._load_data()
        self._save_data()

    def _get_files(self):
        uploaded_files = st.file_uploader("Upload one or more files", type=["csv", "xlsx", "zip", "geojson"], accept_multiple_files=True)
        if uploaded_files:
            self.uploaded_files = uploaded_files
        st.write("Or")
        file_options = self._fetch_github_files()
        if file_options:
            selected_files = st.multiselect("Choose one or more options", list(file_options.keys()))
            self.selected_files = [file_options[file_name] for file_name in selected_files]

    def _fetch_github_files(self):
        url = "https://api.github.com/repos/MEADecarb/st-gis/contents/data"
        response = requests.get(url)
        if response.status_code == 200:
            self.github_files = {file_info['name']: file_info['download_url'] for file_info in response.json() if file_info['name'].endswith(('.csv', '.geojson', '.xlsx', '.zip'))}
            return self.github_files
        else:
            return {}

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
                extension = uploaded_file.name.split(".")[-1]
                if extension in {"csv", "xlsx"}:
                    self._load_tabular_data(uploaded_file, extension)
                else:
                    self._load_geospatial_data(uploaded_file)
        elif self.selected_files:
            for file_url in self.selected_files:
                self._load_data_from_url(file_url)

    def _load_data_from_url(self, url):
        extension = url.split(".")[-1]
        layer_name = url.split('/')[-1].split('.')[0]
        if extension == "geojson":
            self.data_frame = gpd.read_file(url)
            json_data_frame = json.loads(self.data_frame.to_json())
            self._apply_filters()
            self._fit_map_to_bounds(self.data_frame.total_bounds)
            self._add_geojson_layer(json_data_frame, layer_name)
        elif extension in {"csv", "xlsx"}:
            self._load_tabular_data_from_url(url, extension)
        else:
            st.write("Unsupported URL format or unable to load data.")

    def _load_tabular_data(self, file, extension):
        if extension == "csv":
            self.data_frame = pd.read_csv(file)
        else:
            self.data_frame = pd.read_excel(file, engine="openpyxl")

        self.latitude_column, self.longitude_column = self._select_lat_long_columns()
        self.data_frame = gpd.GeoDataFrame(
            self.data_frame,
            geometry=gpd.points_from_xy(
                self.data_frame[self.longitude_column],
                self.data_frame[self.latitude_column],
            ),
            crs="wgs84",
        ).dropna(subset=[self.longitude_column, self.latitude_column])

        self._apply_filters()
        self._fit_map_to_bounds(self.data_frame.total_bounds)
        self._add_markers()
        folium.LayerControl().add_to(self.map)

    def _load_tabular_data_from_url(self, url, extension):
        if extension == "csv":
            self.data_frame = pd.read_csv(url)
        else:
            self.data_frame = pd.read_excel(url, engine="openpyxl")

        self.latitude_column, self.longitude_column = self._select_lat_long_columns()
        self.data_frame = gpd.GeoDataFrame(
            self.data_frame,
            geometry=gpd.points_from_xy(
                self.data_frame[self.longitude_column],
                self.data_frame[self.latitude_column],
            ),
            crs="wgs84",
        ).dropna(subset=[self.longitude_column, self.latitude_column])

        self._apply_filters()
        self._fit_map_to_bounds(self.data_frame.total_bounds)
        self._add_markers()
        folium.LayerControl().add_to(self.map)

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

    def _load_geospatial_data(self, file):
        self.data_frame = gpd.read_file(file)
        layer_name = file.name.split(".")[0]
        json_data_frame = json.loads(self.data_frame.to_json())
        self._apply_filters()
        self._fit_map_to_bounds(self.data_frame.total_bounds)
        self._add_geojson_layer(json_data_frame, layer_name)

    def _fit_map_to_bounds(self, bounds):
        self.map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def _add_markers(self):
        for _, row in self.data_frame.iterrows():
            popup_html = self.create_popup_html(row[:-1])
            folium.Marker(
                location=[row[self.latitude_column], row[self.longitude_column]],
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(self.marker_cluster)

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

    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        st.sidebar.markdown("## Data Manipulation")
        options = ["Select column"]
        unique_values = ["Select value"]

        for column in df.columns:
            options.append(column)

        input_column = st.sidebar.selectbox("Choose column:", options)

        if input_column != options[0]:
            if df[input_column].dtype == "O":
                unique_values.extend(df[input_column].unique())
                uvalue = st.sidebar.multiselect("Select value:", unique_values)
                if uvalue != unique_values[0]:
                    df = df[df[input_column].isin(uvalue)]
            else:
                uvalue = st.sidebar.slider(
                    "Select a range of values",
                    float(df[input_column].min()),
                    float(df[input_column].max()),
                    (float(df[input_column].min()), float(df[input_column].max())),
                )
                df = df[(df[input_column] >= uvalue[0]) & (df[input_column] <= uvalue[1])]
        return df

    def _apply_filters(self):
        self.data_frame = self.filter_dataframe(self.data_frame)

    def create_popup_html(self, properties):
        html = "<div style='max-height: 200px; overflow-y: auto;'>"
        for key, value in properties.items():
            html += f"<b>{key}</b>: {value}<br>"
        html += "</div>"
        return html

    def _display_layout(self):
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("## Map")
            folium_static(self.map, width=700, height=500)

        with col2:
            st.markdown("## DataFrame")
            st.dataframe(self.data_frame.drop(columns="geometry"))
            st.download_button(
                label="Download data as CSV",
                data=self.data_frame.to_csv().encode("utf-8"),
                file_name="Streamlit_df.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    app = GeoDataManipulator()
    app._display_layout()
