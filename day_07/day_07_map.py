import geopandas as gp
from bs4 import BeautifulSoup
import requests
import pandas as pd
import folium
import matplotlib.pyplot as plt

df = gp.read_file("data/coder_geo.gpkg")

ax = df.plot(
    column="count",
    scheme="QUANTILES",
    k=5,
    cmap="BuPu",
    legend=True,
    legend_kwds={"loc": "center left", "bbox_to_anchor": (1, 0.5)},
)
ax.set_axis_off()
ax.set_title("Countries with the Most Finalists in Competitive Programmer Competitions")

plt.savefig("programmers.png", dpi=800, bbox_inches="tight")
