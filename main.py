import streamlit as st
import pandas as pd
import json
import folium
from folium.plugins import HeatMap, TimestampedGeoJson
import tempfile
import streamlit.components.v1 as components

# Function to create heatmap
def create_heatmap(data, place_visits):
    heatmap_map = folium.Map(location=[data['startLatitude'].mean(), data['startLongitude'].mean()], zoom_start=12)
    heatmap_data = []

    # Adding activity segments
    for _, row in data.iterrows():
        heatmap_data.append([row['startLatitude'], row['startLongitude'], 1])
        heatmap_data.append([row['endLatitude'], row['endLongitude'], 1])

    # Adding place visits
    for _, row in place_visits.iterrows():
        heatmap_data.append([row['latitude'], row['longitude'], 1])

    HeatMap(heatmap_data).add_to(heatmap_map)
    return heatmap_map

# Function to create time series map
def create_time_series(data, place_visits):
    m = folium.Map(location=[data['startLatitude'].mean(), data['startLongitude'].mean()], zoom_start=12)
    features = []

    # Adding activity segments to features
    for _, row in data.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [row['startLongitude'], row['startLatitude']],
                    [row['endLongitude'], row['endLatitude']]
                ]
            },
            'properties': {
                'times': [row['startTimestamp'].isoformat(), row['endTimestamp'].isoformat()],
                'style': {'color': 'blue'},
                'icon': 'circle',
                'iconstyle': {
                    'fillColor': 'blue',
                    'fillOpacity': 0.6,
                    'stroke': 'true',
                    'radius': 5
                }
            }
        })

    # Adding place visits to features
    for _, row in place_visits.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['longitude'], row['latitude']]
            },
            'properties': {
                'times': [row['startTimestamp'].isoformat(), row['endTimestamp'].isoformat()],
                'style': {'color': 'red'},
                'icon': 'circle',
                'iconstyle': {
                    'fillColor': 'red',
                    'fillOpacity': 0.6,
                    'stroke': 'true',
                    'radius': 5
                }
            }
        })

    timestamped_geo_json = TimestampedGeoJson({
        'type': 'FeatureCollection',
        'features': features,
    }, period='PT1H', add_last_point=True)

    timestamped_geo_json.add_to(m)
    return m

# Streamlit interface
st.title("Google Timeline Data Visualizer")

# Upload JSON file
uploaded_file = st.file_uploader("Choose a JSON file", type="json")

# Option to select visualization type
vis_option = st.selectbox("Select Visualization", ["Heatmap", "Time series"])

if st.button("Submit"):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            
            # Flattening the nested JSON structure for easier manipulation and analysis
            activity_segments = []
            place_visits = []

            for obj in data['timelineObjects']:
                if 'activitySegment' in obj:
                    activity_segment = obj['activitySegment']
                    activity_segments.append({
                        'startLatitude': activity_segment['startLocation']['latitudeE7'] / 1e7,
                        'startLongitude': activity_segment['startLocation']['longitudeE7'] / 1e7,
                        'endLatitude': activity_segment['endLocation']['latitudeE7'] / 1e7,
                        'endLongitude': activity_segment['endLocation']['longitudeE7'] / 1e7,
                        'startTimestamp': activity_segment['duration']['startTimestamp'],
                        'endTimestamp': activity_segment['duration']['endTimestamp'],
                        'distance': activity_segment.get('distance', 'N/A'),
                        'activityType': activity_segment['activityType'],
                        'confidence': activity_segment['confidence'],
                    })
                elif 'placeVisit' in obj:
                    place_visit = obj['placeVisit']
                    place_visits.append({
                        'latitude': place_visit['location']['latitudeE7'] / 1e7,
                        'longitude': place_visit['location']['longitudeE7'] / 1e7,
                        'placeId': place_visit['location']['placeId'],
                        'address': place_visit['location']['address'],
                        'name': place_visit['location'].get('name', 'N/A'),
                        'startTimestamp': place_visit['duration']['startTimestamp'],
                        'endTimestamp': place_visit['duration']['endTimestamp'],
                        'visitConfidence': place_visit['visitConfidence'],
                    })

            activity_segments_df = pd.DataFrame(activity_segments)
            place_visits_df = pd.DataFrame(place_visits)
            activity_segments_df['startTimestamp'] = pd.to_datetime(activity_segments_df['startTimestamp'])
            activity_segments_df['endTimestamp'] = pd.to_datetime(activity_segments_df['endTimestamp'])
            place_visits_df['startTimestamp'] = pd.to_datetime(place_visits_df['startTimestamp'])
            place_visits_df['endTimestamp'] = pd.to_datetime(place_visits_df['endTimestamp'])

            if vis_option == "Heatmap":
                heatmap = create_heatmap(activity_segments_df, place_visits_df)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
                    heatmap.save(tmpfile.name)
                    st.markdown(f"[Download the heatmap map](./{tmpfile.name})")
                    with open(tmpfile.name, 'r') as f:
                        components.html(f.read(), height=600)
            elif vis_option == "Time series":
                time_series_map = create_time_series(activity_segments_df, place_visits_df)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
                    time_series_map.save(tmpfile.name)
                    st.markdown(f"[Download the timeline map](./{tmpfile.name})")
                    with open(tmpfile.name, 'r') as f:
                        components.html(f.read(), height=600)
        except Exception as e:
            st.error(f"Error processing file: {e}")