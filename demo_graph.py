import streamlit as st
import geopandas as gpd
import pandas as pd
import altair as alt
import json

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    # Load raw gdf (ensure it has 'GEOID', 'NAME', and the needed variables)
    gdf = gpd.read_file('merged_gdf_raw.gpkg')
    gdf = gdf.to_crs(epsg=4326)
    return gdf

gdf = load_data()

# Define variable sets
variables_set_female_age = [
   'Female Under 5 years',
   'Female 5 to 9 years',
   'Female 10 to 14 years',
   'Female 15 to 17 years',
   'Female 18 and 19 years',
   'Female 20 years',
   'Female 21 years',
   'Female 22 to 24 years',
   'Female 25 to 29 years',
   'Female 30 to 34 years',
   'Female 35 to 39 years',
   'Female 40 to 44 years',
   'Female 45 to 49 years',
   'Female 50 to 54 years',
   'Female 55 to 59 years',
   'Female 60 and 61 years',
   'Female 62 to 64 years',
   'Female 65 and 66 years',
   'Female 67 to 69 years',
   'Female 70 to 74 years',
   'Female 75 to 79 years',
   'Female 80 to 84 years',
   'Female 85 years and over'
]
variables_set_male_age = [
   'Male Under 5 years',
   'Male 5 to 9 years',
   'Male 10 to 14 years',
   'Male 15 to 17 years',
   'Male 18 and 19 years',
   'Male 20 years',
   'Male 21 years',
   'Male 22 to 24 years',
   'Male 25 to 29 years',
   'Male 30 to 34 years',
   'Male 35 to 39 years',
   'Male 40 to 44 years',
   'Male 45 to 49 years',
   'Male 50 to 54 years',
   'Male 55 to 59 years',
   'Male 60 and 61 years',
   'Male 62 to 64 years',
   'Male 65 and 66 years',
   'Male 67 to 69 years',
   'Male 70 to 74 years',
   'Male 75 to 79 years',
   'Male 80 to 84 years',
   'Male 85 years and over'
]
variables_set_third = [
 
   'Black or African American alone',
   'American Indian and Alaska Native alone',
   'Asian alone',
   'Native Hawaiian and Other Pacific Islander alone',
   'Some Other Race alone',
   'Population of two or more races:',
   'Population of two races:',
   'White; Black or African American',
   'White; American Indian and Alaska Native',
   'White; Asian',
   'White; Native Hawaiian and Other Pacific Islander',
   'White; Some Other Race',
   'Black or African American; American Indian and Alaska Native',
   'Black or African American; Asian',
   'Black or African American; Native Hawaiian and Other Pacific Islander',
   'Black or African American; Some Other Race',
   'American Indian and Alaska Native; Asian',
   'American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander',
   'American Indian and Alaska Native; Some Other Race',
   'Asian; Native Hawaiian and Other Pacific Islander',
   'Asian; Some Other Race',
   'Native Hawaiian and Other Pacific Islander; Some Other Race',
]

bar_vars = variables_set_female_age + variables_set_male_age + variables_set_third

if not all(var in gdf.columns for var in bar_vars):
    st.write("Columns in the GeoDataFrame:", gdf.columns)
    st.stop()

# Convert GeoDataFrame to a GeoJSON-like dict
geojson = json.loads(gdf.to_json())
geo_data = alt.Data(values=geojson['features'])

# Melt the variables into a tidy DataFrame for the bar chart
bar_data = gdf[["GEOID"] + bar_vars].copy()
bar_data = bar_data.melt(id_vars='GEOID', var_name='variable', value_name='value')

# Important: The map selection will reference 'properties.GEOID'.
# We need to have the same field name in bar_data to allow filtering.
bar_data['properties.GEOID'] = bar_data['GEOID']

# Create a new column that classifies variables as Male, Female, or Other
def classify_gender(var):
    if var.startswith('Male'):
        return 'Male'
    elif var.startswith('Female'):
        return 'Female'
    else:
        return 'Other'

bar_data['gender'] = bar_data['variable'].apply(classify_gender)

# Create a single selection that uses 'properties.GEOID' as the key
selection = alt.selection_single(
    fields=['properties.GEOID'],
    on='click',
    empty='none'
)

# Create the polygon map chart
map_chart = (
    alt.Chart(geo_data)
    .mark_geoshape(stroke='black', strokeWidth=0.5)
    .encode(
        color=alt.condition(selection, alt.value('steelblue'), alt.value('lightgray')),
        tooltip=['properties.NAME:N', 'properties.GEOID:N']  # tooltips on hover
    )
    .add_selection(selection)
    .project(type='albersUsa')
    .properties(width=600, height=400)
)

# Create the bar chart linked to the selection
bars = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        x=alt.X('variable:N', title='Variable'),
        y=alt.Y('value:Q', title='Value'),
        tooltip=['variable:N', 'value:Q'],
        # Set color based on gender classification
        color=alt.Color('gender:N', 
                        scale=alt.Scale(
                            domain=['Male', 'Female', 'Other'],
                            range=['blue', 'pink', 'gray']  # 'Other' gets gray as a fallback
                        ))
    )
    .transform_filter(selection)  # Only show data for the selected district
    .properties(width=600, height=200)
)


# Display the charts in Streamlit.
st.altair_chart(map_chart & bars, use_container_width=True)
