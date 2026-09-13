# get user location lat (y), long (x)
import geocoder as gc
# ll = gc.ip('me')
# usr_lat, usr_lng = ll.latlng[0], ll.latlng[1]
usr_lat, usr_lng = 51.5837, -2.9977
# origin_name = str(ll).split('[')[2].split(']')[0]
origin_name = "Newport"
scan_radius = 100 # km

# create radar search box
import geopy
import geopy.distance
origin = geopy.Point(usr_lat, usr_lng)
bearings = [0, 90, 180, 270] # degrees
scan_coords = {} # dictionary of coords
for b in bearings:
    dest = geopy.distance.geodesic(kilometers=scan_radius
        ).destination(
            origin, bearing = b
        )
    l_lat = dest.latitude
    l_lng = dest.longitude
    scan_coords[b] = (l_lat, l_lng)

min_lat = scan_coords[180][0]   # south point's latitude
max_lat = scan_coords[0][0]     # north point's latitude
min_lng = scan_coords[270][1]   # west point's longitude
max_lng = scan_coords[90][1]    # east point's longitude

from geographiclib.geodesic import Geodesic
def bearing(origin: tuple, target: tuple) -> float:
    """bearing in degrees between orgin & target 
    aruments are touple pairs for lat and lng
    returns bearing clockwise from North"""
    bearing_data = Geodesic.WGS84.Inverse(origin[0], origin[1], target[0], target[1])
    bearing = bearing_data['azi1']
    if bearing <0: bearing +=360
    return bearing

# get aircraft from some defined boundary sorted by distance descending (nearest first)
from opensky_api import OpenSkyApi
api = OpenSkyApi()
import pandas as pd

def get_states(user_origin:tuple, boundaries:tuple):

    min_y, max_y, min_x, max_x = boundaries
    states = api.get_states(bbox=(min_y, max_y, min_x, max_x))

    aircraft_on_radar = []
    for s in states.states:
        if not s.callsign or s.latitude is None or s.longitude is None:
            continue # skip states that have no info
        # collect aircraft information
        aircraft = {}
        aircraft_lat, aircraft_lng = s.latitude, s.longitude
        aircraft_coords = (aircraft_lat, aircraft_lng)
        aircraft_bearing = bearing(user_origin, aircraft_coords)
        aircraft_distance = geopy.distance.geodesic(aircraft_coords, user_origin).km
        aircraft_speed = s.velocity*3.6
        aircraft['callsign'] = s.callsign.replace(" ", "")
        aircraft['latlng'] = aircraft_coords
        aircraft['bearing'] = aircraft_bearing
        aircraft['distance'] = aircraft_distance
        aircraft['speed'] = aircraft_speed
        aircraft_on_radar.append(aircraft)

    # convert to dataframe
    dt_ = pd.DataFrame(aircraft_on_radar)
    dt = dt_.sort_values('distance', ascending=True)

    return dt

import time

# plot radar
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
plt.style.use('dark_background')

llcrnrlat = scan_coords[180][0]
llcrnrlng = scan_coords[270][1]
urcrnrlat = scan_coords[0][0]
urcrnrlng = scan_coords[90][1]

print("generating map...")
fig, ax = plt.subplots()
radar = Basemap(llcrnrlon=llcrnrlng, llcrnrlat=llcrnrlat,
                 urcrnrlon=urcrnrlng, urcrnrlat=urcrnrlat,
                 resolution='i',
                 projection='cass',
                 lon_0=usr_lng,
                 lat_0=usr_lat,
                 ax=ax
                 )
radar.drawcoastlines(color='white')
radar.fillcontinents(color='black', lake_color='black')

# draw origin marker once — this never needs to be redrawn
usr_x, usr_y = radar(usr_lng, usr_lat)
radar.scatter(usr_x, usr_y, 30, marker='^', color='red')

plt.ion()          # turn on interactive mode
plt.show()

aircraft_artists = []  # keep track of everything we draw per-update, so we can remove it

def update_aircraft():
    global aircraft_artists

    # remove previous scatter points and labels
    for artist in aircraft_artists:
        artist.remove()
    aircraft_artists = []

    print('Scanning local space...')
    df = get_states(
        user_origin=(usr_lat, usr_lng),
        boundaries=(min_lat, max_lat, min_lng, max_lng)
    )
    print(df)
    print("Ctrl + C to stop")

    for i, row in df.iterrows():
        callsign = row['callsign']
        lat, lng = row['latlng']
        ac_x, ac_y = radar(lng, lat)
        point = radar.scatter(ac_x, ac_y, 30, marker='s', facecolor='none', edgecolor='blue')
        label = ax.annotate(callsign, (ac_x, ac_y), color='yellow', fontsize=6)
        aircraft_artists.append(point)
        aircraft_artists.append(label)

    now = time.time()
    formatted_datetime = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(now))
    ax.set_title(f"Origin: {origin_name}, {formatted_datetime}", fontsize=10)

    fig.canvas.draw()
    fig.canvas.flush_events()

# main update loop
while True:
    update_aircraft()
    plt.pause(11)   # waits 11s AND keeps the plot window responsive