
# radar.py
# purpose: identify the users nearest aircraft
# flow: 1. get usr location 2. list aircraft in surrounding area 3. list asc aircraft 4. display zeroth
# to-do:
#       - need to check if aircraft not found in 25km

import subprocess as sb
import os
from subprocess import run
run('cls' if os.name == 'nt' else 'clear')

# log run time
import time
start = time.time()

# get user location lat (x), long (y)
import geocoder as gc
ll = gc.ip('me')
usr_lat, usr_lng = ll.latlng[0], ll.latlng[1]
print(f"{ll.__repr__()}")

# create radar search box
import geopy
import geopy.distance
origin = geopy.Point(usr_lat, usr_lng)
scan_radius = 25 # km
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
min_lat = scan_coords[270][0]
max_lat = scan_coords[90][0]
min_lng = scan_coords[180][1]
max_lng = scan_coords[0][1]

# check log before running
dir_items = os.listdir()
gng = 0
if 'radar_log.txt' in dir_items:
    with open('radar_log.txt', 'r') as log:
        last_run_time = log.read()
    time_diff = time.time() - float(last_run_time)
    if time_diff > 10:
        gng = 1
    else:
        print("Please wait, API extract ran less than 10s ago")
        exit() # stop the program for user to run again
else:
    gng = 1
    search_time = str(time.time())
    with open('radar_log.txt', 'w') as log:
        log.write(f'{search_time}')

# get radar information
# get list of aircraft in scan area
from opensky_api import OpenSkyApi
api = OpenSkyApi()
if gng == 1:
    print("\nSearching...")
    states = api.get_states(bbox=(min_lat, max_lat, min_lng, max_lng))
    with open('radar_log.txt', 'w') as log:
        log.write(str(time.time()))
    origin_ = (usr_lat, usr_lng)
    smallest_distance = 0
    nearest_aircraft = {}
    for s in states.states:
        callsign = s.callsign.replace(" ", "")
        lat_lng = (s.latitude, s.longitude)
        distance = geopy.distance.geodesic(lat_lng, origin_)
        if smallest_distance == 0:
            smallest_distance = distance
        elif distance < smallest_distance:
            smallest_distance = distance
            nearest_aircraft['aircraft'] = [
                s.callsign.replace(" ","")
                ,lat_lng
                ,f"{smallest_distance.km:.2f}km"
                ,f"{s.velocity*3.6}km/h"
            ]

# display nearest aircraft, callsign, (lat,lng), distance (km), speed (km/h)
print(f"\n{nearest_aircraft}")
end = time.time()
print(f"\nCompleted in: {end-start:.2f} seconds")