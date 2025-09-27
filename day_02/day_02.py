# %%

from pygris import tracts
from pygris.data import get_census
from pygris.utils import erase_water
import pandas as pd
import matplotlib.pyplot as plt


nyc_counties = [
    "Bronx",
    "Kings",
    "New York",
    "Queens",
    "Richmond",
]

nyc_tracts = tracts(state="NY", county=nyc_counties, cb=False, year=2022)

print(nyc_tracts.head(10))

nyc_tracts = erase_water(nyc_tracts)


# %%
