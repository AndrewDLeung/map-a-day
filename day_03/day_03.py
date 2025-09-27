from pygris import tracts
from pygris.data import get_census
from pygris.utils import erase_water
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    variables=["B08013_001E", "B08303_001E"],
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

nyc_tracts_merged = pd.merge(nyc_tracts, nyc_commute, on="GEOID", how="left")

print(nyc_tracts_merged.head(20))

fig, ax = plt.subplots(figsize=(12, 12))

nyc_tracts_merged.plot(
    column="mean_commute_time",
    cmap="viridis",
    legend=True,
    ax=ax,
    missing_kwds={"color": "lightgray", "label": "No Data"},
    facecolor="#e3ecfa",
    legend_kwds={
        "label": "Mean Travel Time (minutes)",
        "orientation": "horizontal",  # "horizontal" works too
        "shrink": 0.5,  # scales legend size
        "location": "bottom",
    },
)


ax.set_title(
    "Mean Commute Time by Census Tract - NYC",
    fontsize=16,
    loc="left",
    fontname="Helvetica",
)
ax.axis("off")
fig.set_facecolor("#e3ecfa")

plt.savefig(
    "/Users/andrew/Desktop/data-science/projects/map-a-day/map-a-day/day_03/nyc_commute_time_by_tract.png",
    dpi=600,
    bbox_inches="tight",
)
