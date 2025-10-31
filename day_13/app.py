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
import numpy as np
import fitdecode
from io import BytesIO

st.title('Plot My Runs')

col1, col2 = st.columns(2, border=True)

col1.write("""For Strava users: 

- Log into Strava.com on desktop.
- Hover over your name in the upper right-hand corner of the Strava page. 
- Choose "Settings" > "My Account" tab.
- Select “Get Started” under “Download or Delete Your Account.”
- Select “Request your archive”.
- You will receive an email with a link to download your data (this may take a few hours.)
- If you signed up via Facebook, the email address is the same as the one linked to your Facebook account.
""")

col2.write("""For Garmin users:
- Go to Garmin Account Data Management on desktop.
- Sign in.
- Select "Export Your Data".
- Select "Request Data Export".
         """)

uploaded_files = st.file_uploader("Upload your activity files", type=["gpx", "tcx", "gz","fit"], accept_multiple_files=True)

strava_routes = []

for uploaded_file in uploaded_files:

    content = uploaded_file.read()
    route_info = []

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
    elif uploaded_file.name.endswith('.tcx.gz'):
        with gzip.open(io.BytesIO(content), 'rt') as f:
            tcx_content = f.read().lstrip() 
            tree = ET.ElementTree(ET.fromstring(tcx_content))
        
        root = tree.getroot()
        namespace_uri = root.tag.split('}')[0].strip('{')
        ns = {'tcx': namespace_uri}

        found_point = False

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
                found_point = True

        if not found_point:
            st.warning(f"No valid trackpoints in file: {uploaded_file.name}")
            continue
    elif uploaded_file.name.endswith('.tcx'):
        tcx_content = content.decode('utf-8').lstrip() 
        tree = ET.ElementTree(ET.fromstring(tcx_content))
        
        root = tree.getroot()
        namespace_uri = root.tag.split('}')[0].strip('{')
        ns = {'tcx': namespace_uri}

        found_point = False

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
                found_point = True

        if not found_point:
            st.warning(f"No valid trackpoints in file: {uploaded_file.name}")
            continue
    elif uploaded_file.name.endswith(('.fit','.fit.gz')):
        file_obj = gzip.open(io.BytesIO(content), 'rb') if uploaded_file.name.endswith('.gz') else io.BytesIO(content)
        with fitdecode.FitReader(file_obj) as fit_reader:
                for frame in fit_reader:
                    if frame.frame_type == fitdecode.FIT_FRAME_DATA and frame.name == "record":
                        record_data = {field.name: field.value for field in frame.fields}

                        lat_raw = record_data.get("position_lat")
                        lon_raw = record_data.get("position_long")

                        if lat_raw is None or lon_raw is None:
                            continue

                        lat = lat_raw * (180 / 2**31)
                        lon = lon_raw * (180 / 2**31)

                        route_info.append({
                            "latitude": lat,
                            "longitude": lon,
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

st.write(f"Total routes processed: {len(strava_routes_gdf)}")

line_color = st.color_picker("Pick a Line Color", "#00f900")
background_color = st.color_picker("Pick Background Color", "#FFFFFF")

n_routes = len(strava_routes_gdf)


if n_routes == 0:
    st.write("No routes to display.")
    st.stop()
elif st.button("Plot my routes!"):
    if len(uploaded_files) == 1:
        st.write("Plotting single route...")
        fig, ax = plt.subplots(figsize=(12, 12))
        strava_routes_gdf.plot(ax=ax, linewidth=2, color=line_color)
        ax.set_axis_off()
        ax.set_facecolor(background_color)
        st.pyplot(fig)
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        st.download_button(
                label="Download Plot",
                data=img_buffer,
                file_name="my_strava_plot.png",
                mime="image/png"
            )

    elif len(uploaded_files) > 1:
        st.write("Plotting multiple route...")
        n_cols = math.ceil(math.sqrt(n_routes)) + 1
        n_rows = math.ceil(n_routes / n_cols)
        st.write(f"Calculated grid: {n_rows} rows x {n_cols} cols")

        fig_width = max(12, n_cols * 3)
        fig_height = max(8, n_rows * 3)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height), facecolor=background_color)
        st.write(f"Figure size: {fig_width} x {fig_height}")
        
        if isinstance(axes, np.ndarray):
            axes = axes.flatten()
        else:
            axes = [axes]

        for routes, ax in zip(strava_routes_gdf.geometry, axes):
            gp.GeoDataFrame(geometry=[routes], crs="EPSG:4326").plot(ax=ax, linewidth=2, color=line_color)
            ax.set_axis_off()
        
        for ax in axes[n_routes:]:
            ax.set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)

        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        st.download_button(
                label="Download Plot",
                data=img_buffer,
                file_name="my_strava_plot.png",
                mime="image/png"
            )

    


