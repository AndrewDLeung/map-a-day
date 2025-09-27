# %%

from pygris import tracts
from pygris.data import get_census
from pygris.utils import erase_water
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import folium

nyc_counties = [
    "Bronx",
    "Kings",
    "New York",
    "Queens",
    "Richmond",
]

nyc_tracts = tracts(state="NY", county=nyc_counties, cb=False, year=2022)

nyc_tracts = erase_water(nyc_tracts)

nyc_commute = get_census(
    dataset="acs/acs5",
    variables=[
        "B08013_001E",  # total min commuted by sex per tract
        "B08303_001E",  # total respondents for min commuted by sex
        "B08301_002E",  # car, truck, or van
        "B08301_011E",  # bus
        "B08301_012E",  # subway
        "B08301_013E",  # commuter rail
        "B08301_015E",  # ferry boat
        "B08301_016E",  # taxi
        "B08301_017E",  # motorcycle
        "B08301_018E",  # biked
        "B08301_019E",  # walked
        "B08301_020E",  # other
        "B08301_001E",  # total means of transportation respondents
        "B08303_002E",  # < 5min
        "B08303_003E",  # 5 - 9 min
        "B08303_004E",
        "B08303_005E",
        "B08303_006E",
        "B08303_007E",
        "B08303_008E",
        "B08303_009E",
        "B08303_010E",
        "B08303_011E",  # 45 - 59 min
        "B08303_012E",  # 60 - 89 min
        "B08303_013E",  # 90+ min
    ],
    # Total min travel per tract, Total respondents by tract, commute time, uses car
    # uses bus, uses train, uses bike, walked
    params={
        "for": "tract:*",
        "in": "state:36 county:005,047,061,081,085",
        # New York State = 36, Bronx=005, Kings=047, New York=061, Queens=081, Richmond=085
    },
    year=2022,
    return_geoid=True,
    guess_dtypes=True,
)

nyc_commute["mean_commute_time"] = (
    nyc_commute["B08013_001E"] / nyc_commute["B08303_001E"]
)

mode_columns = nyc_commute.columns[2:12]

for col in mode_columns:
    new_col = f"estimated_{col}_share"
    nyc_commute[new_col] = nyc_commute[col] / nyc_commute["B08301_001E"]

nyc_tracts_merged = pd.merge(nyc_tracts, nyc_commute, on="GEOID", how="left")

conditions = [
    nyc_tracts_merged["GEOID"].str.contains("36005", case=False),
    nyc_tracts_merged["GEOID"].str.contains("36047", case=False),
    nyc_tracts_merged["GEOID"].str.contains("36061", case=False),
    nyc_tracts_merged["GEOID"].str.contains("36081", case=False),
    nyc_tracts_merged["GEOID"].str.contains("36085", case=False),
]

choices = ["The Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]

nyc_tracts_merged["boros"] = np.select(conditions, choices, default="Other")

interactive_nyc_tracts = folium.Map(
    [40.7, -74], zoom_start=10, tiles="cartodb positron"
)

fg1 = folium.FeatureGroup(name="Mean Commute Time (Minutes)", overlay=False).add_to(
    interactive_nyc_tracts
)

commute_time_layer = folium.Choropleth(
    geo_data=nyc_tracts_merged,
    data=nyc_tracts_merged,
    columns=["GEOID", "mean_commute_time"],
    key_on="feature.properties.GEOID",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Mean Commute Time (Minutes)",
    highlight=True,
    name="Mean Commute Time (Minutes)",
    show=False,
).geojson.add_to(fg1)

folium.GeoJson(
    nyc_tracts_merged,
    name="Mean Commute Time (Minutes)",
    style_function=lambda x: {
        "fillColor": "transparent",
        "color": "transparent",
        "weight": 0,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["boros", "GEOID", "mean_commute_time"],
        aliases=["Boroughs:", "Census Tract GEOID:", "Commute Time (min):"],
        localize=True,
    ),
).add_to(commute_time_layer)

mode_names = [
    {"var_code": "B08301_002E", "mode_name": "Car"},
    {"var_code": "B08301_011E", "mode_name": "Bus"},
    {"var_code": "B08301_012E", "mode_name": "Subway"},
    {"var_code": "B08301_015E", "mode_name": "Ferry"},
    {"var_code": "B08301_018E", "mode_name": "Bike"},
    {"var_code": "B08301_019E", "mode_name": "Walk"},
]

fg_list = []

for i, modes in enumerate(mode_names):
    fg = folium.FeatureGroup(
        name=f"Number of {modes['mode_name']} Commuters", overlay=False
    ).add_to(interactive_nyc_tracts)
    fg_list.append(fg)

    commuter_layer = folium.Choropleth(
        geo_data=nyc_tracts_merged,
        data=nyc_tracts_merged,
        columns=["GEOID", modes["var_code"]],
        key_on="feature.properties.GEOID",
        fill_color="YlGn",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f"Number of {modes['mode_name']} Commuters",
        highlight=True,
        name=f"Number of {modes['mode_name']} Commuters",
        show=False,
    ).geojson.add_to(fg)

    folium.GeoJson(
        nyc_tracts_merged,
        name=f"Number of {modes['mode_name']} Commuters",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "transparent",
            "weight": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["boros", "GEOID", modes["var_code"]],
            aliases=[
                "Boroughs:",
                "Census Tract GEOID:",
                f"Number of {modes['mode_name']} Commuters:",
            ],
            localize=True,
        ),
    ).add_to(fg)

folium.TileLayer("cartodb positron", overlay=True, name="Basemap").add_to(
    interactive_nyc_tracts
)

folium.LayerControl(collapsed=True).add_to(interactive_nyc_tracts)

interactive_nyc_tracts

interactive_nyc_tracts.save(
    "/Users/andrew/Desktop/data-science/projects/map-a-day/map-a-day/day_04/interative_nyc_tracts.html"
)


# %%
