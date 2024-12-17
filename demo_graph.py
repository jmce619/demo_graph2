import streamlit as st
import geopandas as gpd
import pandas as pd
import altair as alt
import json

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    gdf = gpd.read_file('merged_gdf_raw.gpkg')
    gdf = gdf.to_crs(epsg=4326)
    return gdf

gdf = load_data()

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

geojson = json.loads(gdf.to_json())
geo_data = alt.Data(values=geojson['features'])

bar_data = gdf[["GEOID"] + bar_vars].copy()
bar_data = bar_data.melt(id_vars='GEOID', var_name='variable', value_name='value')
bar_data['properties.GEOID'] = bar_data['GEOID']

def classify_gender(var):
    if var.startswith('Male'):
        return 'Male'
    elif var.startswith('Female'):
        return 'Female'
    else:
        return 'Other'

bar_data['gender'] = bar_data['variable'].apply(classify_gender)

# Remove "Male " and "Female " prefixes from age variables
bar_data['age_group'] = bar_data['variable'].str.replace('Male ', '', regex=False).str.replace('Female ', '', regex=False)

# Create a selection for the map
selection = alt.selection_single(fields=['properties.GEOID'], empty='none')

map_chart = (
    alt.Chart(geo_data)
    .mark_geoshape(stroke='black', strokeWidth=0.5)
    .encode(
        color=alt.condition(selection, alt.value('steelblue'), alt.value('lightgray')),
        tooltip=['properties.NAME:N', 'properties.GEOID:N']
    )
    .add_selection(selection)
    .project(type='albersUsa')
    .properties(width=400, height=300)
)

# For the pyramid chart, find the max population among Male and Female to set fixed x domain
max_val = bar_data.loc[bar_data['gender'].isin(['Male','Female']), 'value'].max()
# Make male values negative
bar_data['adj_value'] = bar_data.apply(lambda row: (-1)*row['value'] if row['gender']=='Male' else row['value'], axis=1)

# Sort age groups (use the female_age list as a reference for sorting)
age_order = [age.replace('Female ', '') for age in variables_set_female_age]

pyramid_chart = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        y=alt.Y('age_group:N', sort=age_order, title='Age Group', axis=alt.Axis(orient='right')),
        x=alt.X('adj_value:Q', title='Population', scale=alt.Scale(domain=[-max_val, max_val])),
        color=alt.Color('gender:N', scale=alt.Scale(domain=['Male', 'Female'], range=['blue', 'pink'])),
        tooltip=['age_group:N', 'value:Q', 'gender:N']
    )
    .transform_filter(selection)
    .transform_filter(alt.datum.gender != 'Other')
    .properties(width=300, height=250)
)


# Add a vertical rule at x=0
rule = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(color='black').encode(x='x:Q')
pyramid_combined = alt.layer(pyramid_chart, rule).resolve_scale(x='shared', y='shared')

# The third bar chart with each bar a different color
bars_third_chart = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        x=alt.X('variable:N', title='Race/Ethnicity'),
        y=alt.Y('value:Q',title=None),
        # Color each bar by its variable name for distinct colors
        color=alt.Color('variable:N', title='Race', scale=alt.Scale(scheme='category20')),
        tooltip=['variable:N', 'value:Q']
    )
    .transform_filter(selection)
    .transform_filter(alt.datum.gender == 'Other')
    .properties(width=180, height=180)
)

final_chart = alt.vconcat(
    alt.hconcat(map_chart, bars_third_chart),
    pyramid_combined
).configure_concat(spacing=5).resolve_scale(color='independent')


st.altair_chart(final_chart)
