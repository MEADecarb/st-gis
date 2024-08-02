import streamlit as st

# Configure the main page
st.set_page_config(
    page_title="Geospatial Tools",
    page_icon="🌍",
    layout="wide",
)

# Sidebar content
st.sidebar.markdown("# Main Page")
st.sidebar.info(
    """
    GitHub repository: [Streamlit Geospatial Tools](https://github.com/MEADecarb/st-gis/)
    """
)
st.sidebar.markdown("# Contact")
st.sidebar.info(
    """
    - [Maryland Energy Administration](https://energy.maryland.gov/Pages/default.aspx)
    """
)


# About section
st.markdown("## About")

st.write(
    """
    Welcome to the Data Explorer application! This tool is designed to help users visualize and interact with geospatial and tabular data in a seamless and intuitive way. Below is a description of the available pages and their functionalities:
    """
)

st.markdown("### Vector Data Visualization 📊")

st.write(
    """
    **Purpose:**
    The Vector Data Visualization page allows users to upload, select, and explore various vector data formats such as CSV, XLSX, ZIP, and GEOJSON. This page is ideal for visualizing geospatial data points, lines, and polygons on an interactive map.

    **Key Features:**
    - **Upload Files**: Users can upload their own files in supported formats (CSV, XLSX, ZIP, GEOJSON).
    - **Select Pre-uploaded Files**: Users can choose from a set of pre-uploaded files available via a dropdown menu.
    - **View Interactive Map**: The map updates automatically to display data from the selected or uploaded files.
    - **Data Table**: The data associated with the map is displayed in a table below the map for easy viewing and analysis.
    """
)

st.markdown("### Data Manipulation 📊")

st.write(
    """
    **Purpose:**
    The Data Manipulation page provides users with tools to perform detailed analysis and manipulation of their data. This page is perfect for users who need to filter, transform, and export data for further analysis.

    **Key Features:**
    - **Upload and Select Files**: Similar to the Vector Data Visualization page, users can upload their own files or select from pre-uploaded options.
    - **Advanced Filtering**: Users can apply complex filters to the data to isolate specific subsets based on custom criteria.
    - **Interactive Map and Data Table**: The map and data table are dynamically linked, allowing users to see the impact of their filters in real-time.
    - **Download Filtered Data**: After manipulating the data, users can download the filtered dataset as a CSV file.
    """
)

st.markdown("### How to Use")

st.write(
    """
    1. **Uploading Files**: Navigate to the desired page and use the file uploader to add your data files. Supported formats include CSV, XLSX, ZIP, and GEOJSON.
    2. **Selecting Pre-uploaded Files**: If you prefer, select from the list of available pre-uploaded files using the dropdown menu.
    3. **Viewing the Map**: The interactive map will automatically update to display the data from your selected or uploaded files.
    4. **Filtering Data**: Use the sidebar options to filter the data based on specific columns and values. This feature helps in focusing on the data points that matter most to you.
    5. **Downloading Data**: Once you are satisfied with your data visualization and filtering, use the download button to export the data as a CSV file.
    6. **Exploring the Data Table**: Scroll down to view the data table associated with the map. This table provides a detailed view of your data and can be used for further analysis.
    
    This application is built to be user-friendly and versatile, catering to both novice and advanced users who need to work with geospatial and tabular data. We hope you find it useful for your data exploration and analysis needs!
    """
)
st.write(
    """
    ### 💻 Used Technology:
    - Streamlit
    - Pandas
    - Geopandas
    - Folium
    """
)
