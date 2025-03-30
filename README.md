# GPS Spoofing Project

This project demonstrates GPS spoofing using ArduCopter, MAVLink, and QGroundControl. It is designed to run on Ubuntu 22.04 hosted on a virtual machine (via UTM) on a MacBook Pro 2021 with an M1 chip.

## Prerequisites

### Hardware
- **PS4 Controller** (optional)

### Software
- A compiled and running version of **ArduCopter**
- **QGroundControl**
- **MAVLink**

### Libraries
- **PyGame**
- **DroneKit**
- **MAVProxy**

**Note:** All spoofing scripts in this project should be run using `python3`.

---

## Compiling and Running ArduCopter

Follow these steps to compile and run ArduCopter:

1. **Clone the Repository:**
    ```bash
    git clone --recurse-submodules https://github.com/Botii/gpsSpoofingProject
    ```
2. **Navigate to the Project Directory:**
    ```bash
    cd gpsSpoofingProject
    ```
3. **Install Prerequisites:**
    ```bash
    Tools/environment_install/install-prereqs-ubuntu.sh -y
    ```
4. **Update Environment Variables:**
    ```bash
    . ~/.profile
    ```
5. **Configure the Build for Your Board (e.g., MatekH743):**
    ```bash
    ./waf configure --board MatekH743
    ```
6. **Compile ArduCopter:**
    ```bash
    ./waf copter
    ```

> **Tip:** Run `./waf clean` before switching experiments, then repeat steps 5 and 6 to ensure a fresh build.

---

## Implementation 1: GPS Spoofing (No Controller)

1. **Launch the Simulation:**
    ```bash
    sim_vehicle.py -v ArduCopter -L KSFO --console --map --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551
    ```
2. **Wait** for all arming checks to complete and for the copter to initialize.
3. **Arm the Drone with Throttle 10:**
    ```bash
    arm throttle 10
    ```
4. **Set Flight Mode to Guided:**
    ```bash
    mode guided
    ```
5. **Initiate Takeoff (e.g., 10 meters):**
    ```bash
    takeoff 10
    ```
6. **Run the Spoof Script:**
    - Open a new terminal and execute the spoofing script spoofingScripts/FirstImplementation/noController.py. 

> **Note:** To run the first implementation with a controller, please run spoofingScripts/FirstImplementation/withController.py.
> > **Tip:** Run the following commands to remove the offsets from the previous flight, "param set SIM_GPS1_GLTCH_X 0" and "param set SIM_GPS1_GLTCH_Y 0"

### Auto Mission Experiment

After takeoff (step 5), you can switch to auto mode:

- **Change to Auto Mode:**
    ```bash
    mode auto
    ```
- **If the Drone Crashes (often in loiter mode), reset throttle using:**
    ```bash
    rc 3 1500
    ```
- **Mission Upload:** Missions can be uploaded to the copter via QGroundControl.

---

## Implementation 2: GPS Spoofing with PS4 Controller (or No Controller)

**Important:** The second implementation requires modifications to the fakegps module in MAVProxy. Replace the file located at `/home/ubuntu/.local/lib/python3.10/site-packages/MAVProxy/modules/mavproxy_fakegps.py` with the spoofing script found in `spoofingScripts/SecondImplementation`. 

1. **Launch the Simulation:**
    ```bash
    sim_vehicle.py -v ArduCopter -L KSFO --console --map --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551
    ```
2. **Switch Communication Protocol to MAVLink:**
    ```bash
    param set GPS1_TYPE 14
    ```
3. **Load the Fake GPS Module:**
    ```bash
    load module fakegps
    ```
4. **Reboot the System.**
5. **Controller Option:**
    - If you do not have a PS4 controller, use spoofingScripts/SeconImplementation/noController.py.
6. **Wait** until all configurations and initialization processes are complete.
7. **Arm the Drone with Throttle 10:**
    ```bash
    arm throttle 10
    ```
8. **Set Flight Mode to Guided:**
    ```bash
    mode guided
    ```
9. **Initiate Takeoff (e.g., 10 meters):**
    ```bash
    takeoff 10
    ```
10. **Start Spoofing:**
    - Right-click on the map and select **startSpoof**.

> **Note:** If you wish to use a PS4 controller, connect it before starting the second implementation and run spoofingScripts/SeconImplementation/withController.py

---

## Viewing Telemetry Data

For real-time telemetry data, please install and run **QGroundControl**. To install, please follow the steps provided at [Installing QGroundControl on Ubuntu ARM64 using Flatpak](https://github.com/sidharthmohannair/Installing-QGroundControl-on-Ubuntu-ARM64-using-Flatpak).
