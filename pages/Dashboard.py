import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt

# Title of the dashboard
st.title("Geospatial Data Dashboard")

# Load WFS data or GeoJSON from a file based on user selection
data_source = st.sidebar.radio("Select Data Source", ("WFS", "Local GeoJSON"))

if data_source == "WFS":
    # WFS input parameters
    wfs_url = st.text_input("Enter WFS URL", "https://your-wfs-url/wfs")  # Replace with your WFS URL
    layer_name = st.text_input("Enter WFS Layer Name", "your-layer-name")  # Replace with the WFS layer name
    
    if wfs_url and layer_name:
        # Connect to the WFS service
        wfs = WebFeatureService(url=wfs_url, version='1.1.0')
        
        # Fetch the data from the WFS service
        response = wfs.getfeature(typename=layer_name, outputFormat='application/json')
        gdf = gpd.read_file(BytesIO(response.read()))
else:
    # Load geospatial data from a local file
    geojson_file = st.file_uploader("Upload a GeoJSON file", type=["geojson"])
    if geojson_file is not None:
        gdf = gpd.read_file(geojson_file)

# Check if data is loaded
if 'gdf' in locals():
    # Sidebar filters for dynamic selection based on WFS/local data attributes
    st.sidebar.header("Filter Options")
    
    # Dynamically populate the filter based on attributes in the dataset
    columns = gdf.columns.tolist()
    
    location_filter_column = st.sidebar.selectbox("Select filter column", columns)
    unique_values = gdf[location_filter_column].unique()
    location_filter = st.sidebar.selectbox(f"Select a value from {location_filter_column}", unique_values)
    
    # Filter data based on selection
    filtered_gdf = gdf[gdf[location_filter_column] == location_filter]
    
    # Display the map with filtered data
    st.subheader(f"Map for {location_filter}")
    st.map(filtered_gdf)

    # Allow user to select a numeric column for stats
    numeric_columns = gdf.select_dtypes(include='number').columns.tolist()
    if numeric_columns:
        numeric_column = st.sidebar.selectbox("Select a numeric column for stats", numeric_columns)
        
        # Calculate some basic stats
        total_records = len(filtered_gdf)
        avg_metric = filtered_gdf[numeric_column].mean()
        
        # Display metrics
        st.metric(label="Total Records", value=total_records)
        st.metric(label=f"Average {numeric_column}", value=f"{avg_metric:.2f}")
    
        # Display a chart based on a selected categorical column
        category_columns = gdf.select_dtypes(include=['object']).columns.tolist()
        if category_columns:
            category_column = st.sidebar.selectbox("Select a categorical column for chart", category_columns)
            st.subheader("Data Distribution")
            fig, ax = plt.subplots()
            filtered_gdf[category_column].value_counts().plot(kind='bar', ax=ax)
            st.pyplot(fig)
    
    # Allow users to download filtered data
    st.subheader("Download Filtered Data")
    csv = filtered_gdf.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"{location_filter}_data.csv",
        mime="text/csv",
    )
else:
    st.warning("No data available. Please select a data source.")
