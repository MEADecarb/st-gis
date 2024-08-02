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
    - [Maryland Energy Administration](hhttps://energy.maryland.gov/Pages/default.aspx)
    """
)

# Main page content
st.markdown("## 🚀 lorum ipsum")
st.write(
    """
   lorum ipsum
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
