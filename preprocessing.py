import json
import pandas as pd

# Load the JSON data
with open('2024_MAY.json') as f:
    data = json.load(f)

# Adjusting the code to handle missing 'distance' fields
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
            'distance': activity_segment.get('distance', 'N/A'),  # Using .get() to handle missing 'distance'
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
            'name': place_visit['location'].get('name', 'N/A'),  # Using .get() to handle missing 'name'
            'startTimestamp': place_visit['duration']['startTimestamp'],
            'endTimestamp': place_visit['duration']['endTimestamp'],
            'visitConfidence': place_visit['visitConfidence'],
        })

# Convert to DataFrame
activity_segments_df = pd.DataFrame(activity_segments)
place_visits_df = pd.DataFrame(place_visits)

import ace_tools as tools; tools.display_dataframe_to_user(name="Activity Segments", dataframe=activity_segments_df)
import ace_tools as tools; tools.display_dataframe_to_user(name="Place Visits", dataframe=place_visits_df)

activity_segments_df.head(), place_visits_df.head()

# ====================================================
# Time-Series version

import folium
from folium.plugins import TimestampedGeoJson
import json

# Creating the map
m = folium.Map(location=[activity_segments_df['startLatitude'].mean(), activity_segments_df['startLongitude'].mean()], zoom_start=12)

# Preparing features for TimestampedGeoJson
features = []

# Adding activity segments to features
for _, row in activity_segments_df.iterrows():
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
for _, row in place_visits_df.iterrows():
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

# Creating TimestampedGeoJson
timestamped_geo_json = TimestampedGeoJson({
    'type': 'FeatureCollection',
    'features': features,
}, period='PT1H', add_last_point=True)

# Adding the TimestampedGeoJson to the map
timestamped_geo_json.add_to(m)

# Saving the map to an HTML file
m.save('/mnt/data/timeline_map.html')

m

# ====================================================
# Heatmap version

