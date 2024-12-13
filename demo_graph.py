import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import base64
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
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
def load_data(file_path='merged_gdf_raw.gpkg'):
    # Load the geopackage with raw numeric data only
    try:
        gdf = gpd.read_file(file_path)
    except FileNotFoundError:
        st.error(f"Data file not found at path: {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()
    return gdf

# Define your variable sets and label dictionaries (customize as needed)
female_vars = ["P12_027N","P12_028N","P12_029N","P12_030N","P12_031N","P12_032N","P12_033N","P12_034N","P12_035N","P12_036N","P12_037N","P12_038N","P12_039N","P12_040N","P12_041N","P12_042N","P12_043N","P12_044N","P12_045N","P12_046N","P12_047N","P12_048N","P12_049N"]
male_vars = ["P12_003N","P12_004N","P12_005N","P12_006N","P12_007N","P12_008N","P12_009N","P12_010N","P12_011N","P12_012N","P12_013N","P12_014N","P12_015N","P12_016N","P12_017N","P12_018N","P12_019N","P12_020N","P12_021N","P12_022N","P12_023N","P12_024N","P12_025N"]
third_vars = ["P10_003N","P10_004N","P10_005N","P10_006N","P10_007N","P10_008N","P10_009N","P10_010N","P10_011N","P10_012N","P10_013N","P10_014N","P10_015N","P10_016N","P10_017N","P10_018N","P10_019N","P10_020N","P10_021N","P10_022N","P10_023N","P10_024N","P10_025N"]

variable_labels = {
    # Provide human-readable labels for your variable codes
    # Example: "P12_027N": "Female Age 0-4", etc.
    # Fill in the actual labels as appropriate
}

def generate_population_pyramid_chart(row, female_vars, male_vars, labels_dict):
    """
    Create a population pyramid: male on left (negative x) and female on right (positive x).
    """
    female_values = [row[v] for v in female_vars if v in row and pd.notna(row[v])]
    male_values = [row[v] for v in male_vars if v in row and pd.notna(row[v])]

    if len(female_values) == 0 and len(male_values) == 0:
        return None

    length = min(len(female_values), len(male_values))
    female_values = female_values[:length]
    male_values = male_values[:length]

    female_values = np.array(female_values)
    male_values = np.array(male_values)
    female_labels = [labels_dict.get(v, v) for v in female_vars][:length]

    plt.figure(figsize=(6, 8))
    y_positions = np.arange(length)

    # Male: negative side, Female: positive side
    plt.barh(y_positions, -male_values, color='skyblue', label='Male')
    plt.barh(y_positions, female_values, color='pink', label='Female')

    plt.yticks(y_positions, female_labels)
    plt.xlabel('Population Count')
    district_name = row.get('NAME', 'Unknown District')
    plt.title(district_name)

    plt.axvline(0, color='black')

    max_val = max(male_values.max() if len(male_values) > 0 else 0,
                  female_values.max() if len(female_values) > 0 else 0)
    plt.xlim(-max_val, max_val)

    plt.legend()
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generate_third_chart(row, third_vars, labels_dict):
    """
    Simple vertical bar chart for the third data set.
    """
    values = [row[v] for v in third_vars if v in row and pd.notna(row[v])]
    if not values:
        return None

    labels = [labels_dict.get(var, var) for var in third_vars]

    plt.figure(figsize=(14, 12))
    plt.bar(labels, values, color='teal')
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.ylabel('Count', fontsize=14)
    plt.title('Ethnic Breakdown', fontsize=14)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generate_map(gdf):
    m = folium.Map(location=[37.8, -96], zoom_start=4)

    def create_html_content(row):
        # Generate charts on-the-fly
        pyramid_img = generate_population_pyramid_chart(row, female_vars, male_vars, variable_labels)
        third_img = generate_third_chart(row, third_vars, variable_labels)

        district_name = row.get('NAME', 'Unknown District')

        # Embed the images if they exist
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

        properties = row.drop('geometry', errors='ignore').to_dict()
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

    # Now gdf no longer has 'Population_Pyramid' or 'Third_BarChart' columns
    # They are generated dynamically.

    folium_map = generate_map(gdf)
    folium_static(folium_map, width=1200, height=800)

    st.markdown("---")
    st.markdown("**Data Source:** 2020 Census API | **App Developed by:** Your Name")

if __name__ == "__main__":
    main()
