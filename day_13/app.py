import streamlit as st
import gpxpy
import gzip
import pandas as pd
import geopandas as gp
from shapely.geometry import LineString
import matplotlib.pyplot as plt
import io
import xml.etree.ElementTree as ET
import math

st.title('Strava Maps')

uploaded_file = st.file_uploader("Upload your Strava file (.gpx, .tcx, or .gz)", type=["gpx", "tcx", "gz"])

strava_routes = []
route_info = []

if uploaded_file is not None:

    content = uploaded_file.read()
    if uploaded_file.name.endswith('.gpx.gz'):
        with gzip.open(io.BytesIO(content), 'rt') as f:
            gpx_content = f.read()
            gpx = gpxpy.parse(gpx_content)
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    route_info.append({
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation
                    })


    elif uploaded_file.name.endswith('.gpx'):
        gpx = gpxpy.parse(io.StringIO(content.decode('utf-8')))
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    route_info.append({
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation
                    })
    elif uploaded_file.name.endswith('.tcx.gz') or uploaded_file.name.endswith('.tcx'):
        with gzip.open(io.BytesIO(content), 'rt') as f:
            tcx_content = f.read()
            tree = ET.ElementTree(ET.fromstring(tcx_content))
        
        root = tree.getroot()
        namespace_uri = root.tag.split('}')[0].strip('{')
        ns = {'tcx': namespace_uri}

        for tp in root.findall('.//tcx:Trackpoint', ns):
            pos = tp.find('tcx:Position', ns)
            ele = tp.find('tcx:AltitudeMeters', ns)

            lat = lon = None
            if pos is not None:
                lat = pos.find('tcx:LatitudeDegrees', ns)
                lon = pos.find('tcx:LongitudeDegrees', ns)

            if lat is not None and lon is not None:
                route_info.append({
                    'latitude': float(lat.text),
                    'longitude': float(lon.text),
                    'elevation': float(ele.text) if ele is not None else None
                })
    else:
        st.error("Unsupported file type. Please upload a .gpx, .tcx, or .gz file.")
        st.stop()

if route_info:
        route_df = pd.DataFrame(route_info)

        if {"latitude", "longitude"}.issubset(route_df.columns):
            route_gdf = gp.GeoDataFrame(
                route_df,
                geometry=gp.points_from_xy(route_df["longitude"], route_df["latitude"]),
                crs="EPSG:4326"
            )
            route_line = LineString(route_gdf.geometry.tolist())

            strava_routes.append(route_line)
else:
    print("No route points found.")

strava_routes_gdf = gp.GeoDataFrame(geometry=strava_routes, crs="EPSG:4326")

n_routes = len(strava_routes_gdf)

if n_routes == 0:
    st.write("No routes to display.")
    st.stop()
else:
    n_cols = math.ceil(math.sqrt(n_routes))
    n_rows = math.ceil(n_routes / n_cols)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 15))

    for routes, ax in zip(strava_routes_gdf.geometry, axes.flatten()):
        gp.GeoDataFrame(geometry=[routes], crs="EPSG:4326").plot(ax=ax, linewidth=2, color='orange')
        ax.set_axis_off()

    plt.tight_layout()
    plt.show()
