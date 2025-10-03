# %%
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

tim_hortons = gpd.read_file("data/geocoded-all_tims_across_canada-2024-10-13.geojson")
canada = gpd.read_file("data/lpr_000b21a_e/lpr_000b21a_e.shp")

tim_hortons = tim_hortons.to_crs(epsg=3347)
canada = canada.to_crs(epsg=3347)

font_path = "/System/Library/Fonts/HelveticaNeue.ttc"
custom_font_prop = fm.FontProperties(fname=font_path)

fig, ax = plt.subplots(figsize=(12, 12))
canada.plot(ax=ax, color="white", edgecolor="black", linewidth=0.4)
tim_hortons.plot(ax=ax, color="#C8102E", alpha=0.5)
ax.set_axis_off()
ax.set_title("Tim Horton's Locations in Canada", fontproperties=custom_font_prop)

plt.savefig(
    "/Users/andrew/Desktop/data-science/projects/map-a-day/map-a-day/day_05/tims_map.png"
)
# %%
