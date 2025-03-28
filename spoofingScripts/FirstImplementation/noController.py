import collections  
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

import time
from dronekit import connect

# Connect to SITL
vehicle = connect('127.0.0.1:14551', wait_ready=True)

# Scaling factors for gradual GPS drift
SCALING_FACTOR_LAT = 0.000000 # Latitude shift per step
SCALING_FACTOR_LON = 0.000008   # Longitude shift per step

lat_offset = 0.0
lon_offset = 0.0
alt_offset = 0.0

step = 0

while True:
    # Gradually apply the offsets
    lat_offset += SCALING_FACTOR_LAT
    lon_offset += SCALING_FACTOR_LON

    # Apply the offsets
    vehicle.parameters['SIM_GPS1_GLTCH_X'] = lat_offset
    vehicle.parameters['SIM_GPS1_GLTCH_Y'] = lon_offset
    # vehicle.parameters['SIM_GPS1_GLTCH_Z'] = alt_offset  # We dont change the alt

    # print the applied offsets to the lat and lng
    print(f"Step {step}: Applied GPS drift -> {lat_offset / 1e7}° lat, {lon_offset / 1e7}° lng")

    # increment the step
    step += 1
    
    time.sleep(0.2)  # sleep before applying the next offset
