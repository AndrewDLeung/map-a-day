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

def parse_gpx(uploaded_file):

    route_info = []
    content = uploaded_file.read()

    if uploaded_file.name.endswith('.gpx.gz'):

        with gzip.open(io.BytesIO(content), 'rt') as f:
            gpx_content = f.read()
            gpx = gpxpy.parse(gpx_content)

    else:
        gpx = gpxpy.parse(io.StringIO(content.decode('utf-8')))
        
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                route_info.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation
                })
    return route_info

def parse_tcx(uploaded_file):
    
    route_info = []
    content = uploaded_file.read()

    if uploaded_file.name.endswith('.tcx.gz'):
        with gzip.open(io.BytesIO(content), 'rt') as f:
            tcx_content = f.read().lstrip() 
    else:
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

    return route_info

def parse_fit(uploaded_file):

    route_info = []
    content = uploaded_file.read()

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
    return route_info