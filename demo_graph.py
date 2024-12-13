import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static

def set_custom_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

@st.cache_data
def load_data(file_path='merged_gdf_specific.pkl'):
    try:
        gdf = gpd.read_file('merged_gdf_filtered.gpkg')
    except FileNotFoundError:
        st.error(f"Data file not found at path: {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()
    return gdf

def generate_map(gdf):
    m = folium.Map(location=[37.8, -96], zoom_start=4)

    def create_html_content(row):
        pyramid_img = row['Population_Pyramid']
        third_img = row['Third_BarChart']
        district_name = row.get('NAME', 'Unknown District')

        pyramid_section = f"<img src='data:image/png;base64,{pyramid_img}' style='width:280px;height:400px;'>" if pyramid_img else "<p>No population pyramid data</p>"
        third_section = f"<img src='data:image/png;base64,{third_img}' style='width:280px;height:150px;'>" if third_img else "<p>No third data</p>"

        html = f"""
        <div style="width:300px;">
            <h4>{district_name}</h4>
            {pyramid_section}
            <h5>Additional Data Set</h5>{third_section}
        </div>
        """
        return html

    # Simple uniform style function
    def style_function(feature):
        return {
            'fillColor': '#3186cc',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7,
        }

    for idx, row in gdf.iterrows():
        if row['geometry'] is None:
            continue

        html_content = create_html_content(row)
        iframe = folium.IFrame(html=html_content, width=320, height=600)
        popup = folium.Popup(iframe, max_width=320)

        properties = row.drop(['geometry', 'Population_Pyramid', 'Third_BarChart'], errors='ignore').to_dict()
        feature = {
            'type': 'Feature',
            'properties': properties,
            'geometry': row['geometry'].__geo_interface__
        }

        folium.GeoJson(
            feature,
            style_function=style_function,
            highlight_function=lambda x: {'weight':3, 'color':'blue'},
            tooltip=folium.Tooltip(row.get('NAME', 'Unknown District')),
            popup=popup
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m

def main():
    set_custom_style()
    gdf = load_data()

    # No generation of charts needed, they are already in the gdf
    # Check if columns exist (optional)
    if 'Population_Pyramid' not in gdf.columns or 'Third_BarChart' not in gdf.columns:
        st.error("Required image columns not found in the data.")
        st.stop()

    # Generate the map without variable-based coloring
    folium_map = generate_map(gdf)
    folium_static(folium_map, width=1200, height=800)

    st.markdown("---")
    st.markdown("**Data Source:** 2020 Census API | **App Developed by:** Your Name")

if __name__ == "__main__":
    main()
