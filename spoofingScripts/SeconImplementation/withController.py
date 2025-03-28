#!/usr/bin/env python
'''fake GPS input using GPS_INPUT packet'''

import collections  
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

import time
import random
from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_settings
from MAVProxy.modules.lib import mp_util
import pygame
from dronekit import connect

if mp_util.has_wxpython:
    from MAVProxy.modules.lib.mp_menu import *

class FakeGPSModule(mp_module.MPModule):
    def __init__(self, mpstate):
        super(FakeGPSModule, self).__init__(mpstate, "fakegps", public=True)
        self.last_send = time.time()
        self.spoofing_active = False  # Flag to track spoofing state
        self.FakeGPS_settings = mp_settings.MPSettings([
            ("nsats", int, 16),
            ("lat", float, -35.363261),
            ("lon", float, 149.165230),
            ("alt", float, 584.0),
            ("yaw", float, 0.0),
            ("rate", float, 10),  # Default to 10Hz for better EKF fusion
            ("velocity_noise", float, 0.1),  # ±0.1 m/s velocity noise
            ("position_noise", float, 0.5),   # ±0.5m position noise
            ("spoof_step", float, 0.00001)    # Step size for spoofing
        ])
        self.add_command('fakegps', self.cmd_FakeGPS, "fakegps control",
                         ["<status>", "set (FAKEGPSSETTING)"])
        self.add_completion_function('(FAKEGPSSETTING)',
                                       self.FakeGPS_settings.completion)
        if mp_util.has_wxpython:
            map = self.module('map')
            if map is not None:
                menu = MPMenuSubMenu('FakeGPS',
                                     items=[MPMenuItem('SetPos', 'SetPos', '# fakegps setpos'),
                                            MPMenuItem('SetPos (with alt)', 'SetPosAlt', '# fakegps setpos ',
                                                       handler=MPMenuCallTextDialog(title='Altitude (m)', default=self.mpstate.settings.guidedalt)),
                                            MPMenuItem('StartSpoof', 'StartSpoof', '# fakegps startspoof'),
                                            MPMenuItem('StopSpoof', 'StopSpoof', '# fakegps stopspoof')])
                map.add_menu(menu)
        self.position = mp_util.mp_position()
        self.update_mpstate()

        # Initialize pygame and joystick
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise Exception("No joystick connected")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        print(f"Joystick initialized: {self.joystick.get_name()}")

    def get_location(self):
        '''access to location for other modules'''
        return (self.FakeGPS_settings.lat,
                self.FakeGPS_settings.lon,
                self.FakeGPS_settings.alt)

    def cmd_FakeGPS(self, args):
        '''fakegps command parser'''
        usage = "usage: fakegps <set|setpos|startspoof|stopspoof>"
        if len(args) == 0:
            print(usage)
            return
        if args[0] == "set":
            self.FakeGPS_settings.command(args[1:])
        elif args[0] == "setpos":
            self.cmd_setpos(args[1:])
        elif args[0] == "startspoof":
            self.spoofing_active = True
            print("GPS spoofing started")
        elif args[0] == "stopspoof":
            self.spoofing_active = False
            print("GPS spoofing stopped")
        else:
            print(usage)

    # update self with new coordinates
    def update_mpstate(self):
        '''update mpstate position'''
        self.position.latitude = self.FakeGPS_settings.lat
        self.position.longitude = self.FakeGPS_settings.lon
        self.position.altitude = self.FakeGPS_settings.alt
        self.position.timestamp = time.time()
        self.mpstate.position = self.position

    # Function to get controller input
    def get_controller_input(self):
        '''Read controller input using pygame joystick API with deadzone applied'''
        pygame.event.pump()
        axis_x = self.joystick.get_axis(0)
        axis_y = self.joystick.get_axis(1)
        
        # Deadzone 
        deadzone = 0.1
        if abs(axis_x) < deadzone:
            axis_x = 0
        if abs(axis_y) < deadzone:
            axis_y = 0

        return axis_x, -axis_y  # return x and y 

    def cmd_setpos(self, args):
        '''set pos from map'''
        latlon = self.mpstate.click_location
        if latlon is None:
            print("No map click position available")
            return
        (lat, lon) = latlon
        self.FakeGPS_settings.lat = lat
        self.FakeGPS_settings.lon = lon
        if len(args) > 0:
            self.FakeGPS_settings.alt = float(args[0])
        self.update_mpstate()

    def idle_task(self):
        '''called on idle'''
        if self.master is None or self.FakeGPS_settings.rate <= 0:
            return
        now = time.time()
        if now - self.last_send < 1.0 / self.FakeGPS_settings.rate:
            return
        self.last_send = now

        # Get current state
        gps_lat = self.FakeGPS_settings.lat 
        gps_lon = self.FakeGPS_settings.lon
        gps_alt = self.FakeGPS_settings.alt
        nsats = self.FakeGPS_settings.nsats
        yaw = self.FakeGPS_settings.yaw

        # Add realistic noise
        noise_lat = random.uniform(-self.FakeGPS_settings.position_noise * 1e-7, 
                                   self.FakeGPS_settings.position_noise * 1e-7)
        noise_lon = random.uniform(-self.FakeGPS_settings.position_noise * 1e-7,
                                   self.FakeGPS_settings.position_noise * 1e-7)
        noise_alt = random.uniform(-self.FakeGPS_settings.position_noise,
                                   self.FakeGPS_settings.position_noise)

        gps_vel = [0.0, 0.0, 0.0]  # these can be replaced with real values from copter

        # noise
        vel_noise = self.FakeGPS_settings.velocity_noise
        gps_vel_noisy = [
            gps_vel[0] + random.uniform(-vel_noise, vel_noise),
            gps_vel[1] + random.uniform(-vel_noise, vel_noise),
            gps_vel[2] + random.uniform(-vel_noise, vel_noise)
        ]

        # Prepare GPS time
        time_us = int(now * 1e6)
        gps_week, gps_week_ms = mp_util.get_gps_time(now)

        self.master.mav.gps_input_send(
            time_us, 0, 0, gps_week_ms, gps_week, 3,  # Always 3D fix
            int((gps_lat + noise_lat) * 1e7),
            int((gps_lon + noise_lon) * 1e7),
            gps_alt + noise_alt,
            0.3,  # hdop
            0.4,  # vdop
            gps_vel_noisy[0],
            gps_vel_noisy[1],
            gps_vel_noisy[2],
            0.2,  # speed_accuracy
            1.0,  # horiz_accuracy
            1.0,  # vert_accuracy
            self.FakeGPS_settings.nsats,
            int(self.FakeGPS_settings.yaw * 100)
        )

       # If spoofing is active, update the position continuously
        if self.spoofing_active:
            # Read controller input
            axis_x, axis_y = self.get_controller_input()

            # define offset scale 
            offset_scale = 0.0000005
            lat_offset = axis_y * offset_scale  # New lat with offset applied 
            lon_offset = axis_x * offset_scale   # New lon with offset applied

            # Update the lat and lon
            self.FakeGPS_settings.lat += lat_offset
            self.FakeGPS_settings.lon += lon_offset

            # Update GPS
            self.mpstate.click_location = (self.FakeGPS_settings.lat, self.FakeGPS_settings.lon)
            
            self.update_mpstate()

def init(mpstate):
    '''initialise module'''
    return FakeGPSModule(mpstate)
